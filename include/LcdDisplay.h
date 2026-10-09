#pragma once

#include <Arduino.h>

// Tela LCD de caracteres (HD44780 com adaptador I2C PCF8574) que mostra o
// endereço do site. Temporária: quando houver uma tela gráfica, a ideia é
// trocar o texto por um QR code com o mesmo endereço.
//
// Se nenhuma tela for encontrada no barramento I2C, todas as funções viram
// no-op e o restante do firmware funciona normalmente.
namespace LcdDisplay {
    constexpr uint8_t COLUMNS = 16;
    constexpr uint8_t ROWS = 2;
    constexpr uint8_t SDA_PIN = 21;
    constexpr uint8_t SCL_PIN = 22;

    bool begin();
    void showConnecting();
    void showAddress(const IPAddress& ip);    // conectado ao Wi-Fi do local
    void showOffline(const IPAddress& apIp);  // sem Wi-Fi: resta a rede do próprio ESP32
}
