#include "LcdDisplay.h"

#include <LiquidCrystal_I2C.h>
#include <Wire.h>

namespace {

LiquidCrystal_I2C* lcd = nullptr;

bool devicePresent(uint8_t address) {
    Wire.beginTransmission(address);
    return Wire.endTransmission() == 0;
}

// O endereço depende do chip do adaptador: PCF8574 usa 0x20-0x27 (0x27 é o
// mais comum) e PCF8574A usa 0x38-0x3F. Procurar evita ter que recompilar
// quando a tela for trocada por outra.
uint8_t findLcdAddress() {
    for (uint8_t address = 0x27; address >= 0x20; address--) {
        if (devicePresent(address)) return address;
    }
    for (uint8_t address = 0x3F; address >= 0x38; address--) {
        if (devicePresent(address)) return address;
    }
    return 0;
}

void printLine(uint8_t row, const String& text) {
    lcd->setCursor(0, row);
    for (uint8_t column = 0; column < LcdDisplay::COLUMNS; column++) {
        lcd->print(column < text.length() ? text[column] : ' ');
    }
}

void show(const String& firstLine, const String& secondLine) {
    if (lcd == nullptr) return;
    printLine(0, firstLine);
    printLine(1, secondLine);
}

}  // namespace

namespace LcdDisplay {

bool begin() {
    if (lcd != nullptr) return true;

    Wire.begin(SDA_PIN, SCL_PIN);
    uint8_t address = findLcdAddress();
    if (address == 0) {
        Serial.println("[lcd] nenhuma tela I2C encontrada; seguindo sem tela");
        return false;
    }

    lcd = new LiquidCrystal_I2C(address, COLUMNS, ROWS);
    lcd->init();
    lcd->backlight();
    Serial.printf("[lcd] tela encontrada no endereco 0x%02X\n", address);
    return true;
}

void showConnecting() {
    show("Conectando ao", "Wi-Fi...");
}

// "http://" + IP não cabe em 16 colunas (um IP sozinho já pode ter 15
// caracteres), então a tela mostra só o IP; a rota "/" redireciona para o
// painel, de modo que digitar o IP no navegador basta.
void showAddress(const IPAddress& ip) {
    show("Site (Wi-Fi):", ip.toString());
}

void showOffline(const IPAddress& apIp) {
    show("Sem Wi-Fi. Rede:", apIp.toString());
}

}  // namespace LcdDisplay
