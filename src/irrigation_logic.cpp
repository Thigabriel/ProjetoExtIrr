#include "irrigation_logic.h"

IrrigationDecision decideIrrigation(const IrrigationConfig& config,
                                     uint8_t currentHour,
                                     uint8_t currentMinute) {
    for (uint8_t i = 0; i < config.scheduleCount; i++) {
        const ScheduleSlot& slot = config.schedules[i];
        if (slot.enabled && slot.hour == currentHour && slot.minute == currentMinute) {
            return {true, config.irrigationDurationSec};
        }
    }
    return {false, 0};
}
