#include "web_server.h"

#include <Arduino.h>
#include <cstdio>
#include <cstring>
#include <sys/time.h>
#include <time.h>

#include "History.h"
#include "Routes.h"
#include "Storage.h"

namespace {

const char* reasonToString(TriggerReason reason) {
    switch (reason) {
        case TriggerReason::SCHEDULE:
            return "SCHEDULE";
        case TriggerReason::MANUAL:
            return "MANUAL";
        case TriggerReason::SKIPPED:
            return "SKIPPED";
        case TriggerReason::BLOCKED_COOLDOWN:
            return "BLOCKED_COOLDOWN";
        case TriggerReason::BLOCKED_DAILY_BUDGET:
            return "BLOCKED_DAILY_BUDGET";
        case TriggerReason::EMERGENCY_STOP:
            return "EMERGENCY_STOP";
    }
    return "UNKNOWN";
}

// CSS compartilhado entre /status e /admin. Sem dependências externas
// (sem CDN) — precisa funcionar 100% offline na rede local do ESP32.
constexpr const char* PAGE_STYLE =
    "<style>"
    ":root{--green:#2f7d4f;--green-dark:#245f3d;--bg:#f4f7f4;--card:#fff;--ink:#1f2a24;"
    "--muted:#6b7a70;--danger:#b3261e;--radius:14px}"
    "*{box-sizing:border-box}"
    "body{margin:0;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Helvetica,Arial,sans-serif;"
    "background:var(--bg);color:var(--ink);padding:0 0 32px}"
    "header{background:linear-gradient(135deg,var(--green),var(--green-dark));color:#fff;"
    "padding:20px 16px;text-align:center}"
    "header h1{margin:0;font-size:1.25rem;font-weight:600}"
    "header p{margin:4px 0 0;opacity:.85;font-size:.85rem}"
    "main{max-width:480px;margin:0 auto;padding:16px}"
    ".card{background:var(--card);border-radius:var(--radius);padding:18px;margin-bottom:16px;"
    "box-shadow:0 1px 3px rgba(0,0,0,.08)}"
    ".card h2{margin:0 0 12px;font-size:1rem;color:var(--green-dark)}"
    ".badge{display:inline-flex;align-items:center;gap:8px;padding:10px 18px;border-radius:999px;"
    "font-weight:600;font-size:1rem}"
    ".badge.on{background:#e3f3e9;color:var(--green-dark)}"
    ".badge.off{background:#eef1ee;color:var(--muted)}"
    ".badge .dot{width:9px;height:9px;border-radius:50%;background:currentColor}"
    ".stat{display:flex;justify-content:space-between;gap:12px;padding:8px 0;border-bottom:1px solid #eef1ee;"
    "font-size:.95rem}"
    ".stat:last-child{border-bottom:none}"
    ".stat span:first-child{color:var(--muted)}"
    ".stat span:last-child{font-weight:600;text-align:right}"
    "label{display:block;font-size:.85rem;color:var(--muted);margin:12px 0 4px}"
    "input[type=number],input[type=datetime-local]{"
    "width:100%;padding:10px 12px;border:1px solid #d6ddd8;border-radius:10px;font-size:1rem;background:#fbfcfb}"
    ".slot{border:1px solid #e3e8e4;border-radius:12px;padding:10px 12px;margin-bottom:8px;"
    "display:flex;align-items:center;gap:10px;flex-wrap:wrap}"
    ".slot .chk{display:flex;align-items:center;gap:6px;margin:0;font-size:.9rem}"
    ".row{display:flex;gap:8px}"
    ".row>div{flex:1}"
    "button{width:100%;padding:13px;border:none;border-radius:10px;background:var(--green);color:#fff;"
    "font-size:1rem;font-weight:600;margin-top:16px;cursor:pointer}"
    "button.danger{background:#fdece9;color:var(--danger)}"
    "a.link{display:inline-block;margin-top:4px;color:var(--green-dark);font-weight:600;text-decoration:none}"
    ".muted{color:var(--muted);font-size:.85rem;margin:4px 0 0}"
    "</style>";

String htmlHead(const char* title) {
    return String("<meta charset=\"utf-8\"><meta name=\"viewport\" "
                   "content=\"width=device-width, initial-scale=1\"><title>") +
           title + "</title>" + PAGE_STYLE;
}

String buildStatusJson(const IrrigationConfig& config, bool valveOpen, bool storageFault) {
    String json = "{\"valveOpen\":" + String(valveOpen ? "true" : "false") +
                  ",\"currentEpoch\":" + String(static_cast<uint32_t>(time(nullptr))) +
                  ",\"storageFault\":" + (storageFault ? "true" : "false") +
                  ",\"config\":{\"schedules\":[";
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        const ScheduleSlot& slot = config.schedules[i];
        if (i > 0) json += ",";
        json += "{\"hour\":" + String(slot.hour) +
                ",\"minute\":" + String(slot.minute) +
                ",\"enabled\":" + (slot.enabled ? "true" : "false") + "}";
    }
    json += "],\"scheduleCount\":" + String(config.scheduleCount) +
            ",\"irrigationDurationSec\":" + String(config.irrigationDurationSec) +
            "}";

