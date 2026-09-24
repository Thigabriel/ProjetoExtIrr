#include <Arduino.h> // fornece size_t antes de Storage.h ser processado

#include "Storage.h"

#include <FS.h>
#include <SPIFFS.h>

// Persistência em SPIFFS. Ambos os arquivos guardam os structs de Config.h/
// History.h como bytes crus (sizeof(struct) por registro) — sem um formato
// portável (sem JSON, sem endianness explícito): válido porque quem grava e
// quem lê é sempre o mesmo firmware ESP32/Xtensa, então o layout é estável
// entre boots. Se os structs mudarem de forma incompatível, os arquivos
// antigos devem ser apagados (voltam a valores padrão / histórico vazio).
namespace {

constexpr const char* CONFIG_PATH = "/config.bin";
constexpr const char* HISTORY_PATH = "/history.bin";

bool mounted = false;
bool mountAttempted = false;

bool ensureMounted() {
    if (mountAttempted) {
        return mounted;
    }
    mountAttempted = true;
    mounted = SPIFFS.begin(true); // formata automaticamente se o FS ainda não existir
    return mounted;
}

void applyDefaultConfig(IrrigationConfig& config) {
    config.scheduleCount = 0;
    for (uint8_t i = 0; i < MAX_SCHEDULE_SLOTS; ++i) {
        config.schedules[i].hour = 0;
        config.schedules[i].minute = 0;
        config.schedules[i].enabled = false;
    }

    config.irrigationDurationSec = 10;
}

} // namespace

bool loadConfig(IrrigationConfig& outConfig) {
    if (!ensureMounted()) {
        applyDefaultConfig(outConfig);
        return false;
    }

    if (!SPIFFS.exists(CONFIG_PATH)) {
        // Primeiro boot: ainda não há config salva.
        applyDefaultConfig(outConfig);
        return true;
    }

    File file = SPIFFS.open(CONFIG_PATH, FILE_READ);
    if (!file) {
        applyDefaultConfig(outConfig);
        return false;
    }

    bool ok = file.size() == sizeof(IrrigationConfig) &&
              file.read(reinterpret_cast<uint8_t*>(&outConfig), sizeof(IrrigationConfig)) ==
                  sizeof(IrrigationConfig);
    file.close();

    if (!ok) {
        applyDefaultConfig(outConfig);
        return false;
    }

    return true;
}

bool saveConfig(const IrrigationConfig& config) {
    if (!ensureMounted()) {
        return false;
    }

    File file = SPIFFS.open(CONFIG_PATH, FILE_WRITE);
    if (!file) {
        return false;
    }

    size_t written = file.write(reinterpret_cast<const uint8_t*>(&config), sizeof(IrrigationConfig));
    file.close();

    return written == sizeof(IrrigationConfig);
}

bool appendHistoryEntry(const HistoryEntry& entry) {
    if (!ensureMounted()) {
        return false;
    }

    File file = SPIFFS.open(HISTORY_PATH, FILE_APPEND);
    if (!file) {
        return false;
    }

    size_t written = file.write(reinterpret_cast<const uint8_t*>(&entry), sizeof(HistoryEntry));
    file.close();

    return written == sizeof(HistoryEntry);
}

size_t historyCount() {
    if (!ensureMounted() || !SPIFFS.exists(HISTORY_PATH)) {
        return 0;
    }

    File file = SPIFFS.open(HISTORY_PATH, FILE_READ);
    if (!file) {
        return 0;
    }

    size_t count = file.size() / sizeof(HistoryEntry);
    file.close();

    return count;
}

bool readHistoryEntry(size_t index, HistoryEntry& outEntry) {
    if (!ensureMounted() || !SPIFFS.exists(HISTORY_PATH)) {
        return false;
    }

    File file = SPIFFS.open(HISTORY_PATH, FILE_READ);
    if (!file) {
        return false;
    }

    size_t offset = index * sizeof(HistoryEntry);
    bool ok = false;
    if (offset + sizeof(HistoryEntry) <= file.size() && file.seek(offset, SeekSet)) {
        ok = file.read(reinterpret_cast<uint8_t*>(&outEntry), sizeof(HistoryEntry)) == sizeof(HistoryEntry);
    }
    file.close();

    return ok;
}

bool clearHistory() {
    if (!ensureMounted()) {
        return false;
    }

    if (!SPIFFS.exists(HISTORY_PATH)) {
        return true;
    }

    return SPIFFS.remove(HISTORY_PATH);
}
