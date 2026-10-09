#pragma once

// Contrato de rotas HTTP servidas pelo ESP32 em modo AP (192.168.4.1).
namespace Routes {
    constexpr const char* ROOT = "/";                                // GET — redireciona para o painel completo (endereco mostrado na tela LCD)
    constexpr const char* STATUS = "/status";                       // GET, aberto — pagina visual (HTML)
    constexpr const char* STATUS_JSON = "/status.json";             // GET, aberto — dados brutos (JSON), consumido pela pagina /status
    constexpr const char* REMOTE = "/remote";                       // GET, aberto — painel completo
    constexpr const char* CLOUD_HISTORY_JSON = "/cloud/history.json"; // GET, cache do histórico Google Sheets
    constexpr const char* ADMIN = "/admin";                         // GET, senha
    constexpr const char* ADMIN_CONFIG = "/admin/config";           // POST, senha
    constexpr const char* ADMIN_IRRIGATE = "/admin/irrigate";       // POST, senha — abre a valvula agora, por N minutos
    constexpr const char* ADMIN_STOP = "/admin/stop";                // POST, senha — fecha a valvula agora (parada de emergencia)
}
