/**
 * Webcom Office Bridge
 * 封裝微軟 Office.js 原生 API，支援 Word, Excel, PowerPoint 自動操作與圖表產生
 */
window.OfficeBridge = (function() {
    let _hostType = 'unknown'; // 'Word' | 'Excel' | 'PowerPoint' | 'web-standalone'
    let _isOfficeReady = false;

    async function init() {
        return new Promise((resolve) => {
            if (typeof Office !== 'undefined') {
                Office.onReady((info) => {
                    _isOfficeReady = true;
                    if (info.host === Office.HostType.Word) {
                        _hostType = 'Word';
                    } else if (info.host === Office.HostType.Excel) {
                        _hostType = 'Excel';
                    } else if (info.host === Office.HostType.PowerPoint) {
                        _hostType = 'PowerPoint';
                    } else {
                        _hostType = 'Office-Other';
                    }
                    console.log(`[OfficeBridge] Initialized in host: ${_hostType}`);
                    resolve({ isOfficeReady: true, host: _hostType });
                });
            } else {
                _hostType = 'web-standalone';
                console.log(`[OfficeBridge] Running in standalone web browser mode`);
                resolve({ isOfficeReady: false, host: _hostType });
            }
        });
    }

    function getHostType() {
        return _hostType;
    }

    // ── 1. 讀取目前文件中使用者選取的內容 ──
    async function getSelectedContent() {
        if (!_isOfficeReady) {
            return "【模擬環境】目前處於瀏覽器預覽模式，未連接至微軟 Office 主機。";
        }

        try {
            if (_hostType === 'Word') {
                return await Word.run(async (context) => {
                    const selection = context.document.getSelection();
                    selection.load('text');
                    await context.sync();
                    return selection.text.trim();
                });
            } else if (_hostType === 'Excel') {
                return await Excel.run(async (context) => {
                    const range = context.workbook.getSelectedRange();
                    range.load(['values', 'formulas', 'address']);
                    await context.sync();
                    
                    const values = range.values;
                    if (!values || values.length === 0) return "";
                    
                    // 轉為 Markdown 表格字串
                    const lines = [];
                    lines.push(`【選取範圍: ${range.address}】`);
                    values.forEach((row) => {
                        lines.push("| " + row.map(cell => String(cell != null ? cell : "")).join(" | ") + " |");
                    });
                    return lines.join("\n");
                });
            } else if (_hostType === 'PowerPoint') {
                return await new Promise((resolve, reject) => {
                    Office.context.document.getSelectedDataAsync(Office.CoercionType.Text, (result) => {
                        if (result.status === Office.AsyncResultStatus.Succeeded) {
                            resolve(result.value || "");
                        } else {
                            resolve("");
                        }
                    });
                });
            }
        } catch (err) {
            console.error('[OfficeBridge getSelectedContent Error]', err);
            return `讀取失敗: ${err.message}`;
        }
        return "";
    }

    // ── 2. 自動在文件游標處插入 / 取代文字或表格 ──
    async function insertText(text, options = {}) {
        if (!_isOfficeReady) {
            console.log('[Mock Insert Text]', text);
            return { success: true, mock: true, text };
        }

        try {
            if (_hostType === 'Word') {
                await Word.run(async (context) => {
                    const selection = context.document.getSelection();
                    if (options.replace) {
                        selection.insertText(text, Word.InsertLocation.replace);
                    } else {
                        selection.insertText(text, Word.InsertLocation.after);
                    }
                    await context.sync();
                });
                return { success: true };
            } else if (_hostType === 'Excel') {
                await Excel.run(async (context) => {
                    const range = context.workbook.getSelectedRange();
                    range.values = [[text]];
                    await context.sync();
                });
                return { success: true };
            } else if (_hostType === 'PowerPoint') {
                return await new Promise((resolve) => {
                    Office.context.document.setSelectedDataAsync(text, { coercionType: Office.CoercionType.Text }, (asyncResult) => {
                        resolve({ success: asyncResult.status === Office.AsyncResultStatus.Succeeded });
                    });
                });
            }
        } catch (err) {
            console.error('[OfficeBridge insertText Error]', err);
            return { success: false, error: err.message };
        }
    }

    // ── 3. Excel 專屬：自動寫入結構化二維矩陣資料 (表格) ──
    async function writeExcelMatrix(headers, rows, startCell = 'A1') {
        if (_hostType !== 'Excel') {
            return { success: false, error: '目前主機不是 Excel，無法寫入試算表矩陣。' };
        }

        try {
            await Excel.run(async (context) => {
                const sheet = context.workbook.worksheets.getActiveWorksheet();
                const allData = [headers, ...rows];
                const rowCount = allData.length;
                const colCount = headers.length;

                // 取得範圍並賦值
                const range = sheet.getRange(startCell).getResizedRange(rowCount - 1, colCount - 1);
                range.values = allData;
                
                // 標題列格式化
                const headerRange = sheet.getRange(startCell).getResizedRange(0, colCount - 1);
                headerRange.format.fill.color = "#4F46E5"; // Indigo
                headerRange.format.font.color = "#FFFFFF";
                headerRange.format.font.bold = true;
                
                range.format.autofitColumns();
                await context.sync();
            });
            return { success: true };
        } catch (err) {
            console.error('[OfficeBridge writeExcelMatrix Error]', err);
            return { success: false, error: err.message };
        }
    }

    // ── 4. Excel 專屬：自動生成原生圖表 (Pie, ColumnClustered, Line) ──
    async function createExcelChart(chartType = 'ColumnClustered', dataRangeAddress = 'A1:B5', title = 'Webcom AI 自動圖表') {
        if (_hostType !== 'Excel') {
            return { success: false, error: '非 Excel 主機環境' };
        }

        try {
            await Excel.run(async (context) => {
                const sheet = context.workbook.worksheets.getActiveWorksheet();
                const range = sheet.getRange(dataRangeAddress);
                
                let excelType = Excel.ChartType.columnClustered;
                const ct = chartType.toLowerCase();
                if (ct.includes('pie')) excelType = Excel.ChartType.pie;
                else if (ct.includes('line')) excelType = Excel.ChartType.line;
                else if (ct.includes('bar')) excelType = Excel.ChartType.barClustered;
                
                const chart = sheet.charts.add(excelType, range, Excel.ChartSeriesBy.auto);
                chart.title.text = title;
                chart.legend.position = Excel.ChartLegendPosition.right;
                chart.top = 220;
                chart.left = 40;
                chart.width = 480;
                chart.height = 300;

                await context.sync();
            });
            return { success: true };
        } catch (err) {
            console.error('[OfficeBridge createExcelChart Error]', err);
            return { success: false, error: err.message };
        }
    }

    // ── 5. 通用：將 Base64 圖片 (如 ECharts 渲染結果) 插入至文件游標處 ──
    async function insertImageBase64(base64Data) {
        // 移除前綴 data:image/png;base64,
        const cleanBase64 = base64Data.replace(/^data:image\/(png|jpeg|jpg);base64,/, '');

        if (!_isOfficeReady) {
            console.log('[Mock Insert Image] Base64 length:', cleanBase64.length);
            return { success: true, mock: true };
        }

        try {
            if (_hostType === 'Word') {
                await Word.run(async (context) => {
                    const selection = context.document.getSelection();
                    selection.insertInlinePictureFromBase64(cleanBase64, Word.InsertLocation.after);
                    await context.sync();
                });
                return { success: true };
            } else if (_hostType === 'Excel') {
                await Excel.run(async (context) => {
                    const sheet = context.workbook.worksheets.getActiveWorksheet();
                    sheet.shapes.addImage(cleanBase64);
                    await context.sync();
                });
                return { success: true };
            } else if (_hostType === 'PowerPoint') {
                return await new Promise((resolve) => {
                    Office.context.document.setSelectedDataAsync(
                        cleanBase64,
                        { coercionType: Office.CoercionType.Image },
                        (asyncResult) => {
                            resolve({ success: asyncResult.status === Office.AsyncResultStatus.Succeeded });
                        }
                    );
                });
            }
        } catch (err) {
            console.error('[OfficeBridge insertImageBase64 Error]', err);
            return { success: false, error: err.message };
        }
    }

    return {
        init,
        getHostType,
        getSelectedContent,
        insertText,
        writeExcelMatrix,
        createExcelChart,
        insertImageBase64
    };
})();