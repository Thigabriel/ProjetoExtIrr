function doGet(e) {
  try {
    checkToken_(e.parameter.token);
    var sheet = getSheet_();
    var lastRow = sheet.getLastRow();
    var count = Math.min(25, Math.max(0, lastRow - 1));
    var history = [];

    if (count > 0) {
      var rows = sheet.getRange(lastRow - count + 1, 1, count, 8).getValues();
      for (var i = rows.length - 1; i >= 0; i--) {
        history.push({
          timestamp: Number(rows[i][1]),
          irrigated: rows[i][2] === true,
          durationSec: Number(rows[i][4]),
          reason: normalizeReason_(rows[i][5]),
          eventId: String(rows[i][6]),
          deviceId: String(rows[i][7] || "")
        });
      }
    }

    return json_({
      ok: true,
      total: Math.max(0, lastRow - 1),
      spreadsheetUrl: getSpreadsheet_().getUrl(),
      timeZone: Session.getScriptTimeZone(),
      history: history
    });
  } catch (error) {
    return json_({ ok: false, error: String(error), total: 0, history: [] });
  }
}

function doPost(e) {
  try {
    var data = parseRequest_(e);
    checkToken_(data.token);
    var event = null;
    if (data.action !== "clear") {
      if (data.action !== "append") throw new Error("Invalid action");
      event = validateEvent_(data);
    }
    var sheet = getSheet_();

    if (data.action === "clear") {
      clearRecords_(sheet);
      return json_({ ok: true });
    }

    var lock = LockService.getScriptLock();
    lock.waitLock(10000);
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
    return json_({ ok: false, error: String(error) });
  }
}

function parseRequest_(e) {
  if (!e || !e.postData || typeof e.postData.contents !== "string") {
    throw new Error("Missing JSON body");
  }
  var data = JSON.parse(e.postData.contents);
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    throw new Error("JSON body must be an object");
  }
  return data;
}

function validateEvent_(data) {
  var timestamp = parseIntegerField_(data.timestamp, "timestamp", 0, 4294967295);
  var durationSec = parseIntegerField_(data.durationSec, "durationSec", 0, 65535);
  var irrigated = parseBooleanField_(data.irrigated);
  var reason = typeof data.reason === "string" ? normalizeReason_(data.reason) : "";
  var eventId = normalizeIdentifier_(data.eventId, "eventId", false);
  var deviceId = normalizeIdentifier_(data.deviceId, "deviceId", true);

  if (!reason || reason.length > 80) throw new Error("Invalid reason");
  return { timestamp: timestamp, durationSec: durationSec, irrigated: irrigated,
    reason: reason, eventId: eventId, deviceId: deviceId };
}

function parseIntegerField_(value, name, minimum, maximum) {
  if ((typeof value !== "number" && typeof value !== "string") ||
      (typeof value === "string" && value.trim() === "")) {
    throw new Error("Invalid " + name);
  }
  var parsed = Number(value);
  if (!Number.isSafeInteger(parsed) || parsed < minimum || parsed > maximum) {
    throw new Error("Invalid " + name);
  }
  return parsed;
}

function parseBooleanField_(value) {
  if (value === true || value === 1 || (typeof value === "string" && value.trim().toLowerCase() === "true")) {
    return true;
  }
  if (value === false || value === 0 || (typeof value === "string" && value.trim().toLowerCase() === "false")) {
    return false;
  }
  throw new Error("Invalid irrigated");
}

function normalizeIdentifier_(value, name, optional) {
  if (value == null && optional) return "";
  if (typeof value !== "string" && typeof value !== "number") {
    throw new Error("Invalid " + name);
  }
  var identifier = String(value).trim();
  if ((!identifier && !optional) || identifier.length > 128) {
    throw new Error("Invalid " + name);
  }
  return identifier;
}

function formatRecord_(event, timeZone) {
  return [
    formatDateTime_(new Date(event.timestamp * 1000), timeZone),
    event.timestamp,
    event.irrigated,
    formatDuration_(event.durationSec),
    event.durationSec,
    event.reason,
    event.eventId,
    event.deviceId
  ];
}

