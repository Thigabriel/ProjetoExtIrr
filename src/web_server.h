#pragma once

#include <ESPAsyncWebServer.h>
#include <functional>

#include "Config.h"

// Resultado de uma tentativa de irrigação manual — permite a interface web
// explicar ao usuário por que um acionamento foi recusado (rotinas de
// segurança: cooldown e orçamento diário) em vez de falhar silenciosamente.
enum class ManualIrrigateResult : uint8_t {
    OK = 0,
    BLOCKED_COOLDOWN = 1,
    BLOCKED_DAILY_BUDGET = 2,
};

// Registra as rotas HTTP definidas em include/Routes.h no servidor assíncrono.
//
// Fase de testes: sem autenticação em nenhuma rota (removida de propósito
// para não atrapalhar testes locais). Reintroduzir antes de qualquer
// implantação real na comunidade.
//
// `config` é a configuração em RAM compartilhada com o restante do firmware
// (carregada no boot via Storage::loadConfig). As rotas leem dela para
// responder e a atualizam (+ Storage::saveConfig) quando /admin/config
// recebe um POST. `valveOpen` é só leitura aqui — usada para mostrar o
// estado ao vivo em /status. `storageFault` é lida e também escrita aqui
// (fica true se um saveConfig falhar durante um POST /admin/config) —
// exibida como aviso genérico de falha em /status.
// `manualIrrigate(durationSec)` é fornecido pelo main.cpp: aplica as travas
// de cooldown/orçamento diário, abre a válvula se permitido e registra um
// HistoryEntry (MANUAL ou BLOCKED_*), retornando o resultado.
// `stopIrrigation()` fecha a válvula imediatamente (parada de emergência),
// independente do que estiver em andamento.
namespace WebServer {
    void begin(AsyncWebServer& server, IrrigationConfig& config, const bool& valveOpen, bool& storageFault,
               std::function<ManualIrrigateResult(uint16_t durationSec)> manualIrrigate,
               std::function<void()> stopIrrigation);
}
