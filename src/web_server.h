#pragma once

#include <ESPAsyncWebServer.h>

#include "Config.h"

// Registra as rotas HTTP definidas em include/Routes.h no servidor assíncrono.
//
// `config` é a configuração em RAM compartilhada com o restante do firmware
// (carregada no boot via Storage::loadConfig). As rotas leem dela para
// responder e a atualizam (+ Storage::saveConfig) quando /admin/config
// recebe um POST autenticado.
namespace WebServer {
    void begin(AsyncWebServer& server, IrrigationConfig& config);
}
