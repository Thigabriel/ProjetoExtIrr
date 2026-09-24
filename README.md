# Irrigação Comunitária

Firmware para um sistema de irrigação automática de uma horta comunitária, rodando inteiramente em um **ESP32**, **offline** — sem depender de internet, servidor remoto ou NTP. Projeto de extensão universitária: a programação está aqui; a montagem física (sensores, válvula, fiação) é responsabilidade de outra equipe.

## Como funciona

O ESP32 sobe sua própria rede WiFi (modo Access Point) e serve uma interface web local, acessível em `http://192.168.4.1`. Não há acesso à internet em nenhum momento — toda a lógica de decisão roda no firmware, e a configuração/histórico ficam salvos no armazenamento interno do ESP32 (SPIFFS).

A irrigação dispara por **horário programado**. Nesta fase do projeto não há sensor de umidade instalado, então não existe confirmação por limiar — a válvula abre sempre que um horário ativo bate, respeitando as rotinas de segurança abaixo.

## Hardware

| Componente | Status |
|---|---|
| ESP32 (DevKit, chip USB-serial CH340) | ✅ em uso |
| Sensor de umidade capacitivo | ⏸ fora de escopo nesta fase — irrigação roda só por horário, sem sensor |
| Válvula solenoide (via relé) | 🔲 ainda não montado — mockada pelo LED onboard (GPIO2) |
| RTC externo (DS3231) | 🔲 ainda não montado — workaround: horário definido manualmente pela interface web (`/admin`), reinicia a cada boot |

Quando o hardware real chegar (válvula, RTC, e eventualmente o sensor), os pontos de mock ficam isolados em `src/main.cpp` (`VALVE_PIN`) — trocar o acionamento sem mexer no resto do firmware.

## Build e gravação

Pré-requisito: [PlatformIO](https://platformio.org/) (`pipx install platformio` é a forma mais simples).

```bash
pio run                                   # compila
pio run -t upload --upload-port /dev/ttyUSB0   # grava no ESP32 (confira a porta com ls /dev/tty*)
pio device monitor -b 115200              # log serial
```

Se mudar algo em `include/Config.h` (ex: número de slots de horário), o layout salvo em SPIFFS fica incompatível com o anterior — apague o filesystem antigo antes de gravar:

```bash
pio run -t uploadfs   # precisa de uma pasta data/ (pode ser vazia) na raiz do projeto
```

## Interface web

**Fase de testes: nenhuma rota exige senha** (removida de propósito, pra não atrapalhar os testes locais). Reintroduzir autenticação em `/admin/*` antes de qualquer implantação real na comunidade — ver Limitações conhecidas.

| Rota | Método | Função |
|---|---|---|
| `/status` | GET | painel visual: válvula, último evento, horários ativos |
| `/status.json` | GET | os mesmos dados em JSON (consumido pela página `/status`) |
| `/admin` | GET | configuração: horário do sistema, horários de irrigação, irrigação manual, parada de emergência, histórico |
| `/admin/config` | POST | salva horários/duração |
| `/admin/time` | POST | define o relógio do sistema (workaround sem RTC) |
| `/admin/irrigate` | POST | abre a válvula imediatamente por N segundos (sujeito a cooldown/orçamento) |
| `/admin/stop` | POST | fecha a válvula agora (parada de emergência) |
| `/admin/history` | GET | baixa o histórico em CSV |
| `/admin/history/reset` | POST | apaga o histórico |

Credenciais padrão da rede WiFi (ver `src/main.cpp` / trocar antes de qualquer uso real): `Irrigacao-Comunitaria` / `irrigacao`.

QR codes prontos pra impressão em `docs/`: `qr-wifi.png` (conecta na rede) e `qr-status.png` (abre a página de status).

## Rotinas de segurança

Sem sensor de umidade nesta fase, a irrigação roda só por horário programado — sem confirmação de que o solo já está úmido. As travas abaixo (fixas no firmware, `include/Config.h`, não editáveis pela interface web) existem pra evitar desperdício de água e dar um jeito de lidar com falhas mesmo assim:

- **Teto absoluto de duração** (`MAX_IRRIGATION_DURATION_SEC`, 300s) — nenhum acionamento, agendado ou manual, ultrapassa esse valor.
- **Cooldown entre acionamentos** (`IRRIGATION_COOLDOWN_SEC`, 10s nesta fase de testes) — bloqueia um novo acionamento enquanto a válvula ainda está aberta ou logo depois dela fechar.
- **Orçamento diário de água** (`DAILY_WATER_BUDGET_SEC`, 900s) — soma o tempo de válvula aberta no dia; ao atingir o teto, novos acionamentos são recusados até o dia seguinte.
- **Parada de emergência** (`/admin/stop`) — fecha a válvula imediatamente, independente do que estiver em andamento.
- **Aviso de falha genérica** em `/status` — se uma gravação em SPIFFS falhar (config ou histórico), a página de status sinaliza o problema e orienta contato com o professor responsável.

Tentativas bloqueadas (cooldown ou orçamento diário) ficam registradas no histórico com o motivo (`BLOCKED_COOLDOWN`, `BLOCKED_DAILY_BUDGET`), e uma parada de emergência fica registrada como `EMERGENCY_STOP` — dá pra auditar quando cada trava atuou.

## Estrutura do projeto

```
include/          contratos de dados/rotas compartilhados entre os módulos
  Config.h        IrrigationConfig (persistido)
  History.h       HistoryEntry, TriggerReason
  Routes.h        caminhos das rotas HTTP
  Storage.h       assinatura das funções de persistência (SPIFFS)
src/
  main.cpp        integra os módulos: setup/loop, mock de válvula, rotinas de segurança
  irrigation_logic.*  decisão de irrigação (horário), função pura
  storage.cpp     implementação da persistência em SPIFFS
  web_server.*    rotas HTTP, páginas HTML
docs/             QR codes pra impressão
```

## Limitações conhecidas

- Sem RTC físico: o relógio zera a cada boot/reset; precisa ser reajustado em `/admin` (`/admin/time`).
- **Sem autenticação em nenhuma rota** (removida de propósito na fase de testes) — qualquer um na rede WiFi do ESP32 consegue configurar/irrigar/apagar histórico. Precisa ser reintroduzida antes de entregar o equipamento pra comunidade.
- Sem sensor de umidade: a irrigação não tem confirmação de que o solo já está úmido, só o horário programado — ver Rotinas de segurança acima para as salvaguardas usadas enquanto isso.
