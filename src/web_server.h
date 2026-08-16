#pragma once

#include <ESPAsyncWebServer.h>
#include <functional>

#include "Config.h"

// Registra as rotas HTTP definidas em include/Routes.h no servidor assíncrono.
//
// `config` é a configuração em RAM compartilhada com o restante do firmware
// (carregada no boot via Storage::loadConfig). As rotas leem dela para
// responder e a atualizam (+ Storage::saveConfig) quando /admin/config
// recebe um POST autenticado. `valveOpen` e `currentMoisturePercent` são só
// leitura aqui — usados para mostrar o estado ao vivo em /status.
// `manualIrrigate(durationSec)` é fornecido pelo main.cpp: abre a válvula e
// registra um HistoryEntry com TriggerReason::MANUAL.
namespace WebServer {
    void begin(AsyncWebServer& server, IrrigationConfig& config, const bool& valveOpen,
               const uint8_t& currentMoisturePercent,
               std::function<void(uint16_t durationSec)> manualIrrigate);
}
