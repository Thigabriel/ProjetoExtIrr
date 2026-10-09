// Web App do Google Apps Script que recebe os eventos de irrigação do ESP32
// e os grava na aba REGISTROS, mantendo a aba PAINEL como resumo.
//
// A planilha é toda em português (cabeçalhos, "Sim"/"Não", motivos por
// extenso). O ESP32 continua enviando e recebendo os códigos originais
// (SCHEDULE, MANUAL, ...): a tradução acontece só aqui, na gravação e na
// leitura, então o firmware não precisa mudar.

const RECORDS_SHEET = "REGISTROS";
const DASHBOARD_SHEET = "PAINEL";
const DASHBOARD_TITLE = "SISTEMA DE IRRIGAÇÃO";
const COLUMN_COUNT = 8;
const HISTORY_LIMIT = 25;
const LOCK_TIMEOUT_MS = 10000;

// Colunas da aba REGISTROS (1 = A).
const COL = {
  DATE_TIME: 1,
  TIMESTAMP: 2,
  IRRIGATED: 3,
  DURATION_TEXT: 4,
  DURATION_SEC: 5,
  REASON: 6,
  EVENT_ID: 7,
  DEVICE_ID: 8
};

const YES = "Sim";
const NO = "Não";

// Código enviado pelo ESP32 -> texto mostrado na planilha.
const REASON_LABELS = {
  SCHEDULE: "Horário programado",
  MANUAL: "Manual",
  SKIPPED: "Ignorado",
  BLOCKED_COOLDOWN: "Bloqueado (intervalo mínimo)",
  BLOCKED_DAILY_BUDGET: "Bloqueado (limite diário)",
  EMERGENCY_STOP: "Parada de emergência"
};

const COLOR = {
  GREEN_DARK: "#245b43",
  GREEN_LIGHT: "#e8f1eb",
  BAND: "#f3f6f4",
  WHITE: "#ffffff",
  MUTED: "#888888",
  YES_BACKGROUND: "#d9ead3",
  YES_TEXT: "#1e5a3a",
  NO_BACKGROUND: "#fff2cc",
  NO_TEXT: "#7f6000"
};

// Versões das rotinas que rodam uma única vez por planilha. Aumentar o número
// faz a rotina rodar de novo na próxima solicitação recebida.
const RECORDS_LAYOUT_VERSION = "2";
const RECORDS_FORMAT_VERSION = "2";
const DASHBOARD_SETUP_VERSION = "3";
const DASHBOARD_CHARTS_VERSION = "1";

// ---------------------------------------------------------------------------
// Entradas do Web App
// ---------------------------------------------------------------------------

function doGet(e) {
  try {
    checkToken_(e && e.parameter ? e.parameter.token : null);
    const sheet = getSheet_();
    const total = Math.max(0, sheet.getLastRow() - 1);
    const count = Math.min(HISTORY_LIMIT, total);
    const history = [];

    if (count > 0) {
      const rows = sheet.getRange(total - count + 2, 1, count, COLUMN_COUNT).getValues();
      for (let i = rows.length - 1; i >= 0; i--) {
        history.push({
          timestamp: Number(rows[i][COL.TIMESTAMP - 1]),
          irrigated: isYes_(rows[i][COL.IRRIGATED - 1]),
          durationSec: Number(rows[i][COL.DURATION_SEC - 1]),
          reason: reasonCode_(rows[i][COL.REASON - 1]),
          eventId: String(rows[i][COL.EVENT_ID - 1]),
          deviceId: String(rows[i][COL.DEVICE_ID - 1] || "")
        });
      }
    }

    return json_({
      ok: true,
      total: total,
      spreadsheetUrl: getSpreadsheet_().getUrl(),
      timeZone: Session.getScriptTimeZone(),
      history: history
    });
  } catch (error) {
    return json_({ ok: false, error: errorMessage_(error), total: 0, history: [] });
  }
}

