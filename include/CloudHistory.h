#pragma once

#include <Arduino.h>

#include "History.h"

namespace CloudHistory {
    void begin();
    bool enqueue(const HistoryEntry& entry);
    bool clear();
    String historyJson();
    bool isConfigured();
    bool isConnected();
    size_t pendingCount();
}