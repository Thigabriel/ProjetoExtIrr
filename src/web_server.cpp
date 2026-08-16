#include "web_server.h"

#include <Arduino.h>
#include <cstring>

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

String buildStatusJson(const IrrigationConfig& config) {
    String json = "{\"config\":{\"schedules\":[";
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

String buildAdminFormHtml(const IrrigationConfig& config) {
    String html =
        "<!DOCTYPE html><html><head><meta charset=\"utf-8\">"
        "<title>Irrigacao - Admin</title></head><body>"
        "<h1>Configuracao</h1>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_CONFIG) + "\">"
        "<h2>Horarios</h2>";

    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        const ScheduleSlot& slot = config.schedules[i];
        html += "<p>Slot " + String(i) +
                ": Hora <input type=\"number\" min=\"0\" max=\"23\" name=\"hour" + String(i) +
                "\" value=\"" + String(slot.hour) + "\">" +
                " Minuto <input type=\"number\" min=\"0\" max=\"59\" name=\"minute" + String(i) +
                "\" value=\"" + String(slot.minute) + "\">" +
                " <label><input type=\"checkbox\" name=\"enabled" + String(i) + "\"" +
                (slot.enabled ? " checked" : "") + "> ativo</label></p>";
    }

    html += "<h2>Limiar de umidade</h2>"
            "<p><label><input type=\"checkbox\" name=\"useThreshold\"" +
            String(config.useThreshold ? " checked" : "") +
            "> usar limiar</label></p>"
            "<p>Limiar (%): <input type=\"number\" min=\"0\" max=\"100\" name=\"moistureThreshold\" value=\"" +
            String(config.moistureThreshold) + "\"></p>"
            "<h2>Irrigacao</h2>"
            "<p>Duracao (s): <input type=\"number\" min=\"0\" name=\"irrigationDurationSec\" value=\"" +
            String(config.irrigationDurationSec) + "\"></p>"
            "<h2>Calibracao do sensor</h2>"
            "<p>Seco (raw): <input type=\"number\" min=\"0\" name=\"sensorDryRaw\" value=\"" +
            String(config.sensorDryRaw) + "\"></p>"
            "<p>Molhado (raw): <input type=\"number\" min=\"0\" name=\"sensorWetRaw\" value=\"" +
            String(config.sensorWetRaw) + "\"></p>"
            "<h2>Senha de admin</h2>"
            "<p>Nova senha: <input type=\"password\" name=\"adminPassword\" maxlength=\"" +
            String(ADMIN_PASSWORD_MAX_LEN - 1) + "\" placeholder=\"deixe em branco para manter a atual\"></p>"
            "<p><button type=\"submit\">Salvar</button></p>"
            "</form>"
            "<h2>Historico</h2>"
            "<p><a href=\"" + String(Routes::ADMIN_HISTORY) + "\">Baixar CSV</a></p>"
            "<form method=\"POST\" action=\"" + String(Routes::ADMIN_HISTORY_RESET) +
            "\" onsubmit=\"return confirm('Apagar todo o historico?');\">"
            "<button type=\"submit\">Zerar historico</button></form>"
            "</body></html>";
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

}  // namespace

namespace WebServer {

void begin(AsyncWebServer& server, IrrigationConfig& config) {
    // AsyncURIMatcher::exact() é necessário aqui: o construtor implícito a
    // partir de const char* usa o modo "BackwardCompatible" da lib, que
    // casa "/admin" com QUALQUER coisa começando com "/admin/" — sem isso,
    // a rota "/admin" (registrada primeiro) intercepta "/admin/config" e
    // "/admin/history" antes deles serem alcançados.
    server.on(AsyncURIMatcher::exact(Routes::STATUS), HTTP_GET, [&config](AsyncWebServerRequest* request) {
        request->send(200, "application/json", buildStatusJson(config));
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