function doPost(e) {
  try {
    const data = parseRequest_(e);
    checkToken_(data.token);

    if (data.action === "clear") {
      clearRecords_(getSheet_());
      return json_({ ok: true });
    }
    if (data.action !== "append") throw new Error("Ação inválida");

    const event = validateEvent_(data);
    const sheet = getSheet_();
    const lock = LockService.getScriptLock();
    lock.waitLock(LOCK_TIMEOUT_MS);
    try {
      if (hasDuplicateEvent_(sheet, event.eventId, event.deviceId)) {
        return json_({ ok: true, duplicate: true });
      }
      sheet.appendRow(formatRecord_(event, Session.getScriptTimeZone()));
    } finally {
      lock.releaseLock();
    }
    return json_({ ok: true });
  } catch (error) {
    return json_({ ok: false, error: errorMessage_(error) });
  }
}

// ---------------------------------------------------------------------------
// Validação da solicitação
// ---------------------------------------------------------------------------

function parseRequest_(e) {
  if (!e || !e.postData || typeof e.postData.contents !== "string") {
    throw new Error("Corpo JSON ausente");
  }
  let data;
  try {
    data = JSON.parse(e.postData.contents);
  } catch (error) {
    throw new Error("JSON inválido");
  }
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("O corpo JSON deve ser um objeto");
  }
  return data;
}

function validateEvent_(data) {
  const reason = typeof data.reason === "string" ? reasonCode_(data.reason) : "";
  if (!reason || reason.length > 80) throw new Error("Campo inválido: reason");

  return {
    timestamp: parseIntegerField_(data.timestamp, "timestamp", 0, 4294967295),
    durationSec: parseIntegerField_(data.durationSec, "durationSec", 0, 65535),
    irrigated: parseBooleanField_(data.irrigated),
    reason: reason,
    eventId: normalizeIdentifier_(data.eventId, "eventId", false),
    deviceId: normalizeIdentifier_(data.deviceId, "deviceId", true)
  };
}

function parseIntegerField_(value, name, minimum, maximum) {
  const isNumber = typeof value === "number";
  const isFilledText = typeof value === "string" && value.trim() !== "";
  const parsed = isNumber || isFilledText ? Number(value) : NaN;
  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error("Campo inválido: " + name);
  }
  return parsed;
}

function parseBooleanField_(value) {
  const text = typeof value === "string" ? value.trim().toLowerCase() : null;
  if (value === true || value === 1 || text === "true") return true;
  if (value === false || value === 0 || text === "false") return false;
  throw new Error("Campo inválido: irrigated");
}

function normalizeIdentifier_(value, name, optional) {
  if (value == null && optional) return "";
  if (typeof value !== "string" && typeof value !== "number") {
    throw new Error("Campo inválido: " + name);
  }
  const identifier = String(value).trim();
  if ((!identifier && !optional) || identifier.length > 128) {
    throw new Error("Campo inválido: " + name);
  }
  return identifier;
}

// ---------------------------------------------------------------------------
// Tradução entre os códigos do ESP32 e o texto da planilha
// ---------------------------------------------------------------------------

function normalizeReason_(reason) {
  return String(reason == null ? "" : reason).trim().toUpperCase();
}

// Aceita tanto o código quanto o texto em português e devolve o código.
// Motivos desconhecidos passam adiante em maiúsculas, sem tradução.
function reasonCode_(value) {
  const normalized = normalizeReason_(value);
  if (REASON_LABELS[normalized]) return normalized;
  const codes = Object.keys(REASON_LABELS);
  for (let i = 0; i < codes.length; i++) {
    if (REASON_LABELS[codes[i]].toUpperCase() === normalized) return codes[i];
  }
  return normalized;
}

function reasonLabel_(value) {
  const code = reasonCode_(value);
  return REASON_LABELS[code] || code;
}

