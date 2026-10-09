#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <WiFi.h>
#include <time.h>

#include "Config.h"
#include "CloudConfig.h"
#include "CloudHistory.h"
#include "History.h"
#include "LcdDisplay.h"
#include "Storage.h"
#include "irrigation_logic.h"
#include "web_server.h"

// Sem hardware ainda: VALVE_PIN pisca o LED onboard no lugar do relé da
// válvula solenoide. Sem sensor de umidade nesta fase (irrigação é só por
// horário programado) e sem RTC externo (DS3231): o relógio é sincronizado
// pela internet via NTP quando o Wi-Fi do local está disponível.
namespace {

constexpr uint8_t VALVE_PIN = 2;

// QR code do equipamento deve ser gerado/impresso a partir destas credenciais.
constexpr const char* AP_SSID = "Irrigacao-Comunitaria";
constexpr const char* AP_PASSWORD = "irrigacao";
constexpr const char* WIFI_SSID = WifiConfig::SSID;
constexpr const char* WIFI_PASSWORD = WifiConfig::PASSWORD;
constexpr time_t VALID_TIME_EPOCH = 1704067200; // 2024-01-01 UTC
constexpr unsigned long WIFI_CONNECT_GRACE_MS = 20000; // espera no boot antes de a tela avisar "sem Wi-Fi"

AsyncWebServer server(80);
IrrigationConfig config;

bool valveOpen = false;
unsigned long valveOpenedAtMs = 0;
uint16_t valveDurationSec = 0;

// Rotinas de segurança: ver README (Rotinas de segurança) para o racional.
bool storageFault = false; // true se uma gravação da configuração em SPIFFS falhar

unsigned long lastIrrigationEndMs = 0;
bool hasIrrigatedBefore = false; // false até a primeira válvula fechar nesta sessão (cooldown não se aplica antes disso)

uint32_t dailyBudgetUsedSec = 0;
int32_t dailyBudgetDayIndex = -1;

void getCurrentTime(uint8_t& hour, uint8_t& minute) {
    time_t now = time(nullptr);
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    hour = static_cast<uint8_t>(timeinfo.tm_hour);
    minute = static_cast<uint8_t>(timeinfo.tm_min);
}

bool isSystemTimeValid() {
    return time(nullptr) >= VALID_TIME_EPOCH;
}

// Ponto único de acionamento: aplica o teto absoluto de duração (rotina de
// segurança 1.1) não importa de onde veio o pedido (agendado, manual ou um
// valor inválido lido da configuração persistida).
void openValve(uint16_t durationSec) {
    if (durationSec > MAX_IRRIGATION_DURATION_SEC) {
        durationSec = MAX_IRRIGATION_DURATION_SEC;
    }
    valveOpen = true;
    valveOpenedAtMs = millis();
    valveDurationSec = durationSec;
    digitalWrite(VALVE_PIN, HIGH);
}

void closeValve() {
    valveOpen = false;
    digitalWrite(VALVE_PIN, LOW);
    lastIrrigationEndMs = millis();
    hasIrrigatedBefore = true;
}

uint16_t remainingValveSeconds() {
    if (!valveOpen) return 0;
    unsigned long durationMs = static_cast<unsigned long>(valveDurationSec) * 1000UL;
    unsigned long elapsedMs = millis() - valveOpenedAtMs;
    if (elapsedMs >= durationMs) return 0;
    return static_cast<uint16_t>((durationMs - elapsedMs + 999UL) / 1000UL);
}

void updateValve() {
    if (valveOpen && millis() - valveOpenedAtMs >= static_cast<unsigned long>(valveDurationSec) * 1000UL) {
        closeValve();
    }
}

void logHistoryEntry(bool irrigated, uint16_t durationSec, TriggerReason reason) {
    HistoryEntry entry;
    entry.timestamp = static_cast<uint32_t>(time(nullptr));
    entry.moisturePercent = 0; // sem sensor nesta fase
    entry.irrigated = irrigated;
    entry.durationSec = durationSec;
    entry.reason = reason;
    if (!CloudHistory::enqueue(entry)) {
        Serial.println("[sheets] fila de envio cheia; registro nao enfileirado");
    }
}

// Orçamento diário (rotina de segurança 1.3): "dia" é derivado do relógio do
// sistema sincronizado por NTP. Antes da sincronização, os agendamentos ficam
// suspensos; o contador diário só usa datas válidas depois disso.
void resetDailyBudgetIfNewDay() {
    int32_t dayIndex = static_cast<int32_t>(time(nullptr) / 86400L);
    if (dayIndex != dailyBudgetDayIndex) {
        dailyBudgetDayIndex = dayIndex;
        dailyBudgetUsedSec = 0;
    }
}

struct AttemptResult {
    bool allowed;
    TriggerReason reason; // motivo real se allowed, motivo do bloqueio se !allowed
};

// Ponto único de disparo de irrigação (agendada ou manual): aplica cooldown
// (1.2) e orçamento diário (1.3) antes de abrir a válvula, e enfileira o
// resultado para o histórico cloud em qualquer caso — inclusive bloqueios.
AttemptResult attemptIrrigation(uint16_t requestedDurationSec, TriggerReason reason) {
    // valveOpen cobre o caso de um novo pedido chegar enquanto a válvula
    // anterior ainda está aberta (cooldown por tempo só é checado depois que
    // ela fecha — sem isso, dois cliques rápidos no botão manual abririam a
    // válvula "de novo" por cima da primeira abertura).
    bool withinCooldown = hasIrrigatedBefore && millis() - lastIrrigationEndMs <
                                                     static_cast<unsigned long>(IRRIGATION_COOLDOWN_SEC) * 1000UL;
    if (valveOpen || withinCooldown) {
        logHistoryEntry(false, 0, TriggerReason::BLOCKED_COOLDOWN);
        return {false, TriggerReason::BLOCKED_COOLDOWN};
    }

    resetDailyBudgetIfNewDay();
    uint16_t cappedDuration =
        requestedDurationSec > MAX_IRRIGATION_DURATION_SEC ? MAX_IRRIGATION_DURATION_SEC : requestedDurationSec;
    if (dailyBudgetUsedSec + cappedDuration > DAILY_WATER_BUDGET_SEC) {
        logHistoryEntry(false, 0, TriggerReason::BLOCKED_DAILY_BUDGET);
        return {false, TriggerReason::BLOCKED_DAILY_BUDGET};
    }

    openValve(cappedDuration);
    dailyBudgetUsedSec += cappedDuration;
    logHistoryEntry(true, cappedDuration, reason);
    return {true, reason};
}

// Acionamento manual via /admin/irrigate — ignora horário, mas continua
// sujeito ao cooldown e ao orçamento diário.
ManualIrrigateResult manualIrrigate(uint16_t durationSec) {
    AttemptResult result = attemptIrrigation(durationSec, TriggerReason::MANUAL);
    if (!result.allowed) {
        Serial.printf("[irrigacao] manual recusado (%s)\n",
                      result.reason == TriggerReason::BLOCKED_COOLDOWN ? "cooldown" : "orcamento diario");
        return result.reason == TriggerReason::BLOCKED_COOLDOWN ? ManualIrrigateResult::BLOCKED_COOLDOWN
                                                                  : ManualIrrigateResult::BLOCKED_DAILY_BUDGET;
    }
    Serial.printf("[irrigacao] manual: abrindo valvula por %us\n", valveDurationSec);
    return ManualIrrigateResult::OK;
}

// Parada de emergência via /admin/stop — fecha a válvula imediatamente,
// independente do que estiver em andamento.
void stopIrrigation() {
    if (valveOpen) {
        closeValve();
        logHistoryEntry(false, 0, TriggerReason::EMERGENCY_STOP);
        Serial.println("[irrigacao] parada de emergencia acionada");
    }
}

// Avalia a decisão de irrigação uma vez por minuto (não uma vez por
// segundo): decideIrrigation() casa o slot pelo minuto inteiro, então sem
// essa deduplicação por chave de minuto o mesmo evento seria reavaliado e
// tentaria reabrir a válvula repetidamente enquanto o relógio permanece
// naquele minuto.
void evaluateIrrigation() {
    if (!isSystemTimeValid()) {
        return;
    }

    uint8_t hour, minute;
    getCurrentTime(hour, minute);

    static int16_t lastMatchedMinuteKey = -1;
    int16_t currentMinuteKey = static_cast<int16_t>(hour) * 60 + minute;

    IrrigationDecision decision = decideIrrigation(config, hour, minute);

    if (!decision.scheduleMatched || currentMinuteKey == lastMatchedMinuteKey) {
        return;
    }
    lastMatchedMinuteKey = currentMinuteKey;

    AttemptResult result = attemptIrrigation(decision.durationSec, TriggerReason::SCHEDULE);
    if (result.allowed) {
        Serial.printf("[irrigacao] abrindo valvula por %us (horario programado)\n", valveDurationSec);
    } else {
        Serial.printf("[irrigacao] horario batido, bloqueado (%s)\n",
                      result.reason == TriggerReason::BLOCKED_COOLDOWN ? "cooldown" : "orcamento diario");
    }
}

// Mantém a tela com o endereço atual do site: o IP vem do roteador por DHCP
// e pode mudar a cada boot ou reconexão, então é reescrito sempre que muda.
// Sem Wi-Fi, mostra o IP da rede do próprio ESP32, que é fixo.
void updateAddressDisplay() {
    enum class Shown : uint8_t { CONNECTING, ADDRESS, OFFLINE };
    static Shown shown = Shown::CONNECTING;
    static IPAddress shownIp;

    if (WiFi.status() == WL_CONNECTED) {
        IPAddress ip = WiFi.localIP();
        if (shown != Shown::ADDRESS || ip != shownIp) {
            shown = Shown::ADDRESS;
            shownIp = ip;
            LcdDisplay::showAddress(ip);
            Serial.printf("[wifi] conectado a %s; painel http://%s/\n", WIFI_SSID, ip.toString().c_str());
        }
        return;
    }

    bool stillBooting = shown == Shown::CONNECTING && millis() < WIFI_CONNECT_GRACE_MS;
    if (shown != Shown::OFFLINE && !stillBooting) {
        shown = Shown::OFFLINE;
        LcdDisplay::showOffline(WiFi.softAPIP());
        Serial.println("[wifi] sem conexao com o Wi-Fi do local");
    }
}

} // namespace

