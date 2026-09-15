/**
 * Webcom Chrome Extension - Background Service Worker (Manifest V3)
 * 負責擴充功能圖示點擊互動、Side Panel 側邊欄控制與獨立分頁開啟
 */

// 1. 點擊瀏覽器工具列圖標時，預設開啟 Chrome Side Panel (側邊欄)
if (chrome.sidePanel && typeof chrome.sidePanel.setPanelBehavior === 'function') {
    chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true }).catch((err) => {
        console.warn('[Webcom Extension] SidePanel behavior setup:', err);
    });
}

// 2. 右鍵選單：提供「以獨立分頁開啟全螢幕 Webcom 控制台」
chrome.runtime.onInstalled.addListener(() => {
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
    if (info.menuItemId === "open_webcom_fullscreen") {
        chrome.tabs.create({ url: chrome.runtime.getURL("index.html") });
    } else if (info.menuItemId === "open_webcom_sidepanel" && tab && tab.id) {
        if (chrome.sidePanel && chrome.sidePanel.open) {
            chrome.sidePanel.open({ tabId: tab.id });
        }
    }
});