function isYes_(value) {
  if (value === true) return true;
  const text = String(value == null ? "" : value).trim().toUpperCase();
  return text === "SIM" || text === "TRUE";
}

function yesNo_(value) {
  return isYes_(value) ? YES : NO;
}

// ---------------------------------------------------------------------------
// Aba REGISTROS
// ---------------------------------------------------------------------------

function headerRow_() {
  return ["Data/Hora", "Timestamp (Unix)", "Irrigou", "Duração", "Duração (s)", "Motivo",
    "ID do evento", "ID do dispositivo"];
}

function formatRecord_(event, timeZone) {
  return [
    formatDateTime_(new Date(event.timestamp * 1000), timeZone),
    event.timestamp,
    yesNo_(event.irrigated),
    formatDuration_(event.durationSec),
    event.durationSec,
    reasonLabel_(event.reason),
    event.eventId,
    event.deviceId
  ];
}

function hasDuplicateEvent_(sheet, eventId, deviceId) {
  const rowCount = sheet.getLastRow() - 1;
  if (rowCount <= 0) return false;

  const matches = sheet.getRange(2, COL.EVENT_ID, rowCount, 1).createTextFinder(eventId)
    .matchCase(true).matchEntireCell(true).findAll();
  for (let i = 0; i < matches.length; i++) {
    const existingDeviceId = String(sheet.getRange(matches[i].getRow(), COL.DEVICE_ID).getValue() || "");
    if (existingDeviceId === deviceId) return true;
  }
  return false;
}

function clearRecords_(sheet) {
  const lock = LockService.getScriptLock();
  lock.waitLock(LOCK_TIMEOUT_MS);
  try {
    sheet.clearContents();
    sheet.appendRow(headerRow_());
  } finally {
    lock.releaseLock();
  }
}

function getSheet_() {
  const spreadsheet = getSpreadsheet_();
  const timeZone = Session.getScriptTimeZone();
  let sheet = spreadsheet.getSheetByName(RECORDS_SHEET);
  if (!sheet) {
    sheet = spreadsheet.getSheetByName("Irrigacoes");
    if (sheet) {
      sheet.setName(RECORDS_SHEET);
    } else {
      sheet = spreadsheet.insertSheet(RECORDS_SHEET);
    }
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headerRow_());
  } else {
    const header = sheet.getRange(1, 1, 1, COLUMN_COUNT).getValues()[0];
    if (header[COL.DURATION_TEXT - 1] !== "Duração" || header[COL.DURATION_SEC - 1] !== "Duração (s)") {
      addDurationTextColumn_(sheet);
    }
    if (header.join("\n") !== headerRow_().join("\n")) {
      sheet.getRange(1, 1, 1, COLUMN_COUNT).setValues([headerRow_()]);
    }
  }

  syncDateTimeColumn_(sheet, spreadsheet, timeZone);
  translateRecords_(sheet, spreadsheet);
  formatRecordsSheet_(sheet, spreadsheet);
  ensureDashboard_(spreadsheet, timeZone);
  return sheet;
}

// Migração do layout mais antigo, de 7 colunas, que não tinha a duração por
// extenso ("1 min 30 s") ao lado da duração em segundos.
function addDurationTextColumn_(sheet) {
  const rowCount = sheet.getLastRow() - 1;
  if (rowCount <= 0) return;

  const migratedRows = sheet.getRange(2, 1, rowCount, COLUMN_COUNT - 1).getValues().map(function(row) {
    const durationSec = Number(row[3]);
    return [row[0], row[1], row[2], formatDuration_(durationSec), durationSec, row[4], row[5],
      String(row[6] || "")];
  });
  sheet.getRange(2, 1, rowCount, COLUMN_COUNT).setValues(migratedRows);
}

