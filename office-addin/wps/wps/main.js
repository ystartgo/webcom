// Webcom WPS JS Add-in Core Logic
var _webcomTaskPane = null;

function OnAddinLoad(ribbonUI) {
    window.ribbonUI = ribbonUI;
    console.log("Webcom WPS Add-in Initialized");
}

function OnAction(control) {
    try {
        if (_webcomTaskPane) {
            try {
                _webcomTaskPane.Visible = !_webcomTaskPane.Visible;
                return true;
            } catch(e) {
                _webcomTaskPane = null;
            }
        }

        var tp = null;
        // 優先路徑 1：相對路徑 taskpane.html (本機離線免聯網)
        try {
            tp = wps.CreateTaskPane("taskpane.html", "Webcom AI 智慧助理");
        } catch(e1) {
            console.log("Relative CreateTaskPane failed:", e1);
        }

        // 優先路徑 2：同源 URL
        if (!tp) {
            try {
                var origin = (typeof location !== 'undefined' && location.origin) ? location.origin : "https://127.0.0.1:8002";
                tp = wps.CreateTaskPane(origin + "/office-addin/taskpane.html", "Webcom AI 智慧助理");
            } catch(e2) {
                console.log("Origin CreateTaskPane failed:", e2);
            }
        }

        // 備援路徑 3：本機 HTTPS 8002
        if (!tp) {
            try {
                tp = wps.CreateTaskPane("https://127.0.0.1:8002/office-addin/taskpane.html", "Webcom AI 智慧助理");
            } catch(e3) {
                console.log("HTTPS 8002 CreateTaskPane failed:", e3);
            }
        }

        // 備援路徑 4：本機 HTTP 8001 (免 SSL 憑證檢驗)
        if (!tp) {
            try {
                tp = wps.CreateTaskPane("http://127.0.0.1:8001/office-addin/taskpane.html", "Webcom AI 智慧助理");
            } catch(e4) {
                console.log("HTTP 8001 CreateTaskPane failed:", e4);
            }
        }

        if (tp) {
            _webcomTaskPane = tp;
            if (typeof tp.Show === 'function') {
                try { tp.Show(); } catch(sErr) {}
            }
            tp.Visible = true;
            tp.Width = 330;
        } else {
            alert("未能成功建立 Webcom 任務窗格，請在 WPS 按 Alt+F12 查看除錯資訊。");
        }
    } catch(err) {
        alert("開啟 Webcom 側邊欄異常: " + (err.message || String(err)));
    }
    return true;
}

function OnToggleTaskPane(control) {
    return OnAction(control);
}
