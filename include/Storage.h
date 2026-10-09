#pragma once

#include "Config.h"

// Persistência local da configuração do ESP32 em SPIFFS; o histórico é cloud.

bool loadConfig(IrrigationConfig& outConfig);
bool saveConfig(const IrrigationConfig& config);

