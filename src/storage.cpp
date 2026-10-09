#include <Arduino.h> // fornece size_t antes de Storage.h ser processado

#include "Storage.h"

#include <FS.h>
#include <SPIFFS.h>

// Persistência da configuração em SPIFFS. O histórico de irrigação vai para
// o Google Sheets e não é gravado na flash.
namespace {

constexpr const char* CONFIG_PATH = "/config.bin";
struct LegacyIrrigationConfig {
    ScheduleSlot schedules[MAX_SCHEDULE_SLOTS];
    uint8_t scheduleCount;
    float irrigationDurationMin;
};

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

    config.irrigationDurationMin = 1.0f;
    config.manualIrrigationDurationMin = 1.0f;
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

    if (file.size() == sizeof(LegacyIrrigationConfig)) {
        LegacyIrrigationConfig oldConfig{};
        bool migrated = file.read(reinterpret_cast<uint8_t*>(&oldConfig), sizeof(oldConfig)) == sizeof(oldConfig);
        file.close();
        if (!migrated) {
            applyDefaultConfig(outConfig);
            return false;
        }
        memcpy(outConfig.schedules, oldConfig.schedules, sizeof(outConfig.schedules));
        outConfig.scheduleCount = oldConfig.scheduleCount;
        outConfig.irrigationDurationMin = oldConfig.irrigationDurationMin;
        outConfig.manualIrrigationDurationMin = 1.0f;
        saveConfig(outConfig);
        return true;
    }

    bool ok = file.size() == sizeof(IrrigationConfig) &&
              file.read(reinterpret_cast<uint8_t*>(&outConfig), sizeof(IrrigationConfig)) == sizeof(IrrigationConfig);
    file.close();

    if (!ok) {
        applyDefaultConfig(outConfig);
        return false;
    }

    if (!(outConfig.irrigationDurationMin >= 0.0f)) {
        outConfig.irrigationDurationMin = 0.0f;
    } else if (outConfig.irrigationDurationMin > MAX_IRRIGATION_DURATION_MIN) {
        outConfig.irrigationDurationMin = MAX_IRRIGATION_DURATION_MIN;
    }
    if (!(outConfig.manualIrrigationDurationMin >= 0.0f)) {
        outConfig.manualIrrigationDurationMin = 0.0f;
    } else if (outConfig.manualIrrigationDurationMin > MAX_IRRIGATION_DURATION_MIN) {
        outConfig.manualIrrigationDurationMin = MAX_IRRIGATION_DURATION_MIN;
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

