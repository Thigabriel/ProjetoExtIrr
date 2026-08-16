#pragma once

#include "Config.h"
#include "History.h"

// Contrato de persistência (SPIFFS/LittleFS). Implementado em src/storage.cpp.
// Usado pelo módulo web (ler/gravar config, listar/exportar histórico) e
// pelo loop principal (ler config, gravar novas entradas de histórico).

bool loadConfig(IrrigationConfig& outConfig);
bool saveConfig(const IrrigationConfig& config);

bool appendHistoryEntry(const HistoryEntry& entry);
size_t historyCount();
bool readHistoryEntry(size_t index, HistoryEntry& outEntry);
bool clearHistory();
