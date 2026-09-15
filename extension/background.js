/**
 * Webcom Chrome Extension - Background Service Worker (Manifest V3)
 * 負責擴充功能圖示點擊互動、Side Panel 側邊欄控制、2/3 視窗展開與訊息處理
 */

// 獲取顯示器可用區域並計算 2/3 視窗幾何尺寸 (右側 2/3，左側 1/3 瀏覽器)
function calculateTwoThirdsGeometry(callback) {
    if (chrome.system && chrome.system.display) {
        chrome.system.display.getInfo((displays) => {
            const primary = (displays && displays.find(d => d.isPrimary)) || (displays && displays[0]) || null;
            if (primary && primary.workArea) {
                const wa = primary.workArea;
                const left = Math.round(wa.left + (wa.width * (1 / 3)));
                const top = wa.top;
                const width = Math.round(wa.width * (2 / 3));
                const height = wa.height;
                callback({ left, top, width, height });
                return;
            }
            callback({ left: 640, top: 0, width: 1280, height: 1080 });
        });
    } else {
        callback({ left: 640, top: 0, width: 1280, height: 1080 });
    }
}

// 建立 2/3 展開視窗
function openTwoThirdsWindow() {
    calculateTwoThirdsGeometry((geo) => {
        chrome.windows.create({
            url: chrome.runtime.getURL("index.html"),
            type: "normal",
            left: geo.left,
            top: geo.top,
            width: geo.width,
            height: geo.height,
            focused: true
        });
    });
}

// 1. 點擊瀏覽器工具列圖標時，預設直接以 2/3 獨立視窗展開 (確保 Web Serial 硬體彈窗無障礙支援)
chrome.action.onClicked.addListener((tab) => {
    openTwoThirdsWindow();
});

// 2. 右鍵選單：提供「以 2/3 視窗展開開啟」、「獨立全螢幕分頁」與「側邊欄」
chrome.runtime.onInstalled.addListener(() => {
    chrome.contextMenus.create({
        id: "open_webcom_twothirds",
        title: "◫ 以 2/3 視窗展開開啟 (左側 1/3 瀏覽器，右側 2/3 Webcom)",
        contexts: ["action"]
    });
    chrome.contextMenus.create({
        id: "open_webcom_fullscreen",
        title: "🖥️ 以獨立分頁開啟 Webcom 控制台",
        contexts: ["action"]
    });
    chrome.contextMenus.create({
        id: "open_webcom_sidepanel",
        title: "📑 在側邊欄 (Side Panel) 開啟控制台",
        contexts: ["action"]
    });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
    if (info.menuItemId === "open_webcom_twothirds") {
        openTwoThirdsWindow();
    } else if (info.menuItemId === "open_webcom_fullscreen") {
        chrome.tabs.create({ url: chrome.runtime.getURL("index.html") });
    } else if (info.menuItemId === "open_webcom_sidepanel" && tab && tab.id) {
        if (chrome.sidePanel && chrome.sidePanel.open) {
            chrome.sidePanel.open({ tabId: tab.id });
        }
    }
});

// 3. 監聽頁面傳來的訊息 (如點擊 2/3 視窗展開按鈕時調整當前視窗尺寸或開啟獨立視窗)
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request && request.action === 'open_twothirds_window') {
        openTwoThirdsWindow();
        sendResponse({ success: true });
        return true;
    }
    if (request && request.action === 'open_select_port_popup') {
        chrome.windows.create({
            url: chrome.runtime.getURL('select_port.html'),
            type: 'popup',
            width: 480,
            height: 380,
            focused: true
        });
        sendResponse({ success: true });
        return true;
    }
    if (request && request.action === 'snap_twothirds_window') {
        const windowId = sender.tab ? sender.tab.windowId : chrome.windows.WINDOW_ID_CURRENT;
        calculateTwoThirdsGeometry((geo) => {
            try {
                chrome.windows.update(windowId, {
                    state: "normal",
                    left: geo.left,
                    top: geo.top,
                    width: geo.width,
                    height: geo.height,
                    focused: true
                }, (win) => {
                    sendResponse({ success: !!win });
                });
            } catch (err) {
                console.warn('[Webcom Extension] Error updating window geometry:', err);
                sendResponse({ success: false, error: String(err) });
            }
        });
        return true; // 保持非同步回應
    }
});
