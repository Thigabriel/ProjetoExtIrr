#pragma once

#include <cstdint>

constexpr uint8_t MAX_SCHEDULE_SLOTS = 2;
constexpr uint8_t ADMIN_PASSWORD_MAX_LEN = 32;

struct ScheduleSlot {
    uint8_t hour;   // 0-23
    uint8_t minute; // 0-59
    bool enabled;
};

// Configuração persistida em SPIFFS/LittleFS, editável via POST /admin/config.
struct IrrigationConfig {
    ScheduleSlot schedules[MAX_SCHEDULE_SLOTS];
    uint8_t scheduleCount;

    uint8_t moistureThreshold; // 0-100%, irriga só se leitura < isso
    bool useThreshold;         // liga/desliga a checagem de limiar

    uint16_t irrigationDurationSec; // duração da abertura da válvula ("intensidade")

    // Calibração do sensor capacitivo: leitura ADC bruta nos extremos.
    uint16_t sensorDryRaw; // leitura com sensor seco/no ar
    uint16_t sensorWetRaw; // leitura com sensor em água

    char adminPassword[ADMIN_PASSWORD_MAX_LEN];
};