// Converte uma única vez os registros antigos para português: TRUE/FALSE vira
// Sim/Não e os códigos de motivo viram texto por extenso.
function translateRecords_(sheet, spreadsheet) {
  const propertyKey = "REGISTROS_LAYOUT_VERSION_" + spreadsheet.getId();
  if (getProperty_(propertyKey) === RECORDS_LAYOUT_VERSION) return;

  const lock = LockService.getScriptLock();
  lock.waitLock(LOCK_TIMEOUT_MS);
  try {
    if (getFreshProperty_(propertyKey) === RECORDS_LAYOUT_VERSION) return;

    const rowCount = sheet.getLastRow() - 1;
    if (rowCount > 0) {
      const irrigatedRange = sheet.getRange(2, COL.IRRIGATED, rowCount, 1);
      irrigatedRange.setValues(irrigatedRange.getValues().map(function(row) {
        return [row[0] === "" ? "" : yesNo_(row[0])];
      }));

      const reasonRange = sheet.getRange(2, COL.REASON, rowCount, 1);
      reasonRange.setValues(reasonRange.getValues().map(function(row) {
        return [reasonLabel_(row[0])];
      }));
    }
    setProperty_(propertyKey, RECORDS_LAYOUT_VERSION);
  } finally {
    lock.releaseLock();
  }
}

// Reescreve a coluna Data/Hora quando o fuso horário do projeto muda, para
// que as datas legíveis continuem batendo com o timestamp.
function syncDateTimeColumn_(sheet, spreadsheet, timeZone) {
  const propertyKey = "REGISTROS_TIME_ZONE_" + spreadsheet.getId();
  if (getProperty_(propertyKey) === timeZone) return;

  const lock = LockService.getScriptLock();
  lock.waitLock(LOCK_TIMEOUT_MS);
  try {
    if (getFreshProperty_(propertyKey) === timeZone) return;

    const rowCount = sheet.getLastRow() - 1;
    if (rowCount > 0) {
      const rows = sheet.getRange(2, 1, rowCount, 2).getValues();
      const dateTimes = rows.map(function(row) {
        const timestamp = row[1];
        if (timestamp !== "" && isFinite(Number(timestamp))) {
          return [formatDateTime_(new Date(Number(timestamp) * 1000), timeZone)];
        }
        if (row[0] instanceof Date) return [formatDateTime_(row[0], timeZone)];
        return [row[0]];
      });
      sheet.getRange(2, COL.DATE_TIME, rowCount, 1).setValues(dateTimes);
    }
    setProperty_(propertyKey, timeZone);
  } finally {
    lock.releaseLock();
  }
}