    size_t count = historyCount();
    HistoryEntry lastEntry;
    if (count > 0 && readHistoryEntry(count - 1, lastEntry)) {
        json += ",\"lastEntry\":{\"timestamp\":" + String(lastEntry.timestamp) +
                ",\"irrigated\":" + (lastEntry.irrigated ? "true" : "false") +
                ",\"durationSec\":" + String(lastEntry.durationSec) +
                ",\"reason\":\"" + reasonToString(lastEntry.reason) + "\"}";
    } else {
        json += ",\"lastEntry\":null";
    }
    json += "}";
    return json;
}

String buildStatusHtml() {
    String html = "<!DOCTYPE html><html><head>" + htmlHead("Irrigacao - Status") +
        "</head><body>"
        "<header><h1>Irrigacao Comunitaria</h1><p>Horta local</p></header>"
        "<main>"
        "<div id=\"faultCard\" class=\"card\" style=\"display:none;border:2px solid var(--danger);\">"
        "<h2 style=\"color:var(--danger)\">Falha detectada</h2>"
        "<p>O sistema encontrou um problema de armazenamento e pode nao estar funcionando "
        "corretamente. Entre em contato com o professor responsavel pelo projeto.</p>"
        "</div>"
        "<div class=\"card\" style=\"text-align:center\">"
        "<span id=\"valveBadge\" class=\"badge off\"><span class=\"dot\"></span>"
        "<span id=\"valveText\">Carregando...</span></span>"
        "</div>"
        "<div class=\"card\"><h2>Horario do sistema</h2>"
        "<div class=\"stat\"><span>Agora</span><span id=\"now\">--</span></div>"
        "</div>"
        "<div class=\"card\"><h2>Ultimo evento registrado</h2>"
        "<div class=\"stat\"><span>Quando</span><span id=\"lastWhen\">--</span></div>"
        "<div class=\"stat\"><span>Resultado</span><span id=\"lastResult\">--</span></div>"
        "</div>"
        "<div class=\"card\"><h2>Horarios programados</h2>"
        "<div id=\"schedules\">--</div>"
        "</div>"
        "<a class=\"link\" href=\"" + String(Routes::ADMIN) + "\">Ir para administracao &rarr;</a>"
        "</main>"
        "<script>"
        "function pad(n){return String(n).padStart(2,'0');}"
        "function fmtTime(s){var h=Math.floor(s/3600)%24,m=Math.floor(s/60)%60;return pad(h)+':'+pad(m);}"
        // new Date(e*1000).toLocaleString() aplica o fuso horario REAL do
        // navegador, mas o epoch aqui e' um relogio "ingenuo" (definido via
        // /admin/time sem conversao de fuso). Por isso usamos os getters
        // *UTC* do Date, que leem os campos de volta sem aplicar deslocamento.
        "function fmtEpoch(e){if(!e)return '--';var d=new Date(e*1000);"
        "return pad(d.getUTCDate())+'/'+pad(d.getUTCMonth()+1)+'/'+d.getUTCFullYear()+' '+pad(d.getUTCHours())+':'+pad(d.getUTCMinutes());}"
        "function reasonLabel(r){return {SCHEDULE:'Irrigou (horario)',MANUAL:'Manual',"
        "BLOCKED_COOLDOWN:'Bloqueado (cooldown)',BLOCKED_DAILY_BUDGET:'Bloqueado (orcamento diario)',"
        "EMERGENCY_STOP:'Parada de emergencia'}[r]||r;}"
        "function refresh(){"
        "fetch('" + String(Routes::STATUS_JSON) + "').then(function(r){return r.json();}).then(function(d){"
        "document.getElementById('faultCard').style.display=d.storageFault?'block':'none';"
        "var badge=document.getElementById('valveBadge');"
        "badge.className='badge '+(d.valveOpen?'on':'off');"
        "document.getElementById('valveText').textContent=d.valveOpen?'Irrigando agora':'Aguardando';"
        "document.getElementById('now').textContent=fmtTime(d.currentEpoch);"
        "if(d.lastEntry){"
        "document.getElementById('lastWhen').textContent=fmtEpoch(d.lastEntry.timestamp);"
        "document.getElementById('lastResult').textContent=reasonLabel(d.lastEntry.reason);"
        "}else{"
        "document.getElementById('lastWhen').textContent='Nenhum evento ainda';"
        "document.getElementById('lastResult').textContent='--';"
        "}"
        "var s='';"
        "d.config.schedules.forEach(function(slot,i){"
        "if(!slot.enabled)return;"
        "s+='<div class=\"stat\"><span>Slot '+i+'</span><span>'+pad(slot.hour)+':'+pad(slot.minute)+'</span></div>';"
        "});"
        "document.getElementById('schedules').innerHTML=s||'<p class=\"muted\">Nenhum horario ativo</p>';"
        "});"
        "}"
        "refresh();setInterval(refresh,5000);"
        "</script>"
        "</body></html>";
    return html;
}

