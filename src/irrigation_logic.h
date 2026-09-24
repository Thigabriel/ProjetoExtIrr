#pragma once

#include "Config.h"

// Resultado da decisão de irrigação para o instante avaliado.
struct IrrigationDecision {
    bool scheduleMatched; // true se algum slot habilitado bate com hour/minute
    uint16_t durationSec; // config.irrigationDurationSec quando scheduleMatched, senão 0
};

// Decide se algum horário programado bate com o instante atual (RTC).
// Função pura, sem I/O. Sem sensor de umidade nesta fase: não há confirmação
// por limiar, só o horário.
IrrigationDecision decideIrrigation(const IrrigationConfig& config,
                                     uint8_t currentHour,
                                     uint8_t currentMinute);