function hasDuplicateEvent_(sheet, eventId, deviceId) {
  var rowCount = sheet.getLastRow() - 1;
  if (rowCount <= 0) return false;

  var matches = sheet.getRange(2, 7, rowCount, 1).createTextFinder(eventId)
    .matchCase(true).matchEntireCell(true).findAll();
  for (var i = 0; i < matches.length; i++) {
    var existingDeviceId = String(sheet.getRange(matches[i].getRow(), 8).getValue() || "");
    if (existingDeviceId === deviceId) return true;
  }
  return false;
}

function clearRecords_(sheet) {
  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    sheet.clearContents();
    sheet.appendRow(headerRow_());
  } finally {
    lock.releaseLock();
  }
}

function getSheet_() {
  var spreadsheet = getSpreadsheet_();
  var sheet = spreadsheet.getSheetByName("REGISTROS");
  if (!sheet) {
    sheet = spreadsheet.getSheetByName("Irrigacoes");
    if (sheet) {
      sheet.setName("REGISTROS");
    } else {
      sheet = spreadsheet.insertSheet("REGISTROS");
    }
  }

  if (sheet.getLastRow() === 0) {
    sheet.appendRow(headerRow_());
  } else {
    var header = sheet.getRange(1, 1, 1, 8).getValues()[0];
    if (header[3] !== "Duração" || header[4] !== "Duração (s)") {
      var rowCount = sheet.getLastRow() - 1;
      if (rowCount > 0) {
        var oldRows = sheet.getRange(2, 1, rowCount, 7).getValues();
        var migratedRows = oldRows.map(function(row) {
          var durationSec = Number(row[3]);
          return [row[0], row[1], row[2], formatDuration_(durationSec), durationSec,
            row[4], row[5], String(row[6] || "")];
        });
        sheet.getRange(2, 1, rowCount, 8).setValues(migratedRows);
      }
    }
    sheet.getRange(1, 1, 1, 8).setValues([headerRow_()]);
  }
  syncDateTimeColumn_(sheet, spreadsheet, Session.getScriptTimeZone());
  syncReasonColumn_(sheet, spreadsheet);
  formatRecordsSheet_(sheet, spreadsheet);
  ensureDashboard_(spreadsheet, Session.getScriptTimeZone());
  return sheet;
}

function formatRecordsSheet_(sheet, spreadsheet) {
  var properties = PropertiesService.getScriptProperties();
  var formatKey = "REGISTROS_FORMAT_VERSION_" + spreadsheet.getId();
  if (properties.getProperty(formatKey) === "1") return;

  var maxRows = sheet.getMaxRows();
  var tableRange = sheet.getRange(1, 1, maxRows, 8);
  if (!sheet.getFilter()) tableRange.createFilter();
  if (sheet.getBandings().length === 0) {
    var banding = tableRange.applyRowBanding(SpreadsheetApp.BandingTheme.LIGHT_GREY, true, false);
    banding.setHeaderRowColor("#245b43");
    banding.setFirstRowColor("#ffffff");
    banding.setSecondRowColor("#f3f6f4");
  }

  sheet.setFrozenRows(1);
  sheet.setTabColor("#245b43");
  sheet.getRange(1, 1, 1, 8).setBackground("#245b43").setFontColor("#ffffff").setFontWeight("bold");
  var dataRows = Math.max(1, maxRows - 1);
  sheet.getRange(2, 1, dataRows, 1).setNumberFormat("@");
  sheet.getRange(2, 2, dataRows, 1).setNumberFormat("0");
  sheet.getRange(2, 5, dataRows, 1).setNumberFormat("0");
  sheet.getRange(2, 2, dataRows, 1).setHorizontalAlignment("center");
  sheet.getRange(2, 3, dataRows, 1).setHorizontalAlignment("center");
  sheet.getRange(2, 4, dataRows, 1).setHorizontalAlignment("center");
  sheet.getRange(2, 5, dataRows, 1).setHorizontalAlignment("center");
  sheet.getRange(2, 7, dataRows, 2).setHorizontalAlignment("center");
  sheet.setColumnWidth(1, 155);
  sheet.setColumnWidth(2, 125);
  sheet.setColumnWidth(3, 105);
  sheet.setColumnWidth(4, 125);
  sheet.setColumnWidth(5, 105);
  sheet.setColumnWidth(6, 230);
  sheet.setColumnWidth(7, 175);
  sheet.setColumnWidth(8, 130);
  properties.setProperty(formatKey, "1");
}

