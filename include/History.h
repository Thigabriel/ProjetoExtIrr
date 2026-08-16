#pragma once

#include <cstdint>

// Motivo do evento registrado no histórico.
enum class TriggerReason : uint8_t {
    SCHEDULE = 0, // horário programado chegou e a válvula abriu
    MANUAL = 1,   // acionamento manual via /admin
    SKIPPED = 2,  // horário programado chegou, mas o limiar de umidade evitou a rega
};

// Um registro append-only no log de histórico (SPIFFS/LittleFS).
struct HistoryEntry {
    uint32_t timestamp;       // unix epoch, vindo do RTC
    uint8_t moisturePercent;  // leitura convertida no momento do evento
    bool irrigated;           // se a válvula abriu
    uint16_t durationSec;     // tempo de abertura (0 se não irrigou)
    TriggerReason reason;
};