void setup() {
    Serial.begin(115200);

    pinMode(VALVE_PIN, OUTPUT);
    digitalWrite(VALVE_PIN, LOW);

    loadConfig(config);

    LcdDisplay::begin();
    LcdDisplay::showConnecting();

    WiFi.mode(WIFI_AP_STA);
    WiFi.softAP(AP_SSID, AP_PASSWORD);
    WiFi.setAutoReconnect(true);
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    configTime(-3 * 60 * 60, 0, "pool.ntp.org", "time.google.com");
    CloudHistory::begin();

    WebServer::begin(server, config, valveOpen, storageFault, remainingValveSeconds, manualIrrigate, stopIrrigation);
    server.begin();

    Serial.printf("[boot] AP \"%s\" ativo, IP %s\n", AP_SSID, WiFi.softAPIP().toString().c_str());
}

void loop() {
    updateValve();

    updateAddressDisplay();

    static bool timeReported = false;
    if (!timeReported && isSystemTimeValid()) {
        timeReported = true;
        Serial.println("[ntp] horario sincronizado");
    }

    static unsigned long lastEvalMs = 0;
    unsigned long nowMs = millis();
    if (nowMs - lastEvalMs >= 1000) {
        lastEvalMs = nowMs;
        evaluateIrrigation();
    }
}
