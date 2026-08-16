#pragma once

#include "Config.h"
#include "History.h"

// Resultado da decisão de irrigação para o instante avaliado.
struct IrrigationDecision {
    bool scheduleMatched;    // true se algum slot habilitado bate com hour/minute
    bool shouldIrrigate;     // true se a válvula deve abrir
    uint16_t durationSec;    // config.irrigationDurationSec se shouldIrrigate, senão 0
    TriggerReason reason;    // válido apenas quando scheduleMatched == true
};

// Decide se deve irrigar agora, dado o config, a leitura de umidade já
// convertida (0-100%) e o horário atual (RTC). Função pura, sem I/O.
IrrigationDecision decideIrrigation(const IrrigationConfig& config,
                                     uint8_t moisturePercent,
                                     uint8_t currentHour,
                                     uint8_t currentMinute);
