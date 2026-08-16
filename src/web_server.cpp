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

// Autenticação HTTP Basic: usuário fixo "admin", senha = IrrigationConfig.adminPassword.
// Único par usuário/senha do sistema — ver include/Config.h (ADMIN_PASSWORD_MAX_LEN).
bool requireAuth(AsyncWebServerRequest* request, const IrrigationConfig& config) {
    if (request->authenticate("admin", config.adminPassword)) {
        return true;
    }
    request->requestAuthentication("admin");
    return false;
}

const char* reasonToString(TriggerReason reason) {
    switch (reason) {
        case TriggerReason::SCHEDULE:
            return "SCHEDULE";
        case TriggerReason::MANUAL:
            return "MANUAL";
        case TriggerReason::SKIPPED:
            return "SKIPPED";
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
    "input[type=number],input[type=password],input[type=datetime-local]{"
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

String buildStatusJson(const IrrigationConfig& config, bool valveOpen, uint8_t currentMoisture) {
    String json = "{\"valveOpen\":" + String(valveOpen ? "true" : "false") +
                  ",\"currentMoisturePercent\":" + String(currentMoisture) +
                  ",\"currentEpoch\":" + String(static_cast<uint32_t>(time(nullptr))) +
                  ",\"config\":{\"schedules\":[";
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        const ScheduleSlot& slot = config.schedules[i];
        if (i > 0) json += ",";
        json += "{\"hour\":" + String(slot.hour) +
                ",\"minute\":" + String(slot.minute) +
                ",\"enabled\":" + (slot.enabled ? "true" : "false") + "}";
    }
    json += "],\"scheduleCount\":" + String(config.scheduleCount) +
            ",\"moistureThreshold\":" + String(config.moistureThreshold) +
            ",\"useThreshold\":" + (config.useThreshold ? "true" : "false") +
            ",\"irrigationDurationSec\":" + String(config.irrigationDurationSec) +
            ",\"sensorDryRaw\":" + String(config.sensorDryRaw) +
            ",\"sensorWetRaw\":" + String(config.sensorWetRaw) +
            "}";

    size_t count = historyCount();
    HistoryEntry lastEntry;
    if (count > 0 && readHistoryEntry(count - 1, lastEntry)) {
        json += ",\"lastEntry\":{\"timestamp\":" + String(lastEntry.timestamp) +
                ",\"moisturePercent\":" + String(lastEntry.moisturePercent) +
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
        "<div class=\"card\" style=\"text-align:center\">"
        "<span id=\"valveBadge\" class=\"badge off\"><span class=\"dot\"></span>"
        "<span id=\"valveText\">Carregando...</span></span>"
        "</div>"
        "<div class=\"card\"><h2>Leitura atual</h2>"
        "<div class=\"stat\"><span>Umidade do solo</span><span id=\"moisture\">--</span></div>"
        "<div class=\"stat\"><span>Horario do sistema</span><span id=\"now\">--</span></div>"
        "</div>"
        "<div class=\"card\"><h2>Ultimo evento registrado</h2>"
        "<div class=\"stat\"><span>Quando</span><span id=\"lastWhen\">--</span></div>"
        "<div class=\"stat\"><span>Umidade na hora</span><span id=\"lastMoisture\">--</span></div>"
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
        "function fmtEpoch(e){if(!e)return '--';var d=new Date(e*1000);return d.toLocaleString();}"
        "function reasonLabel(r){return {SCHEDULE:'Irrigou',MANUAL:'Manual',SKIPPED:'Pulou (solo umido)'}[r]||r;}"
        "function refresh(){"
        "fetch('" + String(Routes::STATUS_JSON) + "').then(function(r){return r.json();}).then(function(d){"
        "var badge=document.getElementById('valveBadge');"
        "badge.className='badge '+(d.valveOpen?'on':'off');"
        "document.getElementById('valveText').textContent=d.valveOpen?'Irrigando agora':'Aguardando';"
        "document.getElementById('moisture').textContent=d.currentMoisturePercent+'%';"
        "document.getElementById('now').textContent=fmtTime(d.currentEpoch);"
        "if(d.lastEntry){"
        "document.getElementById('lastWhen').textContent=fmtEpoch(d.lastEntry.timestamp);"
        "document.getElementById('lastMoisture').textContent=d.lastEntry.moisturePercent+'%';"
        "document.getElementById('lastResult').textContent=reasonLabel(d.lastEntry.reason);"
        "}else{"
        "document.getElementById('lastWhen').textContent='Nenhum evento ainda';"
        "document.getElementById('lastMoisture').textContent='--';"
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

String buildAdminFormHtml(const IrrigationConfig& config) {
    String html = "<!DOCTYPE html><html><head>" + htmlHead("Irrigacao - Admin") +
        "</head><body>"
        "<header><h1>Administracao</h1><p>Irrigacao Comunitaria</p></header>"
        "<main>"

        "<div class=\"card\"><h2>Horario do sistema</h2>"
        "<p class=\"muted\">Sem RTC ainda: defina a hora atual manualmente. Ela reinicia toda vez "
        "que o ESP32 desliga ou reseta.</p>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_TIME) + "\">"
        "<label>Data e hora atuais</label>"
        "<input type=\"datetime-local\" name=\"datetime\" required>"
        "<button type=\"submit\">Definir horario</button>"
        "</form></div>"

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

    html += "<h2>Limiar de umidade</h2>"
            "<label class=\"chk\"><input type=\"checkbox\" name=\"useThreshold\"" +
            String(config.useThreshold ? " checked" : "") +
            "> Usar limiar (nao irrigar se o solo ja estiver umido)</label>"
            "<label>Limiar (%)</label>"
            "<input type=\"number\" min=\"0\" max=\"100\" name=\"moistureThreshold\" value=\"" +
            String(config.moistureThreshold) + "\">"
            "<h2>Duracao da irrigacao</h2>"
            "<label>Duracao (segundos)</label>"
            "<input type=\"number\" min=\"0\" name=\"irrigationDurationSec\" value=\"" +
            String(config.irrigationDurationSec) + "\">"
            "<h2>Calibracao do sensor</h2>"
            "<label>Leitura seco (raw)</label>"
            "<input type=\"number\" min=\"0\" name=\"sensorDryRaw\" value=\"" +
            String(config.sensorDryRaw) + "\">"
            "<label>Leitura molhado (raw)</label>"
            "<input type=\"number\" min=\"0\" name=\"sensorWetRaw\" value=\"" +
            String(config.sensorWetRaw) + "\">"
            "<h2>Senha de admin</h2>"
            "<label>Nova senha (em branco = manter a atual)</label>"
            "<input type=\"password\" name=\"adminPassword\" maxlength=\"" +
            String(ADMIN_PASSWORD_MAX_LEN - 1) + "\">"
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

String buildHistoryCsv() {
    String csv = "timestamp,moisturePercent,irrigated,durationSec,reason\n";
    size_t count = historyCount();
    HistoryEntry entry;
    for (size_t i = 0; i < count; i++) {
        if (!readHistoryEntry(i, entry)) continue;
        csv += String(entry.timestamp) + "," +
               String(entry.moisturePercent) + "," +
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

    config.useThreshold = request->hasParam("useThreshold", true);
    if (request->hasParam("moistureThreshold", true)) {
        config.moistureThreshold =
            clampU8(request->getParam("moistureThreshold", true)->value().toInt(), 0, 100);
    }
    if (request->hasParam("irrigationDurationSec", true)) {
        config.irrigationDurationSec =
            clampU16(request->getParam("irrigationDurationSec", true)->value().toInt(), 0, 65535);
    }
    if (request->hasParam("sensorDryRaw", true)) {
        config.sensorDryRaw = clampU16(request->getParam("sensorDryRaw", true)->value().toInt(), 0, 65535);
    }
    if (request->hasParam("sensorWetRaw", true)) {
        config.sensorWetRaw = clampU16(request->getParam("sensorWetRaw", true)->value().toInt(), 0, 65535);
    }

    // Campo em branco = mantém a senha atual (o form nunca ecoa a senha existente).
    if (request->hasParam("adminPassword", true)) {
        const String& newPassword = request->getParam("adminPassword", true)->value();
        if (newPassword.length() > 0) {
            strncpy(config.adminPassword, newPassword.c_str(), ADMIN_PASSWORD_MAX_LEN - 1);
            config.adminPassword[ADMIN_PASSWORD_MAX_LEN - 1] = '\0';
        }
    }
}

// Aplica o horário digitado em /admin ("YYYY-MM-DDTHH:MM", vindo direto do
// <input type="datetime-local">, sem conversão de fuso no navegador) como o
// relógio do sistema — workaround pra falta de RTC físico.
bool applySystemTimeFromDatetimeLocal(const String& value) {
    int year, month, day, hour, minute;
    if (sscanf(value.c_str(), "%d-%d-%dT%d:%d", &year, &month, &day, &hour, &minute) != 5) {
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

}  // namespace

namespace WebServer {

void begin(AsyncWebServer& server, IrrigationConfig& config, const bool& valveOpen,
           const uint8_t& currentMoisturePercent) {
    // AsyncURIMatcher::exact() é necessário aqui: o construtor implícito a
    // partir de const char* usa o modo "BackwardCompatible" da lib, que
    // casa "/admin" com QUALQUER coisa começando com "/admin/" — sem isso,
    // a rota "/admin" (registrada primeiro) intercepta "/admin/config" e
    // "/admin/history" antes deles serem alcançados.
    server.on(AsyncURIMatcher::exact(Routes::STATUS), HTTP_GET, [](AsyncWebServerRequest* request) {
        request->send(200, "text/html", buildStatusHtml());
    });

    server.on(AsyncURIMatcher::exact(Routes::STATUS_JSON), HTTP_GET,
              [&config, &valveOpen, &currentMoisturePercent](AsyncWebServerRequest* request) {
                  request->send(200, "application/json",
                                buildStatusJson(config, valveOpen, currentMoisturePercent));
              });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN), HTTP_GET, [&config](AsyncWebServerRequest* request) {
        if (!requireAuth(request, config)) return;
        request->send(200, "text/html", buildAdminFormHtml(config));
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_CONFIG), HTTP_POST, [&config](AsyncWebServerRequest* request) {
        if (!requireAuth(request, config)) return;
        applyConfigFromRequest(request, config);
        if (!saveConfig(config)) {
            request->send(500, "text/plain", "Falha ao salvar configuracao");
            return;
        }
        request->redirect(Routes::ADMIN);
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_TIME), HTTP_POST, [&config](AsyncWebServerRequest* request) {
        if (!requireAuth(request, config)) return;
        if (!request->hasParam("datetime", true) ||
            !applySystemTimeFromDatetimeLocal(request->getParam("datetime", true)->value())) {
            request->send(400, "text/plain", "Horario invalido");
            return;
        }
        request->redirect(Routes::ADMIN);
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_HISTORY), HTTP_GET, [&config](AsyncWebServerRequest* request) {
        if (!requireAuth(request, config)) return;
        AsyncWebServerResponse* response =
            request->beginResponse(200, "text/csv", buildHistoryCsv());
        response->addHeader("Content-Disposition", "attachment; filename=history.csv");
        request->send(response);
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_HISTORY_RESET), HTTP_POST, [&config](AsyncWebServerRequest* request) {
        if (!requireAuth(request, config)) return;
        if (!clearHistory()) {
            request->send(500, "text/plain", "Falha ao zerar historico");
            return;
        }
        request->redirect(Routes::ADMIN);
    });
}

}  // namespace WebServer
