# Webcom Pyodide 獨立子專案 (WebAssembly Python Subproject)

本子專案為 Webcom AI 控制台與 Chrome 擴充功能提供純前端／瀏覽器端獨立運行的 **Python 3 (WebAssembly / Pyodide)** 運行環境。

---

## 🌟 特色與架構

1. **零本機相依性**：
   - 不依賴本機作業系統是否有安裝 Python 或啟動 Port 8001 Daemon，直接在瀏覽器記憶體中執行 Python 程式碼。
2. **多執行緒 Web Worker**：
   - 提供 `pyodide.worker.js`，將 Python 長時間運算、數學分析與 PCB 資料處理移至獨立背景線程，保證主介面與 WASM 終端機不卡頓。
3. **智慧載入管線**：
   - 優先偵測本地擴充功能包或子專案目錄內的離線 Pyodide 核心檔。
   - 若離線資源不存在，自動無縫回退至 jsDelivr CDN 高速節點。
4. **Chrome 擴充功能 (Manifest V3) 完全相容**：
   - 遵循 `script-src 'self' 'wasm-unsafe-eval'` 安全規範，不使用動態 `eval`，合規載入 WASM 二進位模組。

---

## 📁 目錄結構

```
pyodide/
├── package.json          # 子專案套件設定
├── README.md             # 本說明文件
├── index.js              # 模組入口匯出
├── pyodide_runner.js     # 前端主線程封裝介面
├── pyodide.worker.js     # Web Worker 背景執行線程
├── download_pyodide.py   # 離線核心套件下載器 (可選)
└── dist/                 # 離線靜態資源存放目錄 (執行 download_pyodide.py 後生成)
```

---

## 🚀 離線套件下載 (可選)

若需要在純離線或內部網路中打包擴充功能，可執行：
```bash
python download_pyodide.py
```
將會自動抓取 `pyodide.js`、`pyodide.asm.wasm` 與 `python_stdlib.zip` 至 `dist/` 目錄。
