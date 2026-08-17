# Irrigação Comunitária

Firmware para um sistema de irrigação automática de uma horta comunitária, rodando inteiramente em um **ESP32**, **offline** — sem depender de internet, servidor remoto ou NTP. Projeto de extensão universitária: a programação está aqui; a montagem física (sensores, válvula, fiação) é responsabilidade de outra equipe.

## Como funciona

O ESP32 sobe sua própria rede WiFi (modo Access Point) e serve uma interface web local, acessível em `http://192.168.4.1`. Não há acesso à internet em nenhum momento — toda a lógica de decisão roda no firmware, e a configuração/histórico ficam salvos no armazenamento interno do ESP32 (SPIFFS).

A irrigação dispara por **horário programado + confirmação por limiar de umidade**: em cada horário ativo, o sistema só abre a válvula se o solo estiver abaixo do limiar configurado — evitando regar solo já úmido.

## Hardware

| Componente | Status |
|---|---|
| ESP32 (DevKit, chip USB-serial CH340) | ✅ em uso |
| Sensor de umidade capacitivo | 🔲 ainda não montado — mockado por leitura ADC (pino 34) |
| Válvula solenoide (via relé) | 🔲 ainda não montado — mockada pelo LED onboard (GPIO2) |
| RTC externo (DS3231) | 🔲 ainda não montado — workaround: horário definido manualmente pela interface web (`/admin`), reinicia a cada boot |

Quando o hardware real chegar, os pontos de mock ficam isolados em `src/main.cpp` (`readMoisturePercent()`, `VALVE_PIN`) — trocar a leitura/acionamento sem mexer no resto do firmware.

## Build e gravação

Pré-requisito: [PlatformIO](https://platformio.org/) (`pipx install platformio` é a forma mais simples).

```bash
pio run                                   # compila
pio run -t upload --upload-port /dev/ttyACM0   # grava no ESP32
pio device monitor -b 115200              # log serial
```

Se mudar algo em `include/Config.h` (ex: número de slots de horário), o layout salvo em SPIFFS fica incompatível com o anterior — apague o filesystem antigo antes de gravar:

```bash
pio run -t uploadfs   # precisa de uma pasta data/ (pode ser vazia) na raiz do projeto
```

## Interface web

| Rota | Método | Acesso | Função |
|---|---|---|---|
| `/status` | GET | aberto | painel visual: leitura atual, válvula, último evento, horários ativos |
| `/status.json` | GET | aberto | os mesmos dados em JSON (consumido pela página `/status`) |
| `/admin` | GET | senha | configuração: horário do sistema, horários de irrigação, limiar, irrigação manual, histórico |
| `/admin/config` | POST | senha | salva horários/limiar/duração/calibração/senha |
| `/admin/time` | POST | senha | define o relógio do sistema (workaround sem RTC) |
| `/admin/irrigate` | POST | senha | abre a válvula imediatamente por N segundos |
| `/admin/history` | GET | senha | baixa o histórico em CSV |
| `/admin/history/reset` | POST | senha | apaga o histórico |

Credenciais padrão (ver `src/main.cpp` / trocar antes de qualquer uso real): rede WiFi `Irrigacao-Comunitaria` / `irrigacao`; login do `/admin`: usuário `admin`, senha definida no primeiro salvamento em `/admin/config` (vazia até lá).

QR codes prontos pra impressão em `docs/`: `qr-wifi.png` (conecta na rede) e `qr-status.png` (abre a página de status).

## Estrutura do projeto

```
include/          contratos de dados/rotas compartilhados entre os módulos
  Config.h        IrrigationConfig (persistido)
  History.h       HistoryEntry, TriggerReason
  Routes.h        caminhos das rotas HTTP
  Storage.h       assinatura das funções de persistência (SPIFFS)
src/
  main.cpp        integra os módulos: setup/loop, mocks de sensor/válvula
  irrigation_logic.*  decisão de irrigação (horário + limiar), função pura
  storage.cpp     implementação da persistência em SPIFFS
  web_server.*    rotas HTTP, páginas HTML, autenticação
docs/             QR codes pra impressão
```

## Limitações conhecidas

- Sem RTC físico: o relógio zera a cada boot/reset; precisa ser reajustado em `/admin` (`/admin/time`).
- Senha do `/admin` guardada em texto simples (sem hash) — aceitável dado o escopo (rede local isolada, projeto de extensão).
- Sem definição ainda de quem fica com a senha do `/admin` após a entrega do equipamento pra comunidade.