String buildAdminFormHtml(const IrrigationConfig& config, const String& notice) {
    bool anyScheduleActive = false;
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        if (config.schedules[i].enabled) anyScheduleActive = true;
    }

    String html = "<!DOCTYPE html><html><head>" + htmlHead("Irrigacao - Admin") +
        "</head><body>"
        "<header><h1>Administracao</h1><p>Irrigacao Comunitaria</p></header>"
        "<main>";

    if (notice.length() > 0) {
        html += "<div class=\"card\" style=\"border:2px solid var(--danger);\"><p style=\"margin:0\">" +
                notice + "</p></div>";
    }
    if (!anyScheduleActive) {
        html += "<div class=\"card\"><p class=\"muted\" style=\"margin:0\">Nenhum horario de irrigacao "
                "ativo no momento — o sistema nao vai irrigar automaticamente ate um horario ser "
                "habilitado abaixo.</p></div>";
    }

    html +=
        "<div class=\"card\"><h2>Horario do sistema</h2>"
        "<p class=\"muted\">Sem RTC ainda: defina a hora atual manualmente. Ela reinicia toda vez "
        "que o ESP32 desliga ou reseta.</p>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_TIME) + "\">"
        "<label>Data e hora atuais</label>"
        "<input type=\"datetime-local\" name=\"datetime\" required>"
        "<button type=\"submit\">Definir horario</button>"
        "</form></div>"

        "<div class=\"card\"><h2>Irrigacao manual</h2>"
        "<p class=\"muted\">Abre a valvula agora, pelo tempo indicado (maximo " +
        String(MAX_IRRIGATION_DURATION_SEC) +
        "s), sem esperar horario. Sujeita ao cooldown e ao orcamento diario.</p>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_IRRIGATE) + "\">"
        "<label>Duracao (segundos)</label>"
        "<input type=\"number\" min=\"1\" max=\"" + String(MAX_IRRIGATION_DURATION_SEC) +
        "\" name=\"durationSec\" value=\"" + String(config.irrigationDurationSec) + "\">"
        "<button type=\"submit\">Irrigar agora</button>"
        "</form>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_STOP) +
        "\" onsubmit=\"return confirm('Fechar a valvula agora?');\">"
        "<button type=\"submit\" class=\"danger\">Parar irrigacao agora</button></form>"
        "</div>"

        "<div class=\"card\"><form method=\"POST\" action=\"" + String(Routes::ADMIN_CONFIG) + "\">"
        "<h2>Horarios de irrigacao</h2>";

    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        const ScheduleSlot& slot = config.schedules[i];
        html += "<div class=\"slot\"><div class=\"row\">"
                "<div><label>Hora</label><input type=\"number\" min=\"0\" max=\"23\" name=\"hour" + String(i) +
                "\" value=\"" + String(slot.hour) + "\"></div>"
                "<div><label>Minuto</label><input type=\"number\" min=\"0\" max=\"59\" name=\"minute" + String(i) +
                "\" value=\"" + String(slot.minute) + "\"></div>"
                "</div>"
                "<label class=\"chk\"><input type=\"checkbox\" name=\"enabled" + String(i) + "\"" +
                (slot.enabled ? " checked" : "") + "> Slot " + String(i) + " ativo</label></div>";
    }

    html += "<h2>Duracao da irrigacao</h2>"
            "<label>Duracao (segundos, maximo " + String(MAX_IRRIGATION_DURATION_SEC) + ")</label>"
            "<input type=\"number\" min=\"0\" max=\"" + String(MAX_IRRIGATION_DURATION_SEC) +
            "\" name=\"irrigationDurationSec\" value=\"" + String(config.irrigationDurationSec) + "\">"
            "<button type=\"submit\">Salvar</button>"
            "</form></div>"

            "<div class=\"card\"><h2>Historico</h2>"
            "<a class=\"link\" href=\"" + String(Routes::ADMIN_HISTORY) + "\">Baixar CSV</a>"
            "<form method=\"POST\" action=\"" + String(Routes::ADMIN_HISTORY_RESET) +
            "\" onsubmit=\"return confirm('Apagar todo o historico?');\">"
            "<button type=\"submit\" class=\"danger\">Zerar historico</button></form></div>"

            "<a class=\"link\" href=\"" + String(Routes::STATUS) + "\">&larr; Ver status</a>"
            "</main></body></html>";
    return html;
}