function ensureDashboard_(spreadsheet, timeZone) {
  var panel = spreadsheet.getSheetByName("PAINEL");
  if (!panel) panel = spreadsheet.insertSheet("PAINEL");

  var properties = PropertiesService.getScriptProperties();
  var setupKey = "PAINEL_SETUP_VERSION_" + spreadsheet.getId();
  if (properties.getProperty(setupKey) !== "2" ||
      panel.getRange("A1").getValue() !== "SISTEMA DE IRRIGAÇÃO") {
    panel.getRange("A1").setValue("SISTEMA DE IRRIGAÇÃO");
    panel.getRange("A3:A8").setValues([
      ["Irrigações hoje"],
      ["Tempo total hoje"],
      ["Última irrigação (data/hora)"],
      ["Motivo"],
      ["Irrigações manuais hoje"],
      ["Irrigações automáticas hoje"]
    ]);

    panel.getRange("Z1").setNumberFormat("@");
    panel.getRange("Z2").setFormula(
      '=SUMIFS(\'REGISTROS\'!E2:E,\'REGISTROS\'!A2:A,$Z$1&"*",\'REGISTROS\'!C2:C,TRUE)'
    );
    panel.getRange("B3").setFormula(
      '=COUNTIFS(\'REGISTROS\'!A2:A,$Z$1&"*",\'REGISTROS\'!C2:C,TRUE)'
    );
    panel.getRange("B4").setFormula(
      '=IF($Z$2=0,"0 s",IF(INT($Z$2/60)>0,INT($Z$2/60)&" min","")&IF(MOD($Z$2,60)>0,IF(INT($Z$2/60)>0," ","")&MOD($Z$2,60)&" s",""))'
    );
    panel.getRange("B5").setFormula(
      '=IFERROR(INDEX(\'REGISTROS\'!A2:A,MATCH(MAXIFS(\'REGISTROS\'!B2:B,\'REGISTROS\'!C2:C,TRUE),\'REGISTROS\'!B2:B,0)),"Sem registros")'
    );
    panel.getRange("B6").setFormula(
      '=IFERROR(INDEX(\'REGISTROS\'!F2:F,MATCH(MAXIFS(\'REGISTROS\'!B2:B,\'REGISTROS\'!C2:C,TRUE),\'REGISTROS\'!B2:B,0)),"-")'
    );
    panel.getRange("B7").setFormula(
      '=COUNTIFS(\'REGISTROS\'!A2:A,$Z$1&"*",\'REGISTROS\'!C2:C,TRUE,\'REGISTROS\'!F2:F,"MANUAL")'
    );
    panel.getRange("B8").setFormula(
      '=COUNTIFS(\'REGISTROS\'!A2:A,$Z$1&"*",\'REGISTROS\'!C2:C,TRUE,\'REGISTROS\'!F2:F,"SCHEDULE")'
    );
    panel.getRange("J1").setFormula(
      '=IFERROR(QUERY({ARRAYFORMULA(IF(\'REGISTROS\'!A2:A<>"",DATE(VALUE(MID(\'REGISTROS\'!A2:A,7,4)),VALUE(MID(\'REGISTROS\'!A2:A,4,2)),VALUE(LEFT(\'REGISTROS\'!A2:A,2))),)),\'REGISTROS\'!C2:C,\'REGISTROS\'!E2:E},"select Col1, count(Col1), sum(Col3) where Col2 = TRUE group by Col1 order by Col1 label Col1 \'Dia\', count(Col1) \'Irrigações\', sum(Col3) \'Duração (s)\'",0),"")'
    );
    panel.getRange("J2:J").setNumberFormat("dd/MM/yyyy");
    panel.getRange("K:L").setNumberFormat("0");

    panel.getRange("A1:B1").setBackground("#245b43").setFontColor("#ffffff")
      .setFontWeight("bold").setFontSize(16);
    panel.getRange("A3:A8").setBackground("#e8f1eb").setFontWeight("bold");
    panel.getRange("B3:B8").setFontSize(14);
    panel.setColumnWidth(1, 270);
    panel.setColumnWidth(2, 240);
    panel.setRowHeight(1, 38);
    panel.setRowHeights(3, 6, 32);
    panel.setFrozenRows(1);
    panel.hideColumns(10, 3);
    panel.hideColumns(26);
    properties.setProperty(setupKey, "2");
  }

  var today = Utilities.formatDate(new Date(), timeZone, "dd/MM/yyyy");
  if (panel.getRange("Z1").getValue() !== today) panel.getRange("Z1").setValue(today);
  ensureDashboardCharts_(spreadsheet, panel);
}

