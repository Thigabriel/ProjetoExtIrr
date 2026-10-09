#include "web_server.h"

#include <Arduino.h>
#include <cstdio>
#include <time.h>
#include <WiFi.h>

#include "CloudHistory.h"
#include "Routes.h"
#include "Storage.h"

namespace {

String formatDurationMinutes(float durationMin) {
    String formatted = String(durationMin, 3);
    while (formatted.endsWith("0")) {
        formatted.remove(formatted.length() - 1);
    }
    if (formatted.endsWith(".")) {
        formatted.remove(formatted.length() - 1);
    }
    return formatted;
}

void durationParts(float durationMin, uint16_t& minutes, uint8_t& seconds) {
    uint16_t totalSeconds = irrigationDurationMinutesToSeconds(durationMin);
    minutes = totalSeconds / 60;
    seconds = totalSeconds % 60;
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
    "input[type=number]{"
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
    ".notice{display:none;border:1px solid #e6b8b4;color:var(--danger)}"
    ".remote{max-width:960px}"
    ".table-wrap{overflow-x:auto;max-height:420px;margin-top:12px}"
    "table{width:100%;border-collapse:collapse;font-size:.85rem;white-space:nowrap}"
    "th,td{padding:9px 8px;border-bottom:1px solid #eef1ee;text-align:left}"
    "th{position:sticky;top:0;background:var(--card);color:var(--muted);font-weight:600}"
    ".progress{height:12px;background:#eef1ee;border-radius:999px;overflow:hidden;margin:10px 0}"
    ".progress div{height:100%;background:var(--green)}"
    "button:disabled{opacity:.55;cursor:not-allowed}"
    "</style>";

String htmlHead(const char* title) {
    return String("<meta charset=\"utf-8\"><meta name=\"viewport\" "
                   "content=\"width=device-width, initial-scale=1\"><title>") +
           title + "</title>" + PAGE_STYLE;
}

String buildStatusJson(const IrrigationConfig& config, bool valveOpen, uint16_t valveRemainingSec, bool storageFault) {
    String json = "{\"valveOpen\":" + String(valveOpen ? "true" : "false") +
                  ",\"valveRemainingSec\":" + String(valveRemainingSec) +
                  ",\"currentEpoch\":" + String(static_cast<uint32_t>(time(nullptr))) +
                  ",\"clockSynchronized\":" + String(time(nullptr) >= 1704067200 ? "true" : "false") +
                  ",\"stationConnected\":" + String(WiFi.status() == WL_CONNECTED ? "true" : "false") +
                  ",\"stationIp\":\"" + WiFi.localIP().toString() + "\"" +
                  ",\"cloudConfigured\":" + String(CloudHistory::isConfigured() ? "true" : "false") +
                  ",\"cloudConnected\":" + String(CloudHistory::isConnected() ? "true" : "false") +
                  ",\"cloudPending\":" + String(CloudHistory::pendingCount()) +
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
            ",\"irrigationDurationMin\":" + formatDurationMinutes(config.irrigationDurationMin) +
            ",\"manualIrrigationDurationMin\":" + formatDurationMinutes(config.manualIrrigationDurationMin) +
            "}";

    json += "}";
    return json;
}

String buildStatusHtml() {
    String html = "<!DOCTYPE html><html><head>" + htmlHead("Irrigacao - Status") +
        "</head><body>"
        "<header><h1>Irrigacao Comunitaria</h1><p>Horta local</p></header>"
        "<main>"
        "<div id=\"faultCard\" class=\"card notice\">"
        "<h2 style=\"color:var(--danger)\">Falha detectada</h2>"
        "<p>O sistema nao conseguiu salvar uma configuracao no armazenamento interno. "
        "Entre em contato com o professor responsavel pelo projeto.</p>"
        "</div>"
        "<div class=\"card\" style=\"text-align:center\">"
        "<span id=\"valveBadge\" class=\"badge off\"><span class=\"dot\"></span>"
        "<span id=\"valveText\">Carregando...</span></span>"
        "<div class=\"stat\"><span>Tempo para fechamento</span><span id=\"valveCountdown\">--</span></div>"
        "</div>"
        "<div class=\"card\"><h2>Data e hora</h2>"
        "<div class=\"stat\"><span>Agora</span><span id=\"now\">--</span></div>"
        "<div class=\"stat\"><span>Internet</span><span id=\"network\">Verificando</span></div>"
        "</div>"
        "<div id=\"actionNotice\" class=\"card notice\"></div>"
        "<div class=\"card\"><h2>Controle da irrigacao</h2>"
        "<p class=\"muted\">Duracao manual: <strong id=\"duration\">--</strong></p>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_IRRIGATE) + "\">"
        "<input type=\"hidden\" name=\"durationMinutes\" id=\"durationMinutes\">"
        "<input type=\"hidden\" name=\"durationSeconds\" id=\"durationSeconds\">"
        "<button type=\"submit\" id=\"irrigateButton\" disabled>Irrigar agora</button></form>"
        "<form method=\"POST\" action=\"" + String(Routes::ADMIN_STOP) + "\">"
        "<button type=\"submit\" class=\"danger\" id=\"stopButton\" disabled>Parar irrigacao</button></form>"
        "</div>"
        "<a class=\"link\" href=\"" + String(Routes::REMOTE) + "\">Abrir painel completo &rarr;</a>"
        "<div class=\"card\"><h2>Ultima vez irrigado</h2>"
        "<div class=\"stat\"><span>Data e hora</span><span id=\"lastWhen\">--</span></div>"
        "<div class=\"stat\"><span>Duracao</span><span id=\"lastDuration\">--</span></div>"
        "</div>"
        "</main>"
        "<script>"
        "function pad(n){return String(n).padStart(2,'0');}"
        "var projectTimeZone='America/Sao_Paulo';"
        "function fmtEpoch(e,timeZone){if(!e)return '--';return new Intl.DateTimeFormat('pt-BR',{timeZone:timeZone||projectTimeZone,dateStyle:'short',timeStyle:'short'}).format(new Date(e*1000));}"
        "function formatDuration(seconds){var minutes=Math.floor(seconds/60),rest=seconds%60;"
        "return (minutes?minutes+' min':'')+(minutes&&rest?' ':'')+(rest?rest+' s':'')||'0 s';}"
        "var valveDeadline=0;"
        "function updateValveCountdown(){var remaining=Math.max(0,Math.ceil((valveDeadline-Date.now())/1000));"
        "document.getElementById('valveCountdown').textContent=valveDeadline?(remaining?formatDuration(remaining):'Fechando...'):'Valvula fechada';}"
        "function refresh(){"
        "fetch('" + String(Routes::STATUS_JSON) + "').then(function(r){return r.json();}).then(function(d){"
        "document.getElementById('faultCard').style.display=d.storageFault?'block':'none';"
        "var badge=document.getElementById('valveBadge');"
        "badge.className='badge '+(d.valveOpen?'on':'off');"
        "document.getElementById('valveText').textContent=d.valveOpen?'Irrigando agora':'Aguardando';"
        "valveDeadline=d.valveOpen?Date.now()+Number(d.valveRemainingSec||0)*1000:0;updateValveCountdown();"
        "document.getElementById('now').textContent=fmtEpoch(d.currentEpoch);"
        "document.getElementById('network').textContent=d.stationConnected?'Conectado ('+d.stationIp+')':'Sem internet';"
        "var duration=Math.round(Number(d.config.manualIrrigationDurationMin)*60);"
        "document.getElementById('duration').textContent=formatDuration(duration);"
        "document.getElementById('durationMinutes').value=Math.floor(duration/60);"
        "document.getElementById('durationSeconds').value=duration%60;"
        "document.getElementById('irrigateButton').textContent='Irrigar agora por '+formatDuration(duration);"
        "document.getElementById('irrigateButton').disabled=d.valveOpen;"
        "document.getElementById('stopButton').disabled=!d.valveOpen;"
        "});"
        "}"
        "function refreshLastIrrigation(){fetch('" + String(Routes::CLOUD_HISTORY_JSON) + "').then(function(r){return r.json();}).then(function(d){"
        "if(d.timeZone)projectTimeZone=d.timeZone;"
        "var entry=(d.history||[]).find(function(item){return item.irrigated;});"
        "document.getElementById('lastWhen').textContent=entry?fmtEpoch(entry.timestamp,d.timeZone):'Nenhuma irrigacao registrada';"
        "document.getElementById('lastDuration').textContent=entry?formatDuration(entry.durationSec):'--';});}"
        "var params=new URLSearchParams(location.search),notice=document.getElementById('actionNotice');"
        "if(params.get('blocked')==='cooldown'){notice.textContent='Aguarde o intervalo minimo entre irrigacoes.';notice.style.display='block';}"
        "if(params.get('blocked')==='budget'){notice.textContent='O limite diario de irrigacao foi atingido.';notice.style.display='block';}"
        "refresh();refreshLastIrrigation();setInterval(refresh,5000);setInterval(refreshLastIrrigation,30000);"
        "setInterval(updateValveCountdown,1000);"
        "</script>"
        "</body></html>";
    return html;
}

String buildAdminFormHtml(const IrrigationConfig& config, const String& notice, bool valveOpen,
                          bool storageFault) {
    bool anyScheduleActive = false;
    uint16_t durationMinutes;
    uint8_t durationSeconds;
    durationParts(config.irrigationDurationMin, durationMinutes, durationSeconds);
    uint16_t manualDurationMinutes;
    uint8_t manualDurationSeconds;
    durationParts(config.manualIrrigationDurationMin, manualDurationMinutes, manualDurationSeconds);
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        if (config.schedules[i].enabled) anyScheduleActive = true;
    }

    String html = "<!DOCTYPE html><html><head>" + htmlHead("Irrigacao - Painel completo") +
        "</head><body>"
        "<header><h1>Painel completo</h1><p>Irrigacao Comunitaria</p></header>"
        "<main class=\"remote\">"
        "<div class=\"card\"><h2>Estado do sistema</h2>"
        "<div class=\"stat\"><span>Valvula</span><span>" + String(valveOpen ? "Irrigando" : "Fechada") + "</span></div>"
        "<div class=\"stat\"><span>Data e hora</span><span id=\"remoteNow\">--</span></div>"
        "<div class=\"stat\"><span>Wi-Fi</span><span id=\"remoteNetwork\">Verificando</span></div>"
        "<div class=\"stat\"><span>Falha ao salvar configuracao</span><span>" + String(storageFault ? "Sim" : "Nao") + "</span></div>"
        "</div>"
        "<div class=\"card\"><h2>Google Sheets</h2>"
        "<div class=\"stat\"><span>Estado</span><span id=\"cloudState\">Verificando</span></div>"
        "<div class=\"stat\"><span>Na fila de envio</span><span id=\"cloudPending\">0</span></div>"
        "<a id=\"spreadsheetLink\" class=\"link\" style=\"display:none\" target=\"_blank\" rel=\"noopener\">Abrir planilha</a>"
        "</div>"
        "<div class=\"card\"><h2>Historico recente</h2>"
        "<p id=\"historyCount\" class=\"muted\">Carregando registros...</p>"
        "<p id=\"historyError\" class=\"muted\"></p>"
        "<div class=\"table-wrap\"><table><thead><tr><th>Data e hora</th><th>Irrigou?</th><th>Duracao</th><th>Motivo</th></tr></thead>"
        "<tbody id=\"historyRows\"></tbody></table></div>"
        "</div>";

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
            "<p class=\"muted\">Defina a duracao com numeros inteiros (maximo " + String(MAX_IRRIGATION_DURATION_MIN) + " minutos).</p>"
            "<div class=\"row\"><div><label>Minutos</label>"
            "<input type=\"number\" min=\"0\" max=\"" + String(MAX_IRRIGATION_DURATION_MIN) +
            "\" step=\"1\" name=\"durationMinutes\" value=\"" + String(durationMinutes) + "\"></div>"
            "<div><label>Segundos</label>"
            "<input type=\"number\" min=\"0\" max=\"59\" step=\"1\" name=\"durationSeconds\" value=\"" + String(durationSeconds) + "\"></div></div>"
            "<button type=\"submit\">Salvar</button>"
            "</form></div>"

            "<div class=\"card\"><form method=\"POST\" action=\"" + String(Routes::ADMIN_CONFIG) + "\">"
            "<h2>Duracao da irrigacao manual</h2>"
            "<p class=\"muted\">Esta duracao vale somente para o botao da tela local.</p>"
            "<div class=\"row\"><div><label>Minutos</label>"
            "<input type=\"number\" min=\"0\" max=\"" + String(MAX_IRRIGATION_DURATION_MIN) +
            "\" step=\"1\" name=\"manualDurationMinutes\" value=\"" + String(manualDurationMinutes) + "\"></div>"
            "<div><label>Segundos</label>"
            "<input type=\"number\" min=\"0\" max=\"59\" step=\"1\" name=\"manualDurationSeconds\" value=\"" + String(manualDurationSeconds) + "\"></div></div>"
            "<button type=\"submit\">Salvar duracao manual</button>"
            "</form></div>"

            "<a class=\"link\" href=\"" + String(Routes::STATUS) + "\">Voltar ao status local &larr;</a>"
            "</main>"
            "<script>"
            "var projectTimeZone='America/Sao_Paulo';"
            "function updateRemoteStatus(){fetch('" + String(Routes::STATUS_JSON) + "').then(function(r){return r.json();}).then(function(d){"
            "document.getElementById('remoteNow').textContent=d.clockSynchronized?new Intl.DateTimeFormat('pt-BR',{timeZone:projectTimeZone,dateStyle:'short',timeStyle:'short'}).format(new Date(d.currentEpoch*1000)):'Aguardando NTP';"
            "document.getElementById('remoteNetwork').textContent=d.stationConnected?'Conectado ('+d.stationIp+')':'Sem internet';"
            "document.getElementById('cloudState').textContent=!d.cloudConfigured?'Endpoint nao configurado':d.cloudConnected?'Conectado':'Sem resposta';"
            "document.getElementById('cloudPending').textContent=d.cloudPending;});}"
            "function updateCloudHistory(){fetch('" + String(Routes::CLOUD_HISTORY_JSON) + "').then(function(r){return r.json();}).then(function(d){"
            "if(d.timeZone)projectTimeZone=d.timeZone;"
            "var rows=document.getElementById('historyRows');rows.textContent='';"
            "var timeZone=d.timeZone||'America/Sao_Paulo';"
            "document.getElementById('historyCount').textContent=d.total+' registro(s) no Sheets; exibindo ate 25 recentes.';"
            "document.getElementById('historyError').textContent=d.ok?'':(d.error||'Aguardando conexao com a planilha.');"
            "if(d.spreadsheetUrl){var link=document.getElementById('spreadsheetLink');link.href=d.spreadsheetUrl;link.style.display='inline-block';}"
            "(d.history||[]).forEach(function(item){var row=document.createElement('tr');"
            "[new Intl.DateTimeFormat('pt-BR',{timeZone:timeZone,dateStyle:'short',timeStyle:'short'}).format(new Date(item.timestamp*1000)),item.irrigated?'SIM':'NÃO',formatDuration(Number(item.durationSec)),item.reason].forEach(function(value){var cell=document.createElement('td');cell.textContent=value;row.appendChild(cell);});rows.appendChild(row);});});}"
            "updateRemoteStatus();setInterval(updateRemoteStatus,5000);"
            "updateCloudHistory();setInterval(updateCloudHistory,30000);"
            "</script></body></html>";
    return html;
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

float clampDurationMinutes(float value) {
    if (!(value >= 0.0f)) return 0.0f;
    if (value > MAX_IRRIGATION_DURATION_MIN) return MAX_IRRIGATION_DURATION_MIN;
    return value;
}

uint16_t clampDurationSeconds(long minutes, long seconds) {
    if (minutes < 0) minutes = 0;
    if (seconds < 0) seconds = 0;
    if (seconds > 59) seconds = 59;
    uint32_t total = static_cast<uint32_t>(minutes) * 60U + static_cast<uint32_t>(seconds);
    if (total > MAX_IRRIGATION_DURATION_SEC) return MAX_IRRIGATION_DURATION_SEC;
    return static_cast<uint16_t>(total);
}

float durationMinutesFromRequest(AsyncWebServerRequest* request, const char* minutesKey,
                                 const char* secondsKey, const char* legacyKey = nullptr) {
    if (request->hasParam(minutesKey, true) || request->hasParam(secondsKey, true)) {
        long minutes = request->hasParam(minutesKey, true)
                           ? request->getParam(minutesKey, true)->value().toInt()
                           : 0;
        long seconds = request->hasParam(secondsKey, true)
                           ? request->getParam(secondsKey, true)->value().toInt()
                           : 0;
        return static_cast<float>(clampDurationSeconds(minutes, seconds)) / 60.0f;
    }
    if (legacyKey != nullptr && request->hasParam(legacyKey, true)) {
        return clampDurationMinutes(request->getParam(legacyKey, true)->value().toFloat());
    }
    return -1.0f;
}

void applyConfigFromRequest(AsyncWebServerRequest* request, IrrigationConfig& config) {
    bool scheduleSettingsSubmitted = false;
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; i++) {
        String hourKey = "hour" + String(i);
        String minuteKey = "minute" + String(i);
        String enabledKey = "enabled" + String(i);

        bool slotSubmitted = request->hasParam(hourKey, true) || request->hasParam(minuteKey, true);
        scheduleSettingsSubmitted = scheduleSettingsSubmitted || slotSubmitted;
        if (!slotSubmitted) continue;

        if (request->hasParam(hourKey, true)) {
            config.schedules[i].hour = clampU8(request->getParam(hourKey, true)->value().toInt(), 0, 23);
        }
        if (request->hasParam(minuteKey, true)) {
            config.schedules[i].minute = clampU8(request->getParam(minuteKey, true)->value().toInt(), 0, 59);
        }
        config.schedules[i].enabled = request->hasParam(enabledKey, true);
    }
    if (scheduleSettingsSubmitted) {
        config.scheduleCount = MAX_SCHEDULE_SLOTS;
    }

    float requestedDuration = durationMinutesFromRequest(request, "durationMinutes", "durationSeconds",
                                                         "irrigationDurationMin");
    if (requestedDuration >= 0.0f) {
        config.irrigationDurationMin = requestedDuration;
    }
    float requestedManualDuration = durationMinutesFromRequest(request, "manualDurationMinutes",
                                                               "manualDurationSeconds");
    if (requestedManualDuration >= 0.0f) {
        config.manualIrrigationDurationMin = requestedManualDuration;
    }
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
           std::function<uint16_t()> remainingValveSeconds,
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
              [&config, &valveOpen, &storageFault, remainingValveSeconds](AsyncWebServerRequest* request) {
                  request->send(200, "application/json",
                                buildStatusJson(config, valveOpen, remainingValveSeconds(), storageFault));
              });

