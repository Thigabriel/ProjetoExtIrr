# Google Sheets

O ESP32 envia eventos para um Web App do Google Apps Script. A configuração da irrigação continua no SPIFFS; o histórico não é gravado na flash.

## Publicar

1. Crie uma planilha Google para o histórico.
2. Na planilha, abra **Extensões > Apps Script** e substitua o conteúdo pelo arquivo [GoogleSheets.gs](GoogleSheets.gs).
3. Em **Configurações do projeto > Propriedades do script**, crie:
   - `SPREADSHEET_ID`: o ID da planilha, entre `/d/` e `/edit` na URL.
   - `ACCESS_TOKEN`: um token aleatório escolhido por você, usando apenas letras e números.
4. Em **Implantar > Nova implantação**, selecione **App da Web**, execute como sua conta Google e permita acesso ao app da web. O token valida as solicitações do ESP32.
5. Copie a URL terminada em `/exec` e preencha `GOOGLE_SHEETS_WEB_APP_URL` e `GOOGLE_SHEETS_TOKEN` em `include/CloudConfig.h` (copiado de `include/CloudConfig.example.h`; fica fora do git).
6. Compile e grave o firmware no ESP32. O painel completo mostrará o estado do endpoint, a quantidade de eventos pendentes e um link para a planilha.

O script grava os dados na aba `REGISTROS`. A coluna `Data/Hora` é formatada como `dd/MM/yyyy HH:mm:ss` usando o fuso configurado em **Configurações do projeto > Fuso horário** no Apps Script; o código não altera essa configuração. Se ela mudar, as datas legíveis existentes são atualizadas a partir do `timestamp` Unix. `Duração` é apenas uma apresentação (por exemplo, `90 s` vira `1 min 30 s`); `Duração (s)` e `timestamp` permanecem numéricos e são as fontes técnicas. A primeira solicitação após a atualização migra as durações já registradas e mantém os valores em segundos. Na primeira solicitação, se existir a aba antiga `Irrigacoes` e ainda não existir `REGISTROS`, ela será renomeada sem apagar os dados. `deviceId` fica vazio até o firmware enviar esse campo; para adicioná-lo futuramente, inclua-o no JSON criado em `src/cloud_history.cpp`, na função `jobPayload()`.

A planilha é toda em português. Os cabeçalhos de `REGISTROS` são `Data/Hora`, `Timestamp (Unix)`, `Irrigou`, `Duração`, `Duração (s)`, `Motivo`, `ID do evento` e `ID do dispositivo`. A coluna `Irrigou` mostra `Sim` (verde) ou `Não` (amarelo), e `Motivo` aparece por extenso:

| Código enviado pelo ESP32 | Texto na planilha |
|---|---|
| `SCHEDULE` | Horário programado |
| `MANUAL` | Manual |
| `SKIPPED` | Ignorado |
| `BLOCKED_COOLDOWN` | Bloqueado (intervalo mínimo) |
| `BLOCKED_DAILY_BUDGET` | Bloqueado (limite diário) |
| `EMERGENCY_STOP` | Parada de emergência |

A tradução acontece só no Apps Script: o ESP32 continua enviando os códigos e os recebe de volta em `/cloud/history.json`, então o firmware não muda. Um motivo desconhecido é gravado em maiúsculas, sem tradução. Os registros antigos (`TRUE`/`FALSE` e códigos) são convertidos uma vez, na primeira solicitação recebida pela nova versão. As mensagens de erro devolvidas ao ESP32 também estão em português.

O Apps Script cria a aba `PAINEL` como visualização derivada de `REGISTROS`; o ESP32 continua gravando apenas em `REGISTROS`. O painel mostra contagem e duração das irrigações de hoje, última data/hora e motivo, além das contagens manuais, das automáticas (horário programado) e das tentativas bloqueadas no dia. O `ID do evento` permanece na aba técnica para identificar cada evento.

O `PAINEL` inclui gráficos de duração por evento, irrigações por dia e duração total por dia. O primeiro usa diretamente data/hora e segundos de `REGISTROS`; os gráficos diários usam uma fórmula agregada oculta, sem copiar os eventos. `REGISTROS` recebe filtro, cabeçalho destacado, primeira linha congelada, larguras e formatos numéricos/textuais adequados, alinhamento técnico e linhas alternadas.

O endpoint rejeita JSON incompleto, `eventId` ausente, timestamp fora do intervalo inteiro de 32 bits, duração não inteira/negativa/maior que 65535, booleano inválido ou motivo vazio. `deviceId` é opcional. A deduplicação é atômica e usa o par `(deviceId, eventId)`; no firmware atual, `deviceId` fica vazio e o `eventId` existente continua sendo aceito como número. Respostas inválidas mantêm `{ok:false}` para o ESP32 reconhecer a falha e seguir o retry já existente.

Depois de atualizar um Web App já implantado, publique uma nova versão em **Implantar > Gerenciar implantações > Editar > Nova versão**. A migração da aba acontece na primeira solicitação recebida por essa versão.

Para testar, publique a nova versão e provoque uma irrigação manual: confirme a nova linha em `REGISTROS`, com `Duração (s)` numérica, e confira os indicadores/gráficos em `PAINEL`. Uma repetição do mesmo POST com o mesmo `eventId` não deve criar outra linha; um POST inválido deve retornar `ok:false`. Nenhuma recompilação ou gravação do firmware é necessária para estas alterações.

Não envie o token para o repositório. O ESP32 usa TLS sem validação de certificado (`setInsecure`) nesta fase de testes; não reutilize o token em outros serviços.

Os eventos ficam em uma fila volátil de até 32 itens enquanto a rede ou o endpoint estiver indisponível. A fila é apagada ao reiniciar o ESP32. Configure e teste o endpoint antes de depender dele para registros permanentes.