function ensureDashboardCharts_(spreadsheet, panel) {
  var properties = PropertiesService.getScriptProperties();
  var versionKey = "PAINEL_CHARTS_VERSION_" + spreadsheet.getId();
  var chartIdsKey = "PAINEL_CHART_IDS_" + spreadsheet.getId();
  var chartIds = JSON.parse(properties.getProperty(chartIdsKey) || "[]");
  var existingCharts = panel.getCharts();
  var allChartsExist = chartIds.length === 3 && chartIds.every(function(id) {
    return existingCharts.some(function(chart) { return chart.getChartId() === id; });
  });
  if (properties.getProperty(versionKey) === "1" && allChartsExist) return;

  existingCharts.forEach(function(chart) {
    if (chartIds.indexOf(chart.getChartId()) >= 0) panel.removeChart(chart);
  });

  var records = spreadsheet.getSheetByName("REGISTROS");
  var createdChartIds = [];
  var eventChart = panel.newChart()
    .setChartType(Charts.ChartType.COLUMN)
    .addRange(records.getRange("A:A"))
    .addRange(records.getRange("E:E"))
    .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS)
    .setNumHeaders(1)
    .setPosition(11, 1, 0, 0)
    .setOption("title", "Tempo de irrigação por evento")
    .setOption("legend", { position: "none" })
    .setOption("hAxis", { title: "Data/hora" })
    .setOption("vAxis", { title: "Duração (s)", minValue: 0 })
    .setOption("width", 680)
    .setOption("height", 340)
    .build();
  panel.insertChart(eventChart);
  createdChartIds.push(panel.getCharts()[panel.getCharts().length - 1].getChartId());

  var dailyCountChart = panel.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(panel.getRange("J:K"))
    .setNumHeaders(1)
    .setHiddenDimensionStrategy(Charts.ChartHiddenDimensionStrategy.SHOW_BOTH)
    .setPosition(11, 9, 0, 0)
    .setOption("title", "Quantidade de irrigações por dia")
    .setOption("legend", { position: "none" })
    .setOption("hAxis", { title: "Dia" })
    .setOption("vAxis", { title: "Irrigações", minValue: 0 })
    .setOption("width", 680)
    .setOption("height", 340)
    .build();
  panel.insertChart(dailyCountChart);
  createdChartIds.push(panel.getCharts()[panel.getCharts().length - 1].getChartId());

  var dailyDurationChart = panel.newChart()
    .setChartType(Charts.ChartType.LINE)
    .addRange(panel.getRange("J:J"))
    .addRange(panel.getRange("L:L"))
    .setMergeStrategy(Charts.ChartMergeStrategy.MERGE_COLUMNS)
    .setNumHeaders(1)
    .setHiddenDimensionStrategy(Charts.ChartHiddenDimensionStrategy.SHOW_BOTH)
    .setPosition(30, 1, 0, 0)
    .setOption("title", "Tempo total de irrigação por dia")
    .setOption("legend", { position: "none" })
    .setOption("hAxis", { title: "Dia" })
    .setOption("vAxis", { title: "Duração (s)", minValue: 0 })
    .setOption("width", 680)
    .setOption("height", 340)
    .build();
  panel.insertChart(dailyDurationChart);
  createdChartIds.push(panel.getCharts()[panel.getCharts().length - 1].getChartId());

  properties.setProperty(chartIdsKey, JSON.stringify(createdChartIds));
  properties.setProperty(versionKey, "1");
}

