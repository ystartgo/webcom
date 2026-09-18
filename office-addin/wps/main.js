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

function EnsureTaskPane() {
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
    }
    return tp;
}

function GetDocSelectionText() {
    try {
        var app = (typeof wps !== 'undefined' && wps.WpsApplication) ? wps.WpsApplication() : (typeof wps !== 'undefined' && wps.Application ? wps.Application : null);
        if (app && app.Selection && app.Selection.Text) {
            return String(app.Selection.Text).replace(/\r/g, "");
        }
    } catch(e) {}
    return "";
}

function GetDocFullText() {
    try {
        var app = (typeof wps !== 'undefined' && wps.WpsApplication) ? wps.WpsApplication() : (typeof wps !== 'undefined' && wps.Application ? wps.Application : null);
        if (app && app.ActiveDocument && app.ActiveDocument.Content && app.ActiveDocument.Content.Text) {
            return String(app.ActiveDocument.Content.Text).replace(/\r/g, "");
        }
    } catch(e) {}
    return "";
}

function OnAction(control) {
    try {
        var ctrlId = control ? (control.Id || control.id || "btnOpenTaskpane") : "btnOpenTaskpane";
        
        var selText = GetDocSelectionText();
        var fullText = "";
        if (ctrlId === "btnDocSummary" || ctrlId === "btnDocQA") {
            fullText = GetDocFullText();
        }

        var payload = {
            action: ctrlId,
            selectionText: selText,
            fullText: fullText,
            timestamp: new Date().getTime()
        };

        try {
            localStorage.setItem("webcom_pending_action", JSON.stringify(payload));
        } catch(lsErr) {}

        EnsureTaskPane();
    } catch(err) {
        alert("執行 Webcom AI 操作異常: " + (err.message || String(err)));
    }
    return true;
}

function OnToggleTaskPane(control) {
    return OnAction(control);
}