function formatRecordsSheet_(sheet, spreadsheet) {
  const propertyKey = "REGISTROS_FORMAT_VERSION_" + spreadsheet.getId();
  if (getProperty_(propertyKey) === RECORDS_FORMAT_VERSION) return;

  const maxRows = sheet.getMaxRows();
  const dataRows = Math.max(1, maxRows - 1);
  const tableRange = sheet.getRange(1, 1, maxRows, COLUMN_COUNT);
  const column = function(index) { return sheet.getRange(2, index, dataRows, 1); };

  if (!sheet.getFilter()) tableRange.createFilter();
  if (sheet.getBandings().length === 0) {
    const banding = tableRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false);
    banding.setHeaderRowColor(COLOR.GREEN_DARK);
    banding.setFirstRowColor(COLOR.WHITE);
    banding.setSecondRowColor(COLOR.BAND);
  }

  sheet.setFrozenRows(1);
  sheet.setTabColor(COLOR.GREEN_DARK);
  sheet.getRange(1, 1, 1, COLUMN_COUNT).setBackground(COLOR.GREEN_DARK).setFontColor(COLOR.WHITE)
    .setFontWeight("bold").setHorizontalAlignment("center").setVerticalAlignment("middle").setWrap(true);
  sheet.setRowHeight(1, 36);

  // Data/Hora fica como texto: o PAINEL filtra o dia pelo começo do texto.
  column(COL.DATE_TIME).setNumberFormat("@");
  column(COL.TIMESTAMP).setNumberFormat("0");
  column(COL.DURATION_SEC).setNumberFormat("0");
  column(COL.EVENT_ID).setNumberFormat("@");
  column(COL.DEVICE_ID).setNumberFormat("@");

  [COL.TIMESTAMP, COL.IRRIGATED, COL.DURATION_TEXT, COL.DURATION_SEC, COL.EVENT_ID, COL.DEVICE_ID]
    .forEach(function(index) { column(index).setHorizontalAlignment("center"); });

  // Colunas técnicas (usadas pelo ESP32, não pela leitura humana) em cinza.
  [COL.TIMESTAMP, COL.EVENT_ID, COL.DEVICE_ID]
    .forEach(function(index) { column(index).setFontColor(COLOR.MUTED); });

  const irrigatedColumn = column(COL.IRRIGATED);
  irrigatedColumn.setFontWeight("bold");
  sheet.setConditionalFormatRules([
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(YES)
      .setBackground(COLOR.YES_BACKGROUND).setFontColor(COLOR.YES_TEXT)
      .setRanges([irrigatedColumn]).build(),
    SpreadsheetApp.newConditionalFormatRule().whenTextEqualTo(NO)
      .setBackground(COLOR.NO_BACKGROUND).setFontColor(COLOR.NO_TEXT)
      .setRanges([irrigatedColumn]).build()
  ]);

  const widths = [155, 135, 90, 125, 105, 240, 150, 150];
  widths.forEach(function(width, index) { sheet.setColumnWidth(index + 1, width); });

  setProperty_(propertyKey, RECORDS_FORMAT_VERSION);
}

// ---------------------------------------------------------------------------
// Aba PAINEL
// ---------------------------------------------------------------------------

function ensureDashboard_(spreadsheet, timeZone) {
  let panel = spreadsheet.getSheetByName(DASHBOARD_SHEET);
  if (!panel) panel = spreadsheet.insertSheet(DASHBOARD_SHEET);

  const propertyKey = "PAINEL_SETUP_VERSION_" + spreadsheet.getId();
  if (getProperty_(propertyKey) !== DASHBOARD_SETUP_VERSION ||
      panel.getRange("A1").getValue() !== DASHBOARD_TITLE) {
    setUpDashboard_(panel);
    setProperty_(propertyKey, DASHBOARD_SETUP_VERSION);
  }

  // Z1 guarda o dia de hoje como texto; as fórmulas "hoje" filtram por ele.
  const today = Utilities.formatDate(new Date(), timeZone, "dd/MM/yyyy");
  if (panel.getRange("Z1").getDisplayValue() !== today) panel.getRange("Z1").setValue(today);
  ensureDashboardCharts_(spreadsheet, panel);
}