function syncDateTimeColumn_(sheet, spreadsheet, timeZone) {
  var properties = PropertiesService.getScriptProperties();
  var propertyKey = "REGISTROS_TIME_ZONE_" + spreadsheet.getId();
  if (properties.getProperty(propertyKey) === timeZone) return;

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    if (properties.getProperty(propertyKey) === timeZone) return;

    var lastRow = sheet.getLastRow();
    if (lastRow > 1) {
      var rows = sheet.getRange(2, 1, lastRow - 1, 2).getValues();
      var dateTimes = rows.map(function(row) {
        var timestamp = row[1];
        if (timestamp !== "" && isFinite(Number(timestamp))) {
          return [formatDateTime_(new Date(Number(timestamp) * 1000), timeZone)];
        }
        if (row[0] instanceof Date) return [formatDateTime_(row[0], timeZone)];
        return [row[0]];
      });
      sheet.getRange(2, 1, dateTimes.length, 1).setValues(dateTimes);
    }

    properties.setProperty(propertyKey, timeZone);
  } finally {
    lock.releaseLock();
  }
}

function syncReasonColumn_(sheet, spreadsheet) {
  var properties = PropertiesService.getScriptProperties();
  var propertyKey = "REGISTROS_REASON_NORMALIZED_" + spreadsheet.getId();
  if (properties.getProperty(propertyKey) === "true") return;

  var lock = LockService.getScriptLock();
  lock.waitLock(10000);
  try {
    if (properties.getProperty(propertyKey) === "true") return;

    var rowCount = sheet.getLastRow() - 1;
    if (rowCount > 0) {
      var reasons = sheet.getRange(2, 6, rowCount, 1).getValues()
        .map(function(row) { return [normalizeReason_(row[0])]; });
      sheet.getRange(2, 6, rowCount, 1).setValues(reasons);
    }
    properties.setProperty(propertyKey, "true");
  } finally {
    lock.releaseLock();
  }
}

function normalizeReason_(reason) {
  return String(reason == null ? "" : reason).trim().toUpperCase();
}

function formatDateTime_(date, timeZone) {
  return Utilities.formatDate(date, timeZone, "dd/MM/yyyy HH:mm:ss");
}

function formatDuration_(seconds) {
  seconds = Number(seconds);
  if (!isFinite(seconds) || seconds < 0) return "";

  var minutes = Math.floor(seconds / 60);
  var remainingSeconds = seconds % 60;
  if (minutes && remainingSeconds) return minutes + " min " + remainingSeconds + " s";
  return minutes ? minutes + " min" : seconds + " s";
}

function headerRow_() {
  return ["Data/Hora", "timestamp", "Irrigação", "Duração", "Duração (s)", "Motivo", "eventId", "deviceId"];
}

function getSpreadsheet_() {
  var spreadsheetId = PropertiesService.getScriptProperties().getProperty("SPREADSHEET_ID");
  if (spreadsheetId) return SpreadsheetApp.openById(spreadsheetId);

  var spreadsheet = SpreadsheetApp.getActiveSpreadsheet();
  if (!spreadsheet) throw new Error("SPREADSHEET_ID script property is missing");
  return spreadsheet;
}

function checkToken_(provided) {
  var expected = PropertiesService.getScriptProperties().getProperty("ACCESS_TOKEN");
  if (!expected || provided !== expected) throw new Error("Unauthorized");
}

function json_(value) {
  return ContentService.createTextOutput(JSON.stringify(value))
    .setMimeType(ContentService.MimeType.JSON);
}