# Irrigação Comunitária

Firmware para um sistema de irrigação automática de uma horta comunitária, rodando em um **ESP32**. O equipamento mantém um ponto de acesso local e também pode se conectar ao Wi-Fi do local para sincronizar o relógio via NTP e servir um painel completo na rede. Projeto de extensão universitária: a programação está aqui; a montagem física (sensores, válvula, fiação) é responsabilidade de outra equipe.

## Como funciona

O ESP32 mantém a rede `Irrigacao-Comunitaria` para a interface simplificada em `http://192.168.4.1` e, em paralelo, conecta-se ao Wi-Fi do local por DHCP para obter a hora por NTP. O IP atribuído pelo roteador ou hotspot aparece no monitor serial; o painel completo fica disponível em `http://<IP-do-ESP32>/remote`. A configuração fica no SPIFFS; os registros de irrigação são enviados ao Google Sheets.

O endereço `/remote` é acessível por dispositivos na mesma rede Wi-Fi do local. Acesso de fora dessa rede exige uma solução de rede adicional, como VPN; não exponha diretamente as portas do ESP32 à internet.

A irrigação dispara por **horário programado**. Nesta fase do projeto não há sensor de umidade instalado, então não existe confirmação por limiar — a válvula abre sempre que um horário ativo bate, respeitando as rotinas de segurança abaixo.

## Hardware

| Componente | Status |
|---|---|
| ESP32 (DevKit, chip USB-serial CH340) | ✅ em uso |
| Sensor de umidade capacitivo | ⏸ fora de escopo nesta fase — irrigação roda só por horário, sem sensor |
| Válvula solenoide (via relé) | 🔲 ainda não montado — mockada pelo LED onboard (GPIO2) |
| RTC externo (DS3231) | 🔲 ainda não montado — horário obtido por NTP via Wi-Fi |

Quando o hardware real chegar (válvula, RTC, e eventualmente o sensor), os pontos de mock ficam isolados em `src/main.cpp` (`VALVE_PIN`) — trocar o acionamento sem mexer no resto do firmware.

## Build e gravação

Pré-requisito: [PlatformIO](https://platformio.org/) (`pipx install platformio` é a forma mais simples).

```bash
pio run                                   # compila
pio run -t upload --upload-port /dev/ttyUSB0   # grava no ESP32 (confira a porta com ls /dev/tty*)
pio device monitor -b 115200              # log serial
```

Se mudar algo em `include/Config.h` (ex: número de slots de horário ou unidade da duração), o layout salvo em SPIFFS fica incompatível com o anterior — apague o filesystem antigo antes de gravar:

```bash
pio run -t uploadfs   # precisa de uma pasta data/ (pode ser vazia) na raiz do projeto
```

## Interface web

**Fase de testes: nenhuma rota exige senha** (removida de propósito, pra não atrapalhar os testes locais). Reintroduzir autenticação em `/admin/*` antes de qualquer implantação real na comunidade — ver Limitações conhecidas.

| Rota | Método | Função |
|---|---|---|
| `/status` | GET | painel local: data e hora, irrigação manual, parada e última irrigação |
| `/status.json` | GET | os mesmos dados em JSON (consumido pela página `/status`) |
| `/cloud/history.json` | GET | cache dos últimos registros recebidos do Google Sheets |
| `/remote` | GET | painel completo: status, histórico do Sheets e configurações |
| `/admin` | GET | redireciona para `/remote` (compatibilidade) |
| `/admin/config` | POST | salva horários e durações; a duração manual é editada apenas no painel completo |
| `/admin/irrigate` | POST | abre a válvula imediatamente pela duração configurada (sujeito a cooldown/orçamento) |
| `/admin/stop` | POST | fecha a válvula agora (parada de emergência) |

O SSID e a senha do Wi-Fi local, assim como a URL e o token do Apps Script, ficam em `include/CloudConfig.h`, que não é versionado: copie `include/CloudConfig.example.h` para `include/CloudConfig.h` e preencha antes de compilar. Siga [docs/GOOGLE_SHEETS_SETUP.md](docs/GOOGLE_SHEETS_SETUP.md) para publicar o endpoint. Credenciais padrão do AP do ESP32: `Irrigacao-Comunitaria` / `irrigacao`.

QR codes prontos pra impressão em `docs/`: `qr-wifi.png` (conecta na rede) e `qr-status.png` (abre a página de status).

## Rotinas de segurança

Sem sensor de umidade nesta fase, a irrigação roda só por horário programado — sem confirmação de que o solo já está úmido. As travas abaixo (fixas no firmware, `include/Config.h`, não editáveis pela interface web) existem pra evitar desperdício de água e dar um jeito de lidar com falhas mesmo assim:

- **Teto absoluto de duração** (`MAX_IRRIGATION_DURATION_MIN`, 5 minutos) — nenhum acionamento, agendado ou manual, ultrapassa esse valor. A interface aceita frações, como `0,167` minuto (aproximadamente 10 segundos).
- **Cooldown entre acionamentos** (`IRRIGATION_COOLDOWN_SEC`, 10s nesta fase de testes) — bloqueia um novo acionamento enquanto a válvula ainda está aberta ou logo depois dela fechar.
- **Orçamento diário de água** (`DAILY_WATER_BUDGET_SEC`, 900s) — soma o tempo de válvula aberta no dia; ao atingir o teto, novos acionamentos são recusados até o dia seguinte.
- **Parada de emergência** (`/admin/stop`) — fecha a válvula imediatamente, independente do que estiver em andamento.
- **Fila cloud limitada a 32 eventos em RAM** — se a rede/endpoint ficar indisponível, os eventos aguardam reenvio; a fila não sobrevive a uma reinicialização.

Tentativas bloqueadas (cooldown ou orçamento diário) ficam registradas no histórico com o motivo (`BLOCKED_COOLDOWN`, `BLOCKED_DAILY_BUDGET`), e uma parada de emergência fica registrada como `EMERGENCY_STOP` — dá pra auditar quando cada trava atuou.

## Estrutura do projeto

```
include/          contratos de dados/rotas compartilhados entre os módulos
  Config.h        IrrigationConfig (persistido)
  History.h       HistoryEntry, TriggerReason
  Routes.h        caminhos das rotas HTTP
  Storage.h       persistência da configuração (SPIFFS)
  CloudConfig.example.h  modelo das credenciais (Wi-Fi, URL e token do Apps Script); copiar para CloudConfig.h
  CloudHistory.h  fila/cache do histórico cloud
src/
  main.cpp        integra os módulos: setup/loop, mock de válvula, rotinas de segurança
  irrigation_logic.*  decisão de irrigação (horário), função pura
  storage.cpp     implementação da persistência de configuração em SPIFFS
  cloud_history.cpp envio assíncrono e cache do Google Sheets
  web_server.*    rotas HTTP, páginas HTML
docs/             QR codes pra impressão
```

## Limitações conhecidas

- Sem RTC físico: data e hora dependem de conexão Wi-Fi e sincronização NTP; o painel informa quando a sincronização ainda não ocorreu.
- **Sem autenticação nas rotas do ESP32** (fase de testes) — qualquer pessoa nas redes do equipamento consegue configurar ou irrigar. Proteja o Apps Script com o token descrito no guia e reintroduza autenticação antes da implantação.
- Sem sensor de umidade: a irrigação não tem confirmação de que o solo já está úmido, só o horário programado — ver Rotinas de segurança acima para as salvaguardas usadas enquanto isso.
