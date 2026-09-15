# Webcom AI Console - Chrome Extension (Manifest V3)

這是依據 Google Chrome Manifest V3 標準打造的 **Webcom 雙引擎邊緣 AI 控制台與多協定終端機** 瀏覽器擴充功能。

---

## 🛠️ 如何安裝至 Chrome 瀏覽器

1. 打開 Google Chrome 瀏覽器，在網址列輸入：
   ```
   chrome://extensions/
   ```
2. 開啟右上角的 **「開發人員模式 (Developer mode)」** 開關。
3. 點擊左上角的 **「載入未封裝項目 (Load unpacked)」** 按鈕。
4. 在檔案選擇器中選取本資料夾：
   ```
   C:\Apps\Webcom\extension
   ```
5. 安裝完成！瀏覽器工具列即會出現 Webcom 高科技 AI 圖標。

---

## 💡 使用方式

1. **側邊欄模式 (Side Panel)**：
   - 點擊瀏覽器工具列上的 Webcom 圖標，即在瀏覽器右側開啟側邊欄。
   - 可一邊瀏覽網頁、閱讀文檔，一邊讓 AI 助手操作終端機或分析資料。
2. **全螢幕獨立分頁**：
   - 在擴充功能圖標上點擊滑鼠右鍵 ➔ 選擇 **「🖥️ 以獨立分頁開啟 Webcom 控制台」**。
3. **Python (Pyodide) 零依賴運算**：
   - 內建 `pyodide` 子專案支援，無須開啟後端 Daemon 也能在瀏覽器記憶體中執行 Python 程式碼。
4. **隨時下載原版單機檔案**：
   - 介面右上角提供 **「📥 下載單機版」** 按鈕，一鍵匯出原生單檔 `index.html` 帶走使用！
