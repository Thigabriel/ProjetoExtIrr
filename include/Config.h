#pragma once

#include <cstdint>

constexpr uint8_t MAX_SCHEDULE_SLOTS = 3;

// Limites de segurança fixos no firmware — não editáveis pela interface web,
// só recompilando. Ver README (Rotinas de segurança) para o racional de
// cada um.
constexpr uint8_t MAX_IRRIGATION_DURATION_MIN = 5;    // teto absoluto por acionamento
constexpr uint16_t MAX_IRRIGATION_DURATION_SEC = MAX_IRRIGATION_DURATION_MIN * 60;
constexpr uint16_t IRRIGATION_COOLDOWN_SEC = 10;      // intervalo mínimo entre acionamentos (fase de testes)
constexpr uint32_t DAILY_WATER_BUDGET_SEC = 900;      // orçamento diário de válvula aberta (15 min)

inline uint16_t irrigationDurationMinutesToSeconds(float durationMin) {
    if (!(durationMin > 0.0f)) return 0;
    if (durationMin >= MAX_IRRIGATION_DURATION_MIN) return MAX_IRRIGATION_DURATION_SEC;

    uint16_t durationSec = static_cast<uint16_t>(durationMin * 60.0f + 0.5f);
    return durationSec == 0 ? 1 : durationSec;
}

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

    float irrigationDurationMin; // duração da irrigação automática
    float manualIrrigationDurationMin; // duração do acionamento manual
};
