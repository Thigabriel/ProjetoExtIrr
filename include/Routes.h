#pragma once

// Contrato de rotas HTTP servidas pelo ESP32 em modo AP (192.168.4.1).
namespace Routes {
    constexpr const char* STATUS = "/status";                       // GET, aberto — pagina visual (HTML)
    constexpr const char* STATUS_JSON = "/status.json";             // GET, aberto — dados brutos (JSON), consumido pela pagina /status
    constexpr const char* ADMIN = "/admin";                         // GET, senha
    constexpr const char* ADMIN_CONFIG = "/admin/config";           // POST, senha
    constexpr const char* ADMIN_TIME = "/admin/time";                // POST, senha — define o horario atual (sem RTC ainda)
    constexpr const char* ADMIN_HISTORY = "/admin/history";         // GET, senha — baixa CSV
    constexpr const char* ADMIN_HISTORY_RESET = "/admin/history/reset"; // POST, senha
}