// Mesma convenção do relógio do sistema (sem TZ, sem RTC): trata o epoch
// como campos de calendário "ingênuos" via gmtime_r, sem aplicar fuso —
// consistente com o que foi digitado em /admin/time.
String formatDateTime(uint32_t timestamp) {
    time_t t = static_cast<time_t>(timestamp);
    struct tm timeinfo;
    gmtime_r(&t, &timeinfo);
    char buf[20];
    snprintf(buf, sizeof(buf), "%02d/%02d/%04d %02d:%02d", timeinfo.tm_mday, timeinfo.tm_mon + 1,
             timeinfo.tm_year + 1900, timeinfo.tm_hour, timeinfo.tm_min);
    return String(buf);
}

String buildHistoryCsv() {
    String csv = "data_hora,irrigated,durationSec,reason\n";
    size_t count = historyCount();
    HistoryEntry entry;
    for (size_t i = 0; i < count; i++) {
        if (!readHistoryEntry(i, entry)) continue;
        csv += formatDateTime(entry.timestamp) + "," +
               (entry.irrigated ? "1" : "0") + "," +
               String(entry.durationSec) + "," +
               reasonToString(entry.reason) + "\n";
    }
    return csv;
}

uint8_t clampU8(long value, uint8_t lo, uint8_t hi) {
    if (value < lo) return lo;
    if (value > hi) return hi;
    return static_cast<uint8_t>(value);
}