function setUpDashboard_(panel) {
  const records = "'" + RECORDS_SHEET + "'!";
  const dateTime = records + "A2:A";
  const timestamp = records + "B2:B";
  const irrigated = records + "C2:C";
  const durationSec = records + "E2:E";
  const reason = records + "F2:F";
  const today = dateTime + ',$Z$1&"*"';
  const irrigatedToday = today + "," + irrigated + ',"' + YES + '"';
  const lastIrrigationRow = "MATCH(MAXIFS(" + timestamp + "," + irrigated + ',"' + YES + '"),' + timestamp + ",0)";

  panel.getRange("A1").setValue(DASHBOARD_TITLE);
  panel.getRange("A3:A9").setValues([
    ["Irrigações hoje"],
    ["Tempo total hoje"],
    ["Última irrigação (data/hora)"],
    ["Motivo da última irrigação"],
    ["Irrigações manuais hoje"],
    ["Irrigações automáticas hoje"],
    ["Tentativas bloqueadas hoje"]
  ]);

  panel.getRange("Z1").setNumberFormat("@");
  panel.getRange("Z2").setFormula("=SUMIFS(" + durationSec + "," + irrigatedToday + ")");
  panel.getRange("B3").setFormula("=COUNTIFS(" + irrigatedToday + ")");
  panel.getRange("B4").setFormula(
    '=IF($Z$2=0,"0 s",IF(INT($Z$2/60)>0,INT($Z$2/60)&" min","")&' +
    'IF(MOD($Z$2,60)>0,IF(INT($Z$2/60)>0," ","")&MOD($Z$2,60)&" s",""))'
  );
  panel.getRange("B5").setFormula(
    "=IFERROR(INDEX(" + dateTime + "," + lastIrrigationRow + '),"Sem registros")'
  );
  panel.getRange("B6").setFormula(
    "=IFERROR(INDEX(" + reason + "," + lastIrrigationRow + '),"-")'
  );
  panel.getRange("B7").setFormula(
    "=COUNTIFS(" + irrigatedToday + "," + reason + ',"' + REASON_LABELS.MANUAL + '")'
  );
  panel.getRange("B8").setFormula(
    "=COUNTIFS(" + irrigatedToday + "," + reason + ',"' + REASON_LABELS.SCHEDULE + '")'
  );
  panel.getRange("B9").setFormula("=COUNTIFS(" + today + "," + reason + ',"Bloqueado*")');

  // Tabela auxiliar (oculta) com o resumo por dia, usada pelos gráficos.
  panel.getRange("J1").setFormula(
    "=IFERROR(QUERY({ARRAYFORMULA(IF(" + dateTime + '<>"",DATE(VALUE(MID(' + dateTime + ",7,4)),VALUE(MID(" +
    dateTime + ",4,2)),VALUE(LEFT(" + dateTime + ",2))),))," + irrigated + "," + durationSec + "}," +
    "\"select Col1, count(Col1), sum(Col3) where Col2 = '" + YES + "' group by Col1 order by Col1 " +
    "label Col1 'Dia', count(Col1) 'Irrigações', sum(Col3) 'Duração (s)'\",0),\"\")"
  );
  panel.getRange("J2:J").setNumberFormat("dd/MM/yyyy");
  panel.getRange("K:L").setNumberFormat("0");

  panel.getRange("A1:B1").setBackground(COLOR.GREEN_DARK).setFontColor(COLOR.WHITE)
    .setFontWeight("bold").setFontSize(16).setVerticalAlignment("middle");
  panel.getRange("A3:A9").setBackground(COLOR.GREEN_LIGHT).setFontWeight("bold").setVerticalAlignment("middle");
  panel.getRange("B3:B9").setFontSize(14).setHorizontalAlignment("left").setVerticalAlignment("middle");
  panel.getRange("A3:B9").setBorder(true, true, true, true, true, true, "#c9d6ce",
    SpreadsheetApp.BorderStyle.SOLID);
  panel.setColumnWidth(1, 270);
  panel.setColumnWidth(2, 240);
  panel.setRowHeight(1, 38);
  panel.setRowHeights(3, 7, 32);
  panel.setFrozenRows(1);
  panel.setTabColor(COLOR.GREEN_DARK);
  panel.hideColumns(10, 3);
  panel.hideColumns(26);
}

