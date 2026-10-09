#pragma once

// Modelo de include/CloudConfig.h, que guarda as credenciais e fica fora do
// git. Copie este arquivo para include/CloudConfig.h e preencha os valores.

namespace CloudConfig {
    // Preencha com a URL /exec e o mesmo token configurado nas propriedades do Apps Script.
    constexpr const char* GOOGLE_SHEETS_WEB_APP_URL = "";
    constexpr const char* GOOGLE_SHEETS_TOKEN = "";
}

namespace WifiConfig {
    // Wi-Fi do local, usado para NTP e para o envio ao Google Sheets.
    constexpr const char* SSID = "";
    constexpr const char* PASSWORD = "";
}