uint16_t clampU16(long value, uint16_t lo, uint16_t hi) {
    if (value < lo) return lo;
    if (value > hi) return hi;
    return static_cast<uint16_t>(value);
}

void applyConfigFromRequest(AsyncWebServerRequest* request, IrrigationConfig& config) {
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        String hourKey = "hour" + String(i);
        String minuteKey = "minute" + String(i);
        String enabledKey = "enabled" + String(i);

        if (request->hasParam(hourKey, true)) {
            config.schedules[i].hour = clampU8(request->getParam(hourKey, true)->value().toInt(), 0, 23);
        }
        if (request->hasParam(minuteKey, true)) {
            config.schedules[i].minute = clampU8(request->getParam(minuteKey, true)->value().toInt(), 0, 59);
        }
        config.schedules[i].enabled = request->hasParam(enabledKey, true);
    }
    config.scheduleCount = MAX_SCHEDULE_SLOTS;

    if (request->hasParam("irrigationDurationSec", true)) {
        config.irrigationDurationSec = clampU16(
            request->getParam("irrigationDurationSec", true)->value().toInt(), 0, MAX_IRRIGATION_DURATION_SEC);
    }
}

bool isLeapYear(int year) {
    return (year % 4 == 0 && year % 100 != 0) || (year % 400 == 0);
}

// Valida os campos de calendário antes de aceitar — mktime() normaliza datas
// fora da faixa (ex: 31/02 vira 03/03) em vez de rejeitar, então a checagem
// de faixa precisa acontecer antes de chamar mktime().
bool isValidCalendarDateTime(int year, int month, int day, int hour, int minute) {
    if (year < 2000 || year > 2099) return false;
    if (month < 1 || month > 12) return false;
    static const uint8_t daysInMonth[] = {31, 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31};
    uint8_t maxDay = daysInMonth[month - 1];
    if (month == 2 && isLeapYear(year)) maxDay = 29;
    if (day < 1 || day > maxDay) return false;
    if (hour < 0 || hour > 23) return false;
    if (minute < 0 || minute > 59) return false;
    return true;
}

// Aplica o horário digitado em /admin ("YYYY-MM-DDTHH:MM", vindo direto do
// <input type="datetime-local">, sem conversão de fuso no navegador) como o
// relógio do sistema — workaround pra falta de RTC físico.
bool applySystemTimeFromDatetimeLocal(const String& value) {
    int year, month, day, hour, minute;
    if (sscanf(value.c_str(), "%d-%d-%dT%d:%d", &year, &month, &day, &hour, &minute) != 5) {
        return false;
    }
    if (!isValidCalendarDateTime(year, month, day, hour, minute)) {
        return false;
    }
    struct tm timeinfo = {};
    timeinfo.tm_year = year - 1900;
    timeinfo.tm_mon = month - 1;
    timeinfo.tm_mday = day;
    timeinfo.tm_hour = hour;
    timeinfo.tm_min = minute;
    timeinfo.tm_sec = 0;
    time_t epoch = mktime(&timeinfo);
    if (epoch < 0) {
        return false;
    }
    struct timeval tv = {epoch, 0};
    return settimeofday(&tv, nullptr) == 0;
}

// Mapeia o motivo de bloqueio de uma tentativa de irrigação manual para uma
// mensagem legível, exibida como aviso no topo de /admin após o redirect.
String blockedNoticeFromQueryValue(const String& value) {
    if (value == "cooldown") {
        return "Irrigacao manual recusada: aguarde o intervalo minimo entre acionamentos (cooldown de " +
               String(IRRIGATION_COOLDOWN_SEC) + "s).";
    }
    if (value == "budget") {
        return "Irrigacao manual recusada: orcamento diario de agua ja foi atingido. Tente novamente amanha.";
    }
    return "";
}

}  // namespace

namespace WebServer {

void begin(AsyncWebServer& server, IrrigationConfig& config, const bool& valveOpen, bool& storageFault,
           std::function<ManualIrrigateResult(uint16_t)> manualIrrigate,
           std::function<void()> stopIrrigation) {
    // AsyncURIMatcher::exact() é necessário aqui: o construtor implícito a
    // partir de const char* usa o modo "BackwardCompatible" da lib, que
    // casa "/admin" com QUALQUER coisa começando com "/admin/" — sem isso,
    // a rota "/admin" (registrada primeiro) intercepta "/admin/config" e
    // "/admin/history" antes deles serem alcançados.
    server.on(AsyncURIMatcher::exact(Routes::STATUS), HTTP_GET, [](AsyncWebServerRequest* request) {
        request->send(200, "text/html", buildStatusHtml());
    });

    server.on(AsyncURIMatcher::exact(Routes::STATUS_JSON), HTTP_GET,
              [&config, &valveOpen, &storageFault](AsyncWebServerRequest* request) {
                  request->send(200, "application/json", buildStatusJson(config, valveOpen, storageFault));
              });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN), HTTP_GET, [&config](AsyncWebServerRequest* request) {
        String notice;
        if (request->hasParam("blocked")) {
            notice = blockedNoticeFromQueryValue(request->getParam("blocked")->value());
        }
        request->send(200, "text/html", buildAdminFormHtml(config, notice));
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_CONFIG), HTTP_POST,
              [&config, &storageFault](AsyncWebServerRequest* request) {
                  applyConfigFromRequest(request, config);
                  if (!saveConfig(config)) {
                      storageFault = true;
                      request->send(500, "text/plain", "Falha ao salvar configuracao");
                      return;
                  }
                  request->redirect(Routes::ADMIN);
              });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_TIME), HTTP_POST, [](AsyncWebServerRequest* request) {
        if (!request->hasParam("datetime", true) ||
            !applySystemTimeFromDatetimeLocal(request->getParam("datetime", true)->value())) {
            request->send(400, "text/plain", "Horario invalido");
            return;
        }
        request->redirect(Routes::ADMIN);
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_IRRIGATE), HTTP_POST,
              [&config, manualIrrigate](AsyncWebServerRequest* request) {
                  uint16_t duration = config.irrigationDurationSec;
                  if (request->hasParam("durationSec", true)) {
                      duration = clampU16(request->getParam("durationSec", true)->value().toInt(), 1,
                                           MAX_IRRIGATION_DURATION_SEC);
                  }
                  ManualIrrigateResult result = manualIrrigate(duration);
                  if (result == ManualIrrigateResult::BLOCKED_COOLDOWN) {
                      request->redirect(String(Routes::ADMIN) + "?blocked=cooldown");
                      return;
                  }
                  if (result == ManualIrrigateResult::BLOCKED_DAILY_BUDGET) {
                      request->redirect(String(Routes::ADMIN) + "?blocked=budget");
                      return;
                  }
                  request->redirect(Routes::ADMIN);
              });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_STOP), HTTP_POST, [stopIrrigation](AsyncWebServerRequest* request) {
        stopIrrigation();
        request->redirect(Routes::ADMIN);
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_HISTORY), HTTP_GET, [](AsyncWebServerRequest* request) {
        AsyncWebServerResponse* response = request->beginResponse(200, "text/csv", buildHistoryCsv());
        response->addHeader("Content-Disposition", "attachment; filename=history.csv");
        request->send(response);
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_HISTORY_RESET), HTTP_POST,
              [&storageFault](AsyncWebServerRequest* request) {
                  if (!clearHistory()) {
                      storageFault = true;
                      request->send(500, "text/plain", "Falha ao zerar historico");
                      return;
                  }
                  request->redirect(Routes::ADMIN);
              });
}

}  // namespace WebServer