    server.on(AsyncURIMatcher::exact(Routes::CLOUD_HISTORY_JSON), HTTP_GET,
              [](AsyncWebServerRequest* request) {
                  request->send(200, "application/json", CloudHistory::historyJson());
              });

    server.on(AsyncURIMatcher::exact(Routes::REMOTE), HTTP_GET,
              [&config, &valveOpen, &storageFault](AsyncWebServerRequest* request) {
        String notice;
        if (request->hasParam("blocked")) {
            notice = blockedNoticeFromQueryValue(request->getParam("blocked")->value());
        }
        request->send(200, "text/html", buildAdminFormHtml(config, notice, valveOpen, storageFault));
    });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN), HTTP_GET, [](AsyncWebServerRequest* request) {
        request->redirect(Routes::REMOTE);
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

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_IRRIGATE), HTTP_POST,
              [&config, manualIrrigate](AsyncWebServerRequest* request) {
                  uint16_t duration = irrigationDurationMinutesToSeconds(config.manualIrrigationDurationMin);
                  float requestedDuration = durationMinutesFromRequest(request, "durationMinutes", "durationSeconds",
                                                                       "durationMin");
                  if (requestedDuration >= 0.0f) {
                      duration = irrigationDurationMinutesToSeconds(requestedDuration);
                  }
                  ManualIrrigateResult result = manualIrrigate(duration);
                  if (result == ManualIrrigateResult::BLOCKED_COOLDOWN) {
                      request->redirect(String(Routes::STATUS) + "?blocked=cooldown");
                      return;
                  }
                  if (result == ManualIrrigateResult::BLOCKED_DAILY_BUDGET) {
                      request->redirect(String(Routes::STATUS) + "?blocked=budget");
                      return;
                  }
                  request->redirect(Routes::STATUS);
              });

    server.on(AsyncURIMatcher::exact(Routes::ADMIN_STOP), HTTP_POST, [stopIrrigation](AsyncWebServerRequest* request) {
        stopIrrigation();
        request->redirect(Routes::STATUS);
    });

}

}  // namespace WebServer