function ensureDashboardCharts_(spreadsheet, panel) {
  const versionKey = "PAINEL_CHARTS_VERSION_" + spreadsheet.getId();
  const chartIdsKey = "PAINEL_CHART_IDS_" + spreadsheet.getId();
  const chartIds = JSON.parse(getProperty_(chartIdsKey) || "[]");
  const existingCharts = panel.getCharts();
  const allChartsExist = chartIds.length === 3 && chartIds.every(function(id) {
    return existingCharts.some(function(chart) { return chart.getChartId() === id; });
  });
  if (getProperty_(versionKey) === DASHBOARD_CHARTS_VERSION && allChartsExist) return;

  existingCharts.forEach(function(chart) {
    if (chartIds.indexOf(chart.getChartId()) >= 0) panel.removeChart(chart);
  });

  const records = spreadsheet.getSheetByName(RECORDS_SHEET);
  const createdChartIds = [];
  const insertChart = function(builder, title, horizontalTitle, verticalTitle, row, column) {
    panel.insertChart(builder
      .setNumHeaders(1)
      .setPosition(row, column, 0, 0)
      .setOption("title", title)
      .setOption("legend", { position: "none" })
      .setOption("colors", [COLOR.GREEN_DARK])
      .setOption("hAxis", { title: horizontalTitle })
      .setOption("vAxis", { title: verticalTitle, minValue: 0 })
      .setOption("width", 680)
      .setOption("height", 340)
      .build());
    const charts = panel.getCharts();
    createdChartIds.push(charts[charts.length - 1].getChartId());
  };

  insertChart(
    panel.newChart()
      .setChartType(Charts.ChartType.COLUMN)
      .addRange(records.getRange("A:A"))
      .addRange(records.getRange("E:E"))
      .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS),
    "Tempo de irrigação por evento", "Data/hora", "Duração (s)", 11, 1
  );
  insertChart(
    panel.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(panel.getRange("J:K"))
      .setHiddenDimensionStrategy(Charts.ChartHiddenDimensionStrategy.SHOW_BOTH),
    "Quantidade de irrigações por dia", "Dia", "Irrigações", 11, 9
  );
  insertChart(
    panel.newChart()
      .setChartType(Charts.ChartType.LINE)
      .addRange(panel.getRange("J:J"))
      .addRange(panel.getRange("L:L"))
      .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS)
      .setHiddenDimensionStrategy(Charts.ChartHiddenDimensionStrategy.SHOW_BOTH),
    "Tempo total de irrigação por dia", "Dia", "Duração (s)", 30, 1
  );

  setProperty_(chartIdsKey, JSON.stringify(createdChartIds));
  setProperty_(versionKey, DASHBOARD_CHARTS_VERSION);
}

// ---------------------------------------------------------------------------
// Utilitários
// ---------------------------------------------------------------------------

function formatDateTime_(date, timeZone) {
  return Utilities.formatDate(date, timeZone, "dd/MM/yyyy HH:mm:ss");
}

function formatDuration_(seconds) {
  seconds = Number(seconds);
  if (!isFinite(seconds) || seconds < 0) return "";

  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  if (minutes && remainingSeconds) return minutes + " min " + remainingSeconds + " s";
  return minutes ? minutes + " min" : seconds + " s";
}

function getSpreadsheet_() {
  const spreadsheetId = getProperty_("SPREADSHEET_ID");
  if (spreadsheetId) return SpreadsheetApp.openById(spreadsheetId);

  const spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  if (!spreadsheet) throw new Error("Propriedade SPREADSHEET_ID não configurada no script");
  return spreadsheet;
}

function checkToken_(provided) {
  const expected = getProperty_("ACCESS_TOKEN");
  if (!expected || provided !== expected) throw new Error("Não autorizado");
}

// As propriedades do script são lidas uma vez por solicitação: o ESP32
// consulta o histórico a cada 30 s e cada leitura avulsa custa uma chamada.
let propertiesCache_ = null;

function getProperty_(key) {
  if (propertiesCache_ === null) {
    propertiesCache_ = PropertiesService.getScriptProperties().getProperties();
  }
  const value = propertiesCache_[key];
  return value === undefined ? null : value;
}

// Releitura sem cache, para conferir dentro de um lock se outra execução já
// concluiu a mesma migração.
function getFreshProperty_(key) {
  return PropertiesService.getScriptProperties().getProperty(key);
}

function setProperty_(key, value) {
  PropertiesService.getScriptProperties().setProperty(key, value);
  if (propertiesCache_ !== null) propertiesCache_[key] = value;
}

function errorMessage_(error) {
  return error && error.message ? error.message : String(error);
}

function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}
