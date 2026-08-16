#include <Arduino.h>
#include <ESPAsyncWebServer.h>
#include <WiFi.h>
#include <time.h>

#include "Config.h"
#include "History.h"
#include "Storage.h"
#include "irrigation_logic.h"
#include "web_server.h"

// Sem hardware ainda: VALVE_PIN pisca o LED onboard no lugar do relé da
// válvula solenoide, e MOISTURE_SENSOR_PIN lê um potenciômetro no lugar do
// sensor capacitivo. Sem RTC externo (DS3231) também: o relógio começa em
// 1970-01-01 00:00:00 a cada boot. Trocar por hardware real quando chegar.
namespace {

constexpr uint8_t VALVE_PIN = 2;
constexpr uint8_t MOISTURE_SENSOR_PIN = 34;

// QR code do equipamento deve ser gerado/impresso a partir destas credenciais.
constexpr const char* AP_SSID = "Irrigacao-Comunitaria";
constexpr const char* AP_PASSWORD = "irrigacao";

AsyncWebServer server(80);
IrrigationConfig config;

bool valveOpen = false;
unsigned long valveOpenedAtMs = 0;
uint16_t valveDurationSec = 0;
uint8_t currentMoisturePercent = 0;

uint8_t readMoisturePercent() {
    int raw = analogRead(MOISTURE_SENSOR_PIN);
    long dry = config.sensorDryRaw;
    long wet = config.sensorWetRaw;
    if (dry == wet) {
        return 0;
    }
    long percent = 100L * (dry - raw) / (dry - wet);
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    return static_cast<uint8_t>(percent);
}

void getCurrentTime(uint8_t& hour, uint8_t& minute) {
    time_t now = time(nullptr);
    struct tm timeinfo;
    localtime_r(&now, &timeinfo);
    hour = static_cast<uint8_t>(timeinfo.tm_hour);
    minute = static_cast<uint8_t>(timeinfo.tm_min);
}

void openValve(uint16_t durationSec) {
    valveOpen = true;
    valveOpenedAtMs = millis();
    valveDurationSec = durationSec;
    digitalWrite(VALVE_PIN, HIGH);
}

void closeValve() {
    valveOpen = false;
    digitalWrite(VALVE_PIN, LOW);
}

void updateValve() {
    if (valveOpen && millis() - valveOpenedAtMs >= static_cast<unsigned long>(valveDurationSec) * 1000UL) {
        closeValve();
    }
}

// Acionamento manual via /admin/irrigate — ignora horário e limiar.
void manualIrrigate(uint16_t durationSec) {
    openValve(durationSec);
    Serial.printf("[irrigacao] manual: abrindo valvula por %us\n", durationSec);

    HistoryEntry entry;
    entry.timestamp = static_cast<uint32_t>(time(nullptr));
    entry.moisturePercent = currentMoisturePercent;
    entry.irrigated = true;
    entry.durationSec = durationSec;
    entry.reason = TriggerReason::MANUAL;
    appendHistoryEntry(entry);
}

// Avalia a decisão de irrigação uma vez por minuto (não uma vez por
// segundo): decideIrrigation() casa o slot pelo minuto inteiro, então sem
// essa deduplicação por chave de minuto o mesmo evento seria reavaliado e
// regravado no histórico repetidamente enquanto o relógio permanece naquele
// minuto.
void evaluateIrrigation(uint8_t moisture) {
    uint8_t hour, minute;
    getCurrentTime(hour, minute);

    static int16_t lastMatchedMinuteKey = -1;
    int16_t currentMinuteKey = static_cast<int16_t>(hour) * 60 + minute;

    IrrigationDecision decision = decideIrrigation(config, moisture, hour, minute);

    if (!decision.scheduleMatched || currentMinuteKey == lastMatchedMinuteKey) {
        return;
    }
    lastMatchedMinuteKey = currentMinuteKey;

    if (decision.shouldIrrigate) {
        openValve(decision.durationSec);
        Serial.printf("[irrigacao] abrindo valvula por %us (umidade %u%%)\n", decision.durationSec, moisture);
    } else {
        Serial.printf("[irrigacao] horario batido, pulado (umidade %u%% acima do limiar)\n", moisture);
    }

    HistoryEntry entry;
    entry.timestamp = static_cast<uint32_t>(time(nullptr));
    entry.moisturePercent = moisture;
    entry.irrigated = decision.shouldIrrigate;
    entry.durationSec = decision.shouldIrrigate ? decision.durationSec : 0;
    entry.reason = decision.reason;
    appendHistoryEntry(entry);
}

} // namespace

void setup() {
    Serial.begin(115200);

    pinMode(VALVE_PIN, OUTPUT);
    digitalWrite(VALVE_PIN, LOW);

    struct timeval epoch = {0, 0};
    settimeofday(&epoch, nullptr);

    loadConfig(config);

    WiFi.softAP(AP_SSID, AP_PASSWORD);
    WebServer::begin(server, config, valveOpen, currentMoisturePercent, manualIrrigate);
    server.begin();

    Serial.printf("[boot] AP \"%s\" ativo, IP %s\n", AP_SSID, WiFi.softAPIP().toString().c_str());
}

void loop() {
    updateValve();

    static unsigned long lastEvalMs = 0;
    unsigned long nowMs = millis();
    if (nowMs - lastEvalMs >= 1000) {
        lastEvalMs = nowMs;
        currentMoisturePercent = readMoisturePercent();
        evaluateIrrigation(currentMoisturePercent);
    }
}
