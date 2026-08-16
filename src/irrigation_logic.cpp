#include "irrigation_logic.h"

IrrigationDecision decideIrrigation(const IrrigationConfig& config,
                                     uint8_t moisturePercent,
                                     uint8_t currentHour,
                                     uint8_t currentMinute) {
    bool scheduleMatched = false;
    for (uint8_t i = 0; i < config.scheduleCount; i++) {
        const ScheduleSlot& slot = config.schedules[i];
        if (slot.enabled && slot.hour == currentHour && slot.minute == currentMinute) {
            scheduleMatched = true;
            break;
        }
    }

    if (!scheduleMatched) {
        return {false, false, 0, TriggerReason::SCHEDULE};
    }

    bool moistureAllows = !config.useThreshold || moisturePercent < config.moistureThreshold;
    if (moistureAllows) {
        return {true, true, config.irrigationDurationSec, TriggerReason::SCHEDULE};
    }

    return {true, false, 0, TriggerReason::SKIPPED};
}
