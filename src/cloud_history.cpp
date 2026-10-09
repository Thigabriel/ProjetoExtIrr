#include "CloudHistory.h"

#include <Arduino.h>
#include <HTTPClient.h>
#include <WiFi.h>
#include <WiFiClientSecure.h>
#include <freertos/FreeRTOS.h>
#include <freertos/queue.h>
#include <freertos/semphr.h>
#include <freertos/task.h>

#include "CloudConfig.h"

namespace {

constexpr uint8_t JOB_APPEND = 0;
constexpr uint8_t JOB_CLEAR = 1;
constexpr UBaseType_t HISTORY_QUEUE_LENGTH = 32;
constexpr uint32_t HISTORY_REFRESH_MS = 30000;

struct CloudJob {
    uint8_t type;
    HistoryEntry entry;
    uint32_t eventId;
};

QueueHandle_t jobQueue = nullptr;
SemaphoreHandle_t cacheMutex = nullptr;
String cachedHistory = "{\"ok\":false,\"error\":\"not_initialized\",\"total\":0,\"history\":[]}";
volatile bool connected = false;

bool configured() {
    return CloudConfig::GOOGLE_SHEETS_WEB_APP_URL[0] != '\0' &&
           CloudConfig::GOOGLE_SHEETS_TOKEN[0] != '\0';
}

String historyUrl() {
    return String(CloudConfig::GOOGLE_SHEETS_WEB_APP_URL) + "?action=history&token=" +
           CloudConfig::GOOGLE_SHEETS_TOKEN;
}

bool requestCloud(const String& url, const String* payload, String& responseBody) {
    WiFiClientSecure client;
    client.setInsecure();

    HTTPClient http;
    http.setTimeout(7000);
    http.setFollowRedirects(HTTPC_FORCE_FOLLOW_REDIRECTS);
    if (!http.begin(client, url)) {
        return false;
    }

    int status;
    if (payload != nullptr) {
        http.addHeader("Content-Type", "application/json");
        status = http.POST(*payload);
    } else {
        status = http.GET();
    }
    if (status <= 0) {
        http.end();
        return false;
    }

    responseBody = http.getString();
    http.end();
    return status == HTTP_CODE_OK && responseBody.indexOf("\"ok\":true") >= 0;
}

String reasonName(TriggerReason reason) {
    switch (reason) {
        case TriggerReason::SCHEDULE: return "SCHEDULE";
        case TriggerReason::MANUAL: return "MANUAL";
        case TriggerReason::SKIPPED: return "SKIPPED";
        case TriggerReason::BLOCKED_COOLDOWN: return "BLOCKED_COOLDOWN";
        case TriggerReason::BLOCKED_DAILY_BUDGET: return "BLOCKED_DAILY_BUDGET";
        case TriggerReason::EMERGENCY_STOP: return "EMERGENCY_STOP";
    }
    return "UNKNOWN";
}

String jobPayload(const CloudJob& job) {
    String payload = "{\"token\":\"" + String(CloudConfig::GOOGLE_SHEETS_TOKEN) + "\",\"action\":";
    if (job.type == JOB_CLEAR) {
        return payload + "\"clear\"}";
    }
    payload += "\"append\",\"timestamp\":" + String(job.entry.timestamp) +
               ",\"irrigated\":" + (job.entry.irrigated ? "true" : "false") +
               ",\"durationSec\":" + String(job.entry.durationSec) +
               ",\"reason\":\"" + reasonName(job.entry.reason) +
               "\",\"eventId\":" + String(job.eventId) + "}";
    return payload;
}

void setCachedHistory(const String& value) {
    if (cacheMutex == nullptr) return;
    xSemaphoreTake(cacheMutex, portMAX_DELAY);
    cachedHistory = value;
    xSemaphoreGive(cacheMutex);
}

bool refreshHistory() {
    String response;
    bool ok = requestCloud(historyUrl(), nullptr, response);
    connected = ok;
    if (ok) setCachedHistory(response);
    return ok;
}

void cloudTask(void*) {
    uint32_t lastRefresh = 0;
    bool refreshPending = true; // busca o histórico assim que houver conexão e logo após cada envio
    for (;;) {
        if (!configured() || WiFi.status() != WL_CONNECTED) {
            connected = false;
            vTaskDelay(pdMS_TO_TICKS(5000));
            continue;
        }

        CloudJob job{};
        if (xQueueReceive(jobQueue, &job, pdMS_TO_TICKS(1000)) == pdTRUE) {
            String payload = jobPayload(job);
            String response;
            if (!requestCloud(String(CloudConfig::GOOGLE_SHEETS_WEB_APP_URL), &payload, response)) {
                connected = false;
                // Volta para a frente da fila, para manter a ordem dos eventos.
                xQueueSendToFront(jobQueue, &job, pdMS_TO_TICKS(1000));
                vTaskDelay(pdMS_TO_TICKS(5000));
                continue;
            }
            connected = true;
            // Com mais eventos na fila, envia todos antes de reler a planilha.
            refreshPending = uxQueueMessagesWaiting(jobQueue) == 0;
        }

        uint32_t now = millis();
        if (refreshPending || now - lastRefresh >= HISTORY_REFRESH_MS) {
            refreshHistory();
            refreshPending = false;
            lastRefresh = now;
        }
    }
}

}  // namespace

namespace CloudHistory {

void begin() {
    if (jobQueue != nullptr) return;
    jobQueue = xQueueCreate(HISTORY_QUEUE_LENGTH, sizeof(CloudJob));
    cacheMutex = xSemaphoreCreateMutex();
    if (jobQueue == nullptr || cacheMutex == nullptr) return;
    if (!configured()) {
        setCachedHistory("{\"ok\":false,\"error\":\"endpoint_not_configured\",\"total\":0,\"spreadsheetUrl\":\"\",\"history\":[]}");
    }
    xTaskCreatePinnedToCore(cloudTask, "sheets_logger", 8192, nullptr, 1, nullptr, 0);
}

bool enqueue(const HistoryEntry& entry) {
    if (jobQueue == nullptr) return false;
    CloudJob job{};
    job.type = JOB_APPEND;
    job.entry = entry;
    job.eventId = micros();
    return xQueueSend(jobQueue, &job, 0) == pdTRUE;
}

bool clear() {
    if (jobQueue == nullptr || !configured()) return false;
    CloudJob job{};
    job.type = JOB_CLEAR;
    return xQueueSend(jobQueue, &job, 0) == pdTRUE;
}

String historyJson() {
    if (cacheMutex == nullptr) {
        return "{\"ok\":false,\"error\":\"not_initialized\",\"total\":0,\"history\":[]}";
    }
    xSemaphoreTake(cacheMutex, portMAX_DELAY);
    String result = cachedHistory;
    xSemaphoreGive(cacheMutex);
    return result;
}

bool isConfigured() {
    return configured();
}

bool isConnected() {
    return connected;
}

size_t pendingCount() {
    return jobQueue == nullptr ? 0 : static_cast<size_t>(uxQueueMessagesWaiting(jobQueue));
}

}  // namespace CloudHistory