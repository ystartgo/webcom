// Webcom WPS JS Add-in Core Logic
var _webcomTaskPane = null;

function GetUrlPath() {
    var e = document.location.toString();
    return -1 != (e = decodeURI(e)).indexOf("/") && (e = e.substring(0, e.lastIndexOf("/"))), e;
}

function OnAddinLoad(ribbonUI) {
    window.ribbonUI = ribbonUI;
    console.log("Webcom WPS Add-in Initialized");
}

function OnAction(control) {
    try {
        var tsId = null;
        try {
            tsId = wps.PluginStorage.getItem("WebcomTaskPaneId");
        } catch(stErr) {}

        var tp = null;
        if (tsId) {
            try {
                tp = wps.GetTaskPane(tsId);
            } catch(getErr) {
                tp = null;
            }
        }

        if (!tp) {
            var url = GetUrlPath() + "/taskpane.html";
            try {
                tp = wps.CreateTaskPane(url, "Webcom AI 智慧助理");
            } catch(e1) {
                try {
                    tp = wps.CreateTaskPane("https://127.0.0.1:8002/office-addin/taskpane.html", "Webcom AI 智慧助理");
                } catch(e2) {
                    console.log("CreateTaskPane fallback error: " + e2);
                }
            }
            if (tp && tp.ID) {
                try {
                    wps.PluginStorage.setItem("WebcomTaskPaneId", tp.ID);
                } catch(setErr) {}
            }
        }

        if (tp) {
            _webcomTaskPane = tp;
            try {
                tp.DockPosition = 2; // msoCTPDockPositionRight
            } catch(dpErr) {}
            try {
                tp.Width = 350;
            } catch(wErr) {}
            tp.Visible = true;
            if (typeof tp.Show === 'function') {
                try { tp.Show(); } catch(sErr) {}
            }
        } else {
            alert("未能成功建立 Webcom 任務窗格。\n請確認 WPS 支援 JS 增益集，或使用 Alt+F11 手動展開。");
        }
    } catch(err) {
        alert("開啟 Webcom 側邊欄異常: " + (err.message || String(err)));
    }
    return true;
}

function OnToggleTaskPane(control) {
    return OnAction(control);
}
