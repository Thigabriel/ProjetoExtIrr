#pragma once

#include <cstdint>

constexpr uint8_t MAX_SCHEDULE_SLOTS = 2;

// Limites de segurança fixos no firmware — não editáveis pela interface web,
// só recompilando. Ver README (Rotinas de segurança) para o racional de
// cada um.
constexpr uint16_t MAX_IRRIGATION_DURATION_SEC = 300; // teto absoluto por acionamento (5 min)
constexpr uint16_t IRRIGATION_COOLDOWN_SEC = 10;      // intervalo mínimo entre acionamentos (fase de testes)
constexpr uint32_t DAILY_WATER_BUDGET_SEC = 900;      // orçamento diário de válvula aberta (15 min)

struct ScheduleSlot {
    uint8_t hour;   // 0-23
    uint8_t minute; // 0-59
    bool enabled;
};

// Configuração persistida em SPIFFS/LittleFS, editável via POST /admin/config.
// Sem sensor de umidade nesta fase do projeto: a irrigação é só por horário
// programado, sem confirmação por limiar — ver README (Rotinas de
// segurança) sobre o orçamento diário como salvaguarda nesse cenário.
struct IrrigationConfig {
    ScheduleSlot schedules[MAX_SCHEDULE_SLOTS];
    uint8_t scheduleCount;

    uint16_t irrigationDurationSec; // duração da abertura da válvula ("intensidade")
};
