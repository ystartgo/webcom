# Webcom — Dual-Engine AI Console

> **繁體中文** ・ [English](#english)
>
> 🎯 **當前版本：`v1.0.7-Dual-Engine-WebGPU-RAG-Supervise`** ・ 釋出日期：`2026-09-14`
> 📝 變更紀錄：見下方 [## 🕓 變更日誌 (Changelog)](#-變更日誌-changelog) / [English Changelog](#-changelog)

**Webcom** 是一套單檔 `index.html` 就能啟動的 **雙引擎 AI 主控台**，整合 **多協定終端機（WSL / SSH / Telnet / Web Serial / 後端 Serial）**、**LM Studio / API** 與 **WebGPU 瀏覽器本地 LLM** 兩種推理引擎、**RAG 知識庫管理**、**MCP 協定工具面板**、**純斷網模擬**、**WinPE 開機自動執行** 等常見的現場維運／離線操作需求。

採用 **GNU GPL v3.0** 開源授權（詳見內建手冊第 6 頁「版權 & 致謝」或 [License & Credits 章節](#-license--credits)）。

---

## ✨ 功能亮點

- 🎛️ **三 LLM 引擎 & 混合模式（Co-Think / Supervise）**
  - LM Studio / 任意 OpenAI 相容 API Endpoint
  - ⚡ **WebGPU 純瀏覽器本地推理**（WebLLM MLC：Qwen 2.5 0.5B / 1.5B / 3B、Llama-3.2-1B、SmolLM2-360M）
  - 📦 **ONNX Runtime + Transformers.js 本地推理**（雙後端：💻 CPU SIMD 高效運算 或 ⚡ WebGPU 顯卡加速）
    - 內建 4 模型：Qwen2.5-0.5B (350MB 極速⭐)、Bonsai-1.7B、Qwen3-VL-2B 視覺、Gemma-4-2B (Google)
    - 支援「自訂 HuggingFace onnx-community 模型 ID」手動加載
  - 可切換：「API → WebGPU → ONNX → 雙引擎聯合思考 → 監督排查流水線」共 5 模式
- 🖥️ **左側多模式工作區（終端機 / noVNC 遠端桌面 / Xorg GUI 視窗）**
  - **多協定終端機**（以 [wterm](https://github.com/vercel-labs/wterm) 為基礎的 WASM 終端）
    - 本地 Shell（WSL）
    - SSH / Telnet 遠端登入
    - Web Serial（Chrome/Edge 內建，免驅動免 Daemon，直接操作 COM 埠）
    - 後端 Serial（透過 Daemon 遠端寫入序列埠）
    - 虛擬鍵盤：`Ctrl+A / Ctrl+C / Ctrl+V / Ctrl+X` + 方向鍵
    - **匯出 LOG / 清除畫面**：一次按鈕輸出整段終端機 Log 為 .log 檔 / 清空滾動緩衝
  - 🌐 **noVNC HTML5 遠端桌面**
    - 本地離線打包 `@novnc/novnc` 獨立模組（無外網也能使用）
    - 支援原生 RFB Canvas WebSocket 直連與 Web Iframe 嵌入模式
    - 支援快捷操作：`Ctrl+Alt+Del` 發送、全螢幕切換、快速預設（本機 6080 / VNC 5900 / 區網 6080）
    - 整合後端 `/api/vnc/probe` TCP 探針，即時檢測連接埠狀態
  - 🖼️ **Xorg GUI 虛擬視窗環境（DISPLAY=:0）**
    - 專為 Windows/WSL2 與 Docker 打造之 Linux GUI 視窗整合工作區
    - 支援 1080p / 720p / 4:3 等多種解析度切換與 Fluxbox / XFCE4 / Openbox / Direct App 模式
    - 內建視窗快捷鍵：`Alt+Tab` 切換視窗、`Alt+F4` 關閉視窗
    - 內建 **WSL2 / Linux Xorg 快速啟動精靈**（支援一鍵複製指令與一鍵直發終端機執行 `Xvfb + fluxbox + x11vnc + websockify`）
  - 🔊 **音訊串流支援 (Audio Streaming Support)**
    - 支援 noVNC 與 Xorg 遠端桌面即時音訊播放（相容 PulseAudio / GStreamer / HTTP MP3 / AAC 串流）
    - 工具列內建：一鍵靜音/開啟、音量調整滑桿（0-100%）、自訂串流 URL、Web Audio 鈴聲自我測試 (`playTestTone`)
    - 後端 Daemon 內建 `/api/audio/probe`（連接埠探針）與 `/api/audio/stream`（反向串流代理，防 CORS）
  - ⌨️ **鍵盤快捷鍵與自訂按鍵設置 (Keypad & Shortcuts Config)**
    - 終端機虛擬按鍵支援一鍵開關與自訂巨集按鈕（如 `clear`, `htop`, `ls -la`, `Esc`, `Ctrl+Z`, `Ctrl+L` 等）
    - 遠端桌面支援自訂組合鍵按鈕（如 `Super/Win 標誌鍵`, `Ctrl+Alt+T`, `Ctrl+Esc`, `Alt+Tab`, `Alt+F4` 等）
    - 提供專屬「按鍵設置」對話盒，設定值自動持久化儲存於 `localStorage`，並支援一鍵恢復原廠設定
- 📚 **RAG 知識庫管理員**（Chunk 分段 + 向量索引 + 即時搜尋測試）
  - **支援格式**：`.txt` / `.md` / `.json` / `.pdf` / `.docx` (Word) / `.xlsx` (Excel) / `.pptx` (PowerPoint) / 原始程式碼（`.py/.js/.sh/.bat/.ps1/...`）
  - 可設定 Chunk 大小（預設 512 / 25% overlap），內建「已收錄文件清單 + 分塊數」即時顯示
- 🔧 **MCP 工具面板**：Model Context Protocol Server 設定與發現（內建 MCP Servers 一鍵掃描、探索工具）
- ⚙️ **4 頁系統設定分頁**（Router 設定 / 知識庫管理 / MCP 工具 / 常駐程式）：
  - **Router 設定**：4+ 個 Router Profile（LM Studio / Ollama / OpenRouter / OpenAI），A/B 作用對象分派
  - **知識庫管理**：RAG Chunk 設定 + 上傳 + 分塊數檢視 + 單詞檢索測試
  - **MCP 工具**：MCP Servers 設定 / 掃描 / 瀏覽已就緒工具
  - **常駐程式**：Port 8001 連線狀態 + **一鍵重啟（自動斷開舊進程 + 重啟）** + 查看日誌 + 下載 .bat
- 🩺 **雙模自我檢測工具**（Dual-Mode Self-Diagnostics）：
  - **CLI 自動化檢測**：`diagnose_system.py` 與 `self_test.bat` 一鍵全自動 32 項檢驗（硬體環境、Python 依賴、8001/8002 埠、前後端語法、檔案雜湊一致性）。
  - **瀏覽器視覺化診斷**：頂部導航列 `[🩺 自我檢測]` Modal 視窗，即時檢查 WebGPU、Daemon、MarkItDown 引擎與 API Router 連線狀態。
- 📄 **Microsoft MarkItDown 智慧文件上傳與轉檔**：
  - 對話列右下角精簡為 2 顆核心按鈕（【上傳文件】與【清除對話】）。
  - 上傳 PDF、Word (DOCX)、Excel (XLSX)、PPTX、HTML、CSV、EPUB 時，自動調用後端原生 Microsoft MarkItDown 核心精準提取結構化 Markdown 餵入 LLM，支援萬字長文件智慧分塊與提問。
- 🛜 **純斷網模擬開關**：一鍵封鎖所有非 `127.0.0.1` 外部請求，免拔網路線測試離線情境
- 🖹 **6 頁完整使用手冊**（雙語 zh-TW / EN）：快速上手、終端機協定、AI + RAG、離線 WinPE、常見問題、**版權 & 致謝**
- 🌍 **完整 zh-TW / English 雙語 UI**：頂部語言切換鈕即時生效
- 🪟 **WinPE 自動執行**：`WinPE_Autorun.bat` 掛載 ISO 即可自動啟動 Daemon 並開啟介面

---
<img width="2544" height="1300" alt="image" src="https://github.com/user-attachments/assets/8ccd21ef-c563-417b-8829-d94504a09855" />

## 🧱 目錄結構

```
webcom/
├── index.html                  ← 前端單檔主程式（直接雙擊或經 8001 Daemon 開啟）
├── daemon.py                   ← 後端 FastAPI 常駐服務（預設 port 8001）
├── start_daemon.bat            ← Windows 一鍵啟動 Daemon（自動找 python / 自動安裝依賴）
├── requirements.txt            ← 後端 Python 依賴
├── .gitignore                  ← 忽略模型權重 / wasm / zip / python 內嵌環境
│
├── download_offline_assets.bat ← 下載前端必備資源包（JS/CSS）
├── download_offline_assets.py
├── download_offline_models.bat ← 下載 WebGPU LLM 權重 & WASM 引擎
├── download_offline_models.py
│
├── WinPE_Autorun.bat           ← WinPE 環境自動啟動腳本
├── diagnose_system.py          ← 32 項全方位硬體、相依性與完整性自我檢測工具 (CLI)
├── self_test.bat               ← Windows 一鍵執行系統自我檢測批次檔
├── mcp/
│   └── mcp_servers.json        ← MCP Server 設定
└── assets/                     ← 前端依賴（不含 *.wasm 引擎，見下方說明）
    ├── lucide.min.js / marked.min.js / tailwindcss.js
    ├── webllm.js / webllm.bundle.js
    ├── wterm.js / wterm.bundle.js / wterm.css
```

> ⚠️ **本 GitHub 倉庫 intentionally 不包含 `assets/*.wasm` 與 `/models/**`**（單一 Qwen 3B 權重就超過 5 GB）。請依照下一節指令下載。

---

## 🚀 快速開始

### ① 安裝 Python 後端依賴（使用 Daemon 功能才需要）

```powershell
# Windows PowerShell
pip install -r requirements.txt
```

| 套件 | 用途 |
|---|---|
| FastAPI / Uvicorn | 後端 Daemon（Port 8001）Web 框架與伺服器 |
| Pydantic | 請求 / 回應 schema 驗證 |
| Paramiko | SSH 遠端連線 |
| PySerial | 後端序列埠讀寫（Web Serial 以外的 Agent 模式專用）|

### ② 啟動 Daemon（推薦，可解決 file:// 下 WebGPU Cache 被封鎖的問題）

```powershell
# 方式 A：使用封裝好的 batch（自動偵測 python / 自動重試）
start_daemon.bat

# 方式 B：直接執行
python daemon.py
```

啟動後用瀏覽器打開：  
👉 **<http://127.0.0.1:8001>**

> 如果你不想啟動 Daemon，也可以 **直接雙擊 `index.html`**，但此時：
> - Local Shell / SSH / Telnet / 後端 Serial 無法使用
> - RAG 文件解析會被停用
> - WebGPU 快取行為在部分瀏覽器會被限制，建議仍使用 8001 Daemon 開啟。

### ③ 下載 WebGPU LLM 權重與 WASM 引擎（選用，僅當你要使用「WebGPU 瀏覽器本地」引擎時才需要）

```powershell
# 下載前端資源包（lucide/marked/tailwind/wterm/webllm 等 JS / CSS）
download_offline_assets.bat

# 下載 WebGPU LLM 權重（Qwen / Llama 系列）與對應的 *.wasm 引擎
download_offline_models.bat
```

下載完成後資料夾會長這樣：

```
webcom/
├── assets/
│   ├── Qwen2.5-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm   ← 新增
│   ├── Qwen2.5-1.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm  ← 新增
│   ├── ... (更多 wasm)
│   └── (既有 JS / CSS)
└── models/                                                    ← 新增
    ├── Qwen2.5-0.5B-Instruct-q4f16_1-MLC/
    ├── Qwen2.5-1.5B-Instruct-q4f16_1-MLC/
    ├── Qwen2.5-3B-Instruct-q4f16_1-MLC/
    ├── Llama-3.2-1B-Instruct-q4f16_1-MLC/
    └── SmolLM2-360M-Instruct-q0f16_1-MLC/
```

完成後就能在介面頂部「Engine Mode Select」切換到 `⚡ WebGPU Browser Local` 並選擇模型。

### ④ (選用) 啟用 📦 ONNX Runtime + Transformers.js 本地模型（CPU SIMD / WebGPU 雙後端）

**不需要手動執行 batch 下載**，首次切換 Engine Mode 到 `📦 ONNX 瀏覽器本機` 時會自動：
1. 加載 ONNX Runtime Web + Transformers.js WASM 模組；
2. 從 HuggingFace `onnx-community` 自動下載選取的 ONNX 模型權重（進度條位於輸入列上方，顯示「📦 正在載入 ONNX Runtime 本地模型…」+ 百分比）。

**內建 4 個 ONNX 模型**（隨選即用，推薦標註 ⭐）：

| 模型 | 體積 / 顯卡需求 | 適用場景 |
|------|----------------|---------|
| `onnx-community/Qwen2.5-0.5B-Instruct` | 350 MB ⭐（純 CPU 也流暢） | 一般問答 / 快速初審 / 無獨顯老電腦 |
| `onnx-community/Bonsai-1.7B-ONNX` | 約 1.0 GB（建議 WebGPU）| 複雜推理 / 程式碼修補 |
| `onnx-community/Qwen3-VL-2B-Instruct-ONNX` | 約 1.6 GB（WebGPU 強烈建議）| **圖片 / 截圖 / 故障照片** 視覺診斷（Agent 上傳圖片後啟用） |
| `onnx-community/gemma-4-E2B-it-ONNX` | 約 1.5 GB（WebGPU 建議）| Google 官方模型，程式碼生成 / 除錯品質穩定 |

**📦 ONNX 運算硬體 3 選**（Router 設定 → ONNX 硬體設定下拉）：
- ⚙️ **自動偵測**（預設）：優先 WebGPU，失敗無縫切換到 CPU SIMD
- 💻 **CPU 高性能 SIMD**：無獨立顯卡、或內顯跑 WebGPU 會卡頓時**強烈建議**
- ⚡ **WebGPU 顯卡加速**：需中高階獨立顯卡（RTX / RX / Apple M Pro 以上）

> 💡 **自訂 ONNX 模型**：Router 設定 → 自訂模型分頁 → 切到 📦 ONNX 頁籤 → 輸入 HuggingFace `onnx-community/<model-id>` 即可新增。

### ⑤ (可選 / WSL) 在 WSL 啟動 Daemon 並開通 Port 8001

若你要使用終端機的 **Local Shell (WSL)** 協定，或想把 Daemon 跑在 WSL Linux 環境內，請參閱完整步驟文件：
👉 **[docs/wsl_port_8001.md](docs/wsl_port_8001.md)**（雙語：繁中 + English）

簡易啟動（在 Windows 端雙擊 / 執行）：

```powershell
scripts\start_daemon_wsl.bat            # 自動選預設發行版
scripts\start_daemon_wsl.bat Ubuntu-22.04   # 或指定發行版
```

它會自動：
1. 確認 WSL distro 可執行；
2. 把專案複製到 `~/workspace/webcom/`（原生 Linux FS，比 `/mnt/c` 快 10~30x）；
3. 呼叫 [scripts/start_daemon_wsl.sh](scripts/start_daemon_wsl.sh) 自動找 venv / 裝依賴 / 啟動 `daemon.py` 監聽 `0.0.0.0:8001`；
4. Windows 端一樣能直接開 `http://127.0.0.1:8001`（WSL2 localhost forwarding）。

> 若 Windows 端 `127.0.0.1:8001` 連不到 WSL → 照 [docs/wsl_port_8001.md §4](docs/wsl_port_8001.md#4-遇到問題port-8001-在-windows-端連不到-wsl-) 改用 **mirrored 網路模式**（最穩）或手動 `netsh interface portproxy` 轉送。

---

## 🌐 語系切換

右上角下拉選單可隨時切換：

- 🈶 **繁體中文**（預設）
- 🌐 **English**

包含：所有 Tab 按鈕、6 頁手冊、Daemon 診斷視窗、終端歡迎橫幅、純斷網模擬、連線協定選單、虛擬鍵盤、WebGPU 模型選項、Router 設定、RAG/MCP 面板等。

---

## 🧪 五種引擎模式 (Inference Engine Modes)

在右上角 Engine Mode Select 切換：

| 模式 | 說明 | 需求 |
|---|---|---|
| 🖥️ LM Studio / API | 呼叫任何 OpenAI 相容 Endpoint（需在 Router Settings 設定 profile）| 有 Daemon 或 LM Studio 本機執行中 |
| ⚡ WebGPU 瀏覽器純本機 | 100% 離線，瀏覽器內 WebLLM (MLC) 推理；需先 `download_offline_models.bat` | 需支援 WebGPU 之顯卡 |
| 📦 ONNX 瀏覽器本機 (ONNX Runtime + Transformers.js) | 100% 離線，**雙後端**：💻 CPU 高效 SIMD 或 ⚡ WebGPU 顯卡加速；**首次選模型自動 HuggingFace 下載**；內建 4 模型；可自訂 onnx-community ID | **免 batch 下載**；CPU SIMD 無獨顯也能跑 |
| 🧠 Co-Think（雙引擎聯合思考）| 優先使用 API 強模型，失敗或無連線時自動 fallback 到 WebGPU / ONNX | 至少設定 2 種引擎 |
| 🛡️ Supervise（監督排查模式，4-Stage SRE 流水線）| 雙 LLM 互查 → 偵測問題 → 可執行修補 → 稽核簽核；**最差情境（階段失敗）也一定出 log 報告**。3 種引擎型別 (API / WGPU / ONNX) 自由配對 ≥ 27 種組合 | 任選兩側模型（含 ONNX ↔ ONNX 純本地）|

---

## 🛡️ 監督排查模式：4-Stage SRE 故障排除流水線（v1.0.0 新增）

解決單一 LLM 容易出現的**幻覺指令 / 遺漏風險 / rm -rf 類危險操作 / 逾時卡死**四類常見問題。

### 運作流程
```
使用者提問
   │
   ▼
Stage-A（第一引擎獨立作答） ──► 輸出答案 + 自陳盲點清單
Stage-B（第二引擎獨立作答） ──► 輸出答案 + 自陳盲點清單
   │
   ▼  _stageDiagnostics() 自動產生 diagA / diagB 結構化偵測物件
   │
   ▼
Stage-C（🛠️ Patch Eng 修補工程師）
  ① 🔍 問題偵測（逐項列出，並核對 diagA/diagB 診斷表）
  ② 🔧 可執行修補程式（強制 bash/cmd/powershell fence，禁止空泛文字）
  ③ 🧐 A 盲點稽核（A 自陳盲點的真實性 / 幻覺比例）
  ④ 📋 固定 7 行 Stage-C 診斷報告（問題數 / 修補數 / 信心 / 阻斷級別 / 下一步）
   │
   ▼  (若 Stage-C TIMEOUT / 有效字元 < 100 / 手動停止 → 自動跳過 Stage-D，並附 D Skipped 原因)
   ▼
Stage-D（🛡️ Audit Sign-off 最終稽核 SRE）
  ① Patch 驗證（逐段 VERIFIED✅ / NEEDS-EDIT⚠️ / DANGEROUS❌ 標註）
  ② 殘留風險掃描（P0/P1 風險一定要揭露，禁止隱藏 escalate）
  ③ 🛡️ 固定 5 節最終稽核報告（摘要 / 確認問題 / 已驗證修補 / 殘留風險 / 最終執行方案）
   │
   ▼
Final Summary Card（正式 log 報告）
  📊 4 階段診斷儀表板表格（Status/Tokens/有效字元/截斷原因）
  📌 配對流水線元資訊（Pairing / AnyFail 旗標）
  🔎 Stage-C 修補工程輸出
  🛡️ Stage-D 5 節最終稽核報告（若未執行則顯示 ⚠️ 跳過原因）
  🧭 最終可執行方案

※ 若 A/B **雙方各自獨立回傳 ❗CLARIFY_NEEDED**（bothWantClarify=true），直接觸發「澄清短路」：跳過 Stage-C/D 全部、不跑修補、改輸出 🟡 **待澄清卡片**（自動整合兩側澄清提問，請使用者補充資訊後重送）。
```

### ≥ 27 種配對方式（Side-A / Side-B 獨立選型，3 種 engine kind × 多模型）

不再假設「A=WGPU / B=API」，3 種引擎型別 × 4+ Router Profile × 5+ WGPU Model × 4+ ONNX Model × 2 Role 可自由組合，基礎 3×3=9 種配對 + 模型互換 = **≥ 27 種設定**：

| 選擇器 | 可用類型（3 選 1） |
|--------|------------------|
| Side-A (左側) | 🖥️ API Profile 或 ⚡ WebGPU Model 或 **📦 ONNX Model** |
| Side-B (右側) | 🖥️ API Profile 或 ⚡ WebGPU Model 或 **📦 ONNX Model** |

常見場景推薦（新增 ONNX 系列）：
- `WGPU 0.5B ↔ LM Studio Qwen 14B`：本地快速初審 + 強模型深度審查
- `OpenRouter Claude ↔ OpenAI GPT-4o`：跨廠交叉稽核，單邊降級不影響流程
- `WGPU 3B ↔ WGPU 0.5B`：100% 斷網環境也能跑雙引擎互查
- `API A (不同 Profile) ↔ API B (不同 Profile)`：Router 設定內「作用對象 A/B」切換可強制分派不同 Endpoint
- `📦 ONNX Qwen2.5-0.5B (CPU SIMD) ↔ API GPT-4o`：**無獨顯老電腦**首選，CPU 即可跑 ONNX 小模型初審
- `📦 ONNX Bonsai-1.7B (WebGPU) ↔ WGPU Qwen2.5-3B`：WebGPU 雙 ONNX/WGPU 跨引擎交叉，100% 離線
- `📦 ONNX Qwen3-VL-2B 視覺 ↔ API GPT-4V`：**影像故障排查** 雙模型交叉核對截圖/畫面
- `📦 ONNX Gemma-4-2B ↔ 📦 ONNX Qwen2.5-0.5B`：**100% 純 ONNX 雙引擎互查**（適用 WebLLM/WASM 不相容的特殊瀏覽器）

### 結構化報告範例

**📊 各階段診斷儀表板**（每次流水線自動產生，**最差情境（Stage-C/D 全壞）也會有這張表當 log**）：

| Stage | Status | Tokens | Useful chars | Truncated reason |
|-------|--------|--------|--------------|------------------|
| Stage A (Side-A) | ✅ OK | 412 | 588 | — |
| Stage B (Side-B) | ✅ OK | 520 | 701 | — |
| Stage C (Patch Eng) | ⚠️ TIMEOUT/TRUNCATED | 0 | 22 | watchdog-idle-30s |
| Stage D (Audit) | 🛑 SKIPPED (C failed) | 0 | 0 | stage-c-threw-timeout |

**📋 Stage-C 診斷報告（7 行固定格式）**：
```
📋 Stage-C 診斷報告
====================
偵測到的問題數：   3
已撰寫修補數：     3
修補信心水準：     高 (所有修補均使用官方 apt / systemctl 指令)
阻斷級別：         P1-故障 (SSH server 未啟用導致連線失敗)
下一步動作：       accept-B-apply-patches
若 escalate，1 行提問：—
```

**🛡️ Stage-D 最終稽核報告（5 節固定格式）**：
```
🛡️ 監督排查最終稽核報告
=======================
✅ 執行摘要：部分通過 (3 patches, 2 VERIFIED / 1 NEEDS-EDIT)
🔍 已確認的問題清單：P1-001 (sshd off) / P2-002 (ufw default deny) / P2-003 (apt cache stale)
🔧 已驗證修補：Patch-001 [VERIFIED✅] 最終版 → systemctl enable --now ssh.socket
⚠️ 殘留風險與後續行動：Patch-003 NEEDS-EDIT (換 apt-get 避免 20.04 相容問題，建議手動加 -y 旗標)
🧭 最終執行方案：照 Patch-001 + Patch-002 VERIFIED 版直接執行；Patch-003 等使用者確認 distro 再跑
```

### 12 層卡死 / 逾時防護鏈（stop-timer + watchdog 架構 v26）

針對「WebGPU for-await 卡死 / API SSE 0 token 半死連線 / 停止按鈕按了還跳 idle timer」三類常見問題：

| # | 防護項目 | 門檻 / 行為 |
|---|---------|------------|
| 1 | 新 Stage 卡片建立前，removeAllByStageId 移除同一 stageId 的歷史卡 | 解決「同一 Stage C 同時有 3 張」 |
| 2 | CustomEvent `webcom-stage-killed` → 閉包 `_killedFlag=true` + 立即清 4 timer | 停止按鈕穿透非同步閉包 |
| 3 | WebGPU watchdog setInterval tick = 350ms（原本 700ms） | idle / 0-tok 反應縮半 |
| 4 | Review Stage (C/D) idle 門檻：30s；Independent Stage (A/B)：35s | 不再 idle=38s 仍未截斷 |
| 5 | TIMEOUT/IDLE/WDOG 被中斷時，`webllmEngine = null` 強制 invalidate cache | 解決「第二次重跑一樣卡」 |
| 6 | API observeTimer 每 420ms 掃 body，idle>50s(review)/60s(indep) abort | API 分支也有 idle 防護 |
| 7 | API 分支 0 tokens ≥ 15s 快速 abort（總 timeout 為 200s+ 的 early-exit）| 失效的 OpenRouter key 立即脫離 |
| 8 | `stageTimersRegistry` 全域存 4 timer + 2 reject → `stopOneStage()` 外部直接清/reject | 不用等 finally，idle 立即停跳 |
| 9 | `_onKilledEvt` 閉包內同步清 4 timer + reject + stageAC.abort() | 雙重確保 timer 不再跳 |
| 10 | Loop 內 badge 寫入前檢查 `!_killedFlag && !perStageStopFlags.get(stageId)` | 已停止的卡片不會被 tick 覆蓋回「串流中」 |
| 11 | `awaitStageSettled(stageId, 450ms)` 管線屏障：上一 Stage 的 AC + registry 全清空才出下一張卡 | 解決「A 還在停但 B 已出現」 |
| 12 | finally 區塊雙重清：閉包 timer + `_treg.*` + delete registry 全域 entry | 預防 memory leak 與 ghost tick |

### Per-Stage 獨立操作按鈕

4 張 Stage 卡片 footer 列均有（右→左順序）：
- 🛑 **停止 Stage**：只中止該 Stage，不影響其他（例如 C timeout → 只停 C）
- 🔄 **重試 Stage**：原地重跑同一 Stage，自動移除舊卡片並回填最新結果
- 📋 **複製 Stage Body**：只複製 body 內容，不含 badge 與按鈕

使用者 / assistant 聊天氣泡也各有獨立 🔄 重試 / 📋 複製按鈕。

### 防重複 / 死循環 3 層防護
1. Prompt 規則：回答末尾強制加 `--- END STAGE ---` 標記
2. Stream 規則：`superviseGuards = { maxTokens:1800, endMarker, repeatStreak:4, repeatSim:0.92 }`
3. Chunk 規則：每 chunk 檢查 END marker / 4 行相似 ≥ 0.92 / maxTokens，任一命中立即截斷並附 `⚠️ [防護：...]`

### 第 5 段：CLARIFY 短路（雙方都說不清楚時直接問使用者）

當 Stage-A 與 Stage-B **各自獨立**在輸出尾端寫下 `❗CLARIFY_NEEDED <使用者必須先回答的一或多個封閉式問題>` 時：
- `bothWantClarify=true` 自動成立；
- **Stage-C 修補工程 / Stage-D 稽核**全數跳過（因為前提不足，跑修補只是在製造幻覺）；
- Final Summary Card 改為 **🟡 待澄清卡片**（琥珀色），自動整併兩側的澄清問題成條列，等使用者補充再 rerun。

---

## ⚙️ 四頁系統設定分頁（Router / RAG / MCP / Daemon）

點擊介面下方的 4 個圓角圖示按鈕或對應熱區即可進入：

| 分頁 | 內容 |
|---|---|
| 🛰️ **Router 設定** | 4+ 個 API Router Profile（Local LM Studio / Ollama / OpenRouter / OpenAI / 自訂）；URL / Key / Model 三欄；**作用對象 A/B 分派列**（A 專用 / B 專用 / A+B 同步，Shift+Click = A+B 一次套用）；儲存 / 匯入 / 匯出 JSON；ONNX 硬體加速 3 選下拉；自訂模型三頁籤（API / WebGPU / 📦 ONNX）；測試連線按鈕 |
| 📚 **知識庫管理** | 上傳檔案（txt/md/json/pdf/docx/xlsx/pptx/code）→ 選 Chunk 大小 → 新增並建立索引；文件清單 + 已切分塊數；「檢索」測試單詞查詢即時結果 |
| 🔧 **MCP 工具** | MCP Servers 設定 / 探索工具 / 已就緒工具清單 |
| 🩺 **常駐程式 (Port 8001)** | 目前連線狀態即時指示；**一鍵重啟 / 啟用**（自動 kill 舊 8001 process，再啟 python daemon.py）；查看日誌；下載模型 / 資源包；手動 cmd.exe 啟動指令複製 |

---

## 🛠️ 常見問題 FAQ（Q4/Q5/Q6 新增）

Q1~Q3 請見內建手冊第 5 頁「常見問題」。以下為本次 v1.0.0 新增的 SRE 流水線 / ONNX / WebGPU 進階問題：

**Q4：WebGPU 模式出現「Program terminated with exit(1)」、「MLCEngine exception」或畫面上 D 進度 0% 卡死怎麼辦？**
> 這是 WebGPU 驅動 / 記憶體不足或 MLC WebLLM 舊 instance 被復用的典型症狀。解決三步驟：
> 1. 點對話框右下角 **🛑 停止 Stage**（或上方全域停止按鈕）—— 會自動呼叫 `webllmEngine=null` invalidate cache；
> 2. 切換 Engine Mode 到 `🖥️ LM Studio / API` 再切回 `⚡ WebGPU`，強制卸載舊權重；
> 3. 仍失敗時 **把 WebGPU 模型換成 Qwen2.5-0.5B**（350MB 卡頓率最低），或改使用 **📦 ONNX Qwen2.5-0.5B CPU SIMD**（完全不碰 WebGPU 驅動）。

**Q5：LM Studio 有 tokens 統計但對話框空白、assistant 訊息沒內容？**
> 這是 LM Studio 預設 `stream=true` 的 SSE chunk 沒有正確帶 `content` 欄位。Router 設定 → 對應 Profile 點「測試此節點連線」，若回傳 OK 但 content 空：
> - 在 LM Studio 設定頁面 → 啟用「OpenAI API compatibility mode → Include raw stream payloads」；
> - 或改用 Supervise 模式（任一 Stage 若內容 0 token 超過 15s 會被 0-token-fast-abort 即時中斷，不會等 200s）。

**Q6：切換語系到 English 後 AI 只吐 0 tokens / 空回應？**
> 原因：Supervise Prompt 裡的固定 7 行/5 節報告格式用的是 zh 欄位名，LLM 以為要中文而 prompt 換英文導致不一致。解決：
> - 切到 English 後先按一次 Router 設定的 **儲存設定**（重新載入 i18n 預設 Prompt 版本）；
> - 或 Supervise 模式下送任何一句話前先送 `/reset` 清空 chat（清空 Prompt cache）。

---

## 🕓 變更日誌 (Changelog)

#### `v1.0.7-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-14 **雙向收合佈局、Artifact 工坊介面重構與完整雙語 i18n 釋出 (Layout Optimization, Artifact Drawer & Full i18n Release)**
> 🚀 重大更新：1366×768 (Asus VS229 等緊湊螢幕) 雙向極致收合佈局 ＋ Artifact 工坊頂部導航抽屜化與常駐離開按鈕 ＋ Xorg 工具列整合為直覺式選單 ＋ 補齊全站 54+ 項 UI 按鈕與選單雙語 (zh-TW / en) i18n 支援 ＋ 系統全功能 55 項自我檢測通過。

- **🖥️ 雙向極致收合佈局 (Compact Screen & Collapsible Panels)**：
  1. **左右雙向獨立收合**：左側工作區（終端機/桌面）可向左收合為極窄直條，讓右側 AI 對話區展開至 100% 完整寬度；右側 AI 對話區亦可向右收合，讓左側工作區展開全螢幕操作。
  2. **1366×768 (Asus VS229) 緊湊螢幕最佳化**：即使在標準 1366×768 或小尺寸筆電螢幕下，多欄位、多面板皆能彈性切換，不再擠壓 UI 排版。
  3. **收合條快捷展開指示**：收合後顯示提示直條，支援一鍵即時還原雙欄佈局或快速展開特定功能（終端、noVNC、Xorg、AI 對話、設定）。
- **🎨 Artifact 預覽工坊 (Workbench Drawer) 頂部抽屜化與導航優化**：
  1. **常駐「離開」與「功能 ▾」按鈕**：Artifact 工坊右上方固定常駐「離開 (Esc)」與「功能 ▾」下拉選單，避免窄螢幕時動作按鈕溢出或遮擋關閉鈕。
  2. **多項動作整合入下拉選單**：重新載入沙箱、新視窗開啟、複製全檔、下載檔案、存入應用庫、版本差異比對、LLM 接續輸出等完整收納於功能選單中。
- **🖼️ Xorg 工具列收納與直覺化操作**：
  1. **精簡工具列選單化**：將 Xorg 原有密集的「啟動 App」與「控制設定」工具列重構為「🚀 啟動 App ▾」與「⚙️ 控制與設置 ▾」下拉式選單，釋放寶貴的垂直與水平工作空間。
  2. **快速啟動 Linux GUI 程式**：內建終端機、Thunar 檔案總管、Mousepad 編輯器、計算機與自訂指令輸入，一鍵在 Linux Xorg 視窗中喚醒。
- **🌐 補齊新建按鈕與全站雙語 (zh-TW / en) 翻譯**：
  1. **全面盤點補齊 54+ 項遺漏之 i18n 鍵值**：全面補充收合條提示、頂部工具選單、左側工作區動作選單、MarkItDown 轉換器、終端機/桌面/Xorg 下拉功能、自訂應用庫按鈕與快捷鍵設定之雙語對照。
  2. **動態按鈕選單語言即時聯動**：修正選單在切換語言時即時透過 `t(...)` 翻譯更新，杜絕語系切換後殘留未翻譯字串。
- **🩺 全系統 55 項自我檢測 100% 通過**：
  - `diagnose_system.py` 與 `self_test.bat` 執行 55 項全自動檢驗（WSL 服務探針、前後端語法、檔案 SHA256 雜湊一致性等），全數綠燈通過。

#### `v1.0.6-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-11 **功能整合、自我檢測與跨平台相容性釋出 (Feature & Compatibility Release)**
> 🚀 重大更新：完整整合 Microsoft MarkItDown 本地文件轉換與上傳 ＋ 雙模全自動自我檢測系統 ＋ Windows 批次檔跨機相容性重構 ＋ 介面按鈕精簡與終端機修復

- **📄 完整整合 Microsoft MarkItDown 本地文件轉換中心**：
  1. **右下角文件上傳調用 MarkItDown 轉檔**：對話列右下角精簡為 2 顆核心按鈕（【上傳文件】與【清除對話】）。上傳 PDF、DOCX、XLSX、PPTX、HTML、CSV、EPUB 自動調用 Microsoft MarkItDown 核心提取結構化 Markdown 餵入 LLM，支援長篇文件自動分塊提問。
  2. **零安裝獨立轉檔中心**：獨立打包 1.8MB 完整 Web 應用置於 `webcom/markitdown/`，免裝 Docker、免裝 Node.js、免全域 Python 環境。
  3. **原生轉檔支援**：由 Microsoft MarkItDown 0.1.7 原生核心支援（`/api/convert`），秒級轉換所有主流文件為標準 Markdown。
  4. **頂部導航智慧喚醒**：頁首導航列新增 `[MarkItDown]` 捷徑按鈕，具備「智慧健康探測」，未啟動 8001 後端時自動觸發 `webcom://` 背景靜默拉起，無縫開啟轉檔頁面。
  5. **雙向無縫穿梭**：MarkItDown 頁面頂部常駐「返回 Webcom 主控台」捷徑，流暢切換終端、AI 諮詢與文件轉換任務。
  6. **Service Worker 動態子路徑修正**：補強 `sw.js` 預載機制與 `manifest.json`，精準支援 `/markitdown/` 子目錄代理，杜絕 404 資源錯誤與註冊失敗。
- **🩺 雙模系統自我檢測工具 (Dual-Mode Self-Diagnostics)**：
  1. **CLI 全方位檢測工具 (`diagnose_system.py` / `self_test.bat`)**：全自動 32 項自動化測試，覆蓋系統硬體、Python 依賴套件、8001/8002 埠連線、前後端語法編譯檢查、以及工作區與 github 倉庫檔案一致性。
  2. **前端即時檢測 Modal (`[🩺 自我檢測]`)**：點擊頂部導航列即可彈出視覺化自我診斷面板，即時探測 WebGPU 支援、Daemon 狀態、MarkItDown 引擎可用性與 API Router 狀態。
- **🩹 介面按鈕優化、終端機初始化與常駐程式檢測燈號修復**：
  1. **按鈕觸發機制防護**：修正上傳與工具列按鈕的原生觸發與點擊穿透，避免合成事件遭到攔截。
  2. **常駐程式指示燈**：修正 Daemon 連線狀態即時輪詢與視覺化狀態燈號邏輯。
  3. **WTerm 終端機初始化修復**：修正終端機在部分瀏覽器環境中初始載入與視窗大小計算異常。
- **🛡️ Windows 跨機批次檔啟動器重構（純 ASCII ＋ 嚴格 CRLF）**：
  1. **徹底解決 cmd.exe 緩衝區位元偏移崩潰**：根除因 Unix LF 換行搭配全形破折號等多位元組字元引發的 cmd 區塊讀取位移（導致 `REM` 變 `'M'`、`setlocal` 變 `'tlocal'`、`cd /d` 變 `'/d'`）。
  2. **配置 `.gitattributes`**：強制所有 `*.bat`、`*.cmd`、`*.vbs`、`*.ps1`、`*.reg` 採用 `eol=crlf`，防範 git clone 時換行符號跑位。
  3. **四層環境智慧探測與扁平化架構**：以純 ASCII 與扁平 `goto` 架構重寫 `start_daemon.bat`，**優先使用根目錄 `%~dp0python\python.exe` 綠色便攜環境**（無 Python 環境之新電腦也能直接執行），依序 fallback `uv`、系統 `python`、`py -3`。
  4. **全自動 URL 協議註冊**：啟動時自動在 `HKCU` 註冊 `webcom://` 協定（免管理員權限），賦予瀏覽器按鈕直接喚醒後端之能力。
- **⚖️ 開源版權與致謝補齊**：於雙語手冊、關於抽屜與 `README.md` 完整補充 Microsoft MarkItDown 與 GoneTone/markitdown-website 開源授權聲明。
- **🧾 全面升級版本號 v1.0.5 → v1.0.6**：同步更新 `index.html` 內全數 11 處版號標記、雙語手冊操作指引、版權致謝與雙語 `README.md`。

### `v1.0.5-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-11 **版本升級維護釋出 (Maintenance)**
> 🔖 版本凍結標記：v1.0.4 所有 daemon.py / webcom:// / silent_daemon 修正通過穩定性驗證，正式升版
- **🧾 版號全面升級 v1.0.4 → v1.0.5**：`index.html` 內 10 處版本字串（Meta/Title/Badge/Footer/雙語手冊/ANSI 歡迎詞/JSON Demo）、`README.md` 雙語 Banner 與 Changelog 標題全部統一為 `v1.0.5`
- **🧪 v1.0.4 三項穩定性修正標記 STABLE**：
  1. daemon.py 自動釋放 8001 埠 + pythonw stdout/stderr 重導向 → **STABLE**
  2. `webcom://` 協定 `<a>.click()` 繞過 CSP iframe 封鎖 → **STABLE**
  3. `silent_daemon.vbs` wscript 完全背景無黑窗 → **STABLE**
- **📄 文件補齊**：雙語 Changelog 新增 v1.0.5 維護釋出章節

### `v1.0.4-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-09 **修正釋出 (Bugfix)**
> 🐛 修復 v1.0.3 回報的 3 項穩定性問題 + 2 項檔案同步
- **🩹 daemon.py 4 處修復（8001 埠佔用 + 靜默啟動 + pythonw 崩潰）**：
  1. 啟動前自動偵測 `127.0.0.1:8001 LISTEN` → 非自身 PID 就 `psutil.kill()` 舊進程（解決「Daemon 一鍵重啟失敗/Address already in use」）
  2. `delayed_exit()` 0.5s→0.3s + 寫 `.stop_daemon` 停止旗標檔 + 父程序 cmd.exe 也一併結束（解決關閉時留下殭屍 cmd 黑窗）
  3. `pythonw.exe` / 無視窗服務模式 `sys.stdout/sys.stderr is None` 時自動重導向到 `daemon.log`（解決 Windows 排程/靜默啟動時 stderr 丟失造成崩潰）
  4. 工作目錄保險：啟動開頭強制 `os.chdir(__file__)` + `sys.path.insert(0, __dir__)`（解決從不同 CWD 啟動 import 失敗）
- **🩹 `webcom://` 協定改為 `<a>.click()` 而非 `iframe.src`**：Edge/Chromium 新版 CSP 安全機制會阻止 iframe 載入 custom protocol（3000ms 閃退）；改 `<a href="webcom://…">` + `.click()` + 2000ms 後移除，支援 Chrome/Edge/Firefox
- **🩹 下載註冊 regbat → 改 wscript `silent_daemon.vbs` 靜默啟動**：原本 `regbat` 直接 `start_daemon.bat` 會彈 cmd 黑窗；改為 `HKCU\…\webcom\shell\open\command = wscript.exe silent_daemon.vbs %1`，**完全背景執行、無干擾、無黑窗**
- **📦 同步檔案**：`assets/webllm.bundle.js`（WebGPU 載入期間 callback 優先級調整，78 bytes 差異）
- **📄 文件**：雙語 Changelog 補 v1.0.4 修正明細 + 頂部 banner 版號 v1.0.3→v1.0.4

### `v1.0.3-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-09
- **文件一致化維護釋出**（程式碼主體與 v1.0.2 功能相同，版本升級用於標記以下穩定凍結點）：
  - 🛡️ Supervise SRE 4-Stage 流水線 12 層卡死防護鏈 + stop-timer v26 → 標記 **STABLE**
  - 📦 ONNX Runtime 4 模型文件 / 3 選硬體加速 / 首次 HuggingFace 自動抓檔 → 標記 **STABLE**
  - FAQ Q4/Q5/Q6（WebGPU exit1 / LM SSE 空 payload / 語系切換 0-token）解法與文件標記穩定
  - 「四頁系統設定分頁」表格 / 「RAG PDF/Word/Excel/PPT 格式清單」/「終端機 匯出 LOG / 清除畫面」文件同步
  - 內建手冊 4 處 License & Credits 頁籤版號、Footer Brand、ANSI 終端歡迎詞、JSON Demo payload **全部版號一致（v1.0.3）**
  - 修復 v1.0.2 README 英文 Supervise § 多餘尾空白與 zh/en Changelog 行寬對齊

### `v1.0.2-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-09
- **🛡️ Supervise 模式升級為 SRE 故障排除流水線**（diag-1~4 完成）：
  - Stage-C（修補工程師）強制 4 步驟：問題偵測 → 可執行 bash/cmd fence 修補 → A 盲點稽核 → 📋 固定 7 行診斷報告
  - Stage-D（稽核 SRE）強制 3 步驟：Patch VERIFIED✅/NEEDS-EDIT⚠️/DANGEROUS❌ 逐段標註 → 殘留風險 → 🛡️ 5 節最終稽核報告
  - Final Summary 強制擺 📊 A/B/C/D 全階段診斷表格（最差情境也有 log 報告，不會空白）
  - CLARIFY_NEEDED 雙方短路：A/B 都說要問使用者 → 直接出 🟡 琥珀色待澄清卡，C/D 全跳
- **stop-timer v26 12 層卡死防護鏈**：stageTimersRegistry + CustomEvent 穿透閉包 + settle 屏障 450ms + skip-D 閘（C TIMEOUT 時 D 絕不出現）
- **Per-Stage 獨立 3 按鈕 footer**：🛑 停止 / 🔄 重試 / 📋 複製 body；user/assistant 氣泡也加 retry-copy
- **ux 1/2/3 修補**：D 進度可視 tok@t/s + idle 秒數；footer DOM 流按鈕不再壓對話；chat-box 底部 88px 預留高度
- **📦 ONNX Runtime + Transformers.js 文件化**：4 內建模型表 / CPU SIMD vs WebGPU 3 選硬體加速 / 首次啟動 HuggingFace 自動抓檔 / 自訂 onnx-community ID
- **配對 ≥ 27 種**：api / webgpu / onnx 3 種 engine kind × Side-A/B 自由組合，新增 ONNX↔ONNX 純本地、Qwen3-VL↔GPT-4V 視覺交叉等 4 場景
- **文件補齊**：新增「四頁系統設定分頁」表格、FAQ Q4/Q5/Q6（WebGPU exit1 / LM SSE 空 payload / 語系切換 token=0）、RAG PDF/Word/Excel/PPT 格式清單、終端機「匯出 LOG / 清除畫面」
- **stuckD 根因修復**：WebGPU for-await 忽略 AbortSignal → chunks.return() + webllmEngine=null invalidate cache；0-tokens 15s fast abort；API idle watchdog

### `v1.0.1-Dual-Engine-WebGPU-RAG` — 2026-08-30
- 新增 **🛡️ Supervise Mode** 初版（Side-A/B 雙 LLM 4-Stage 流水線）
- 新增 **Co-Think** 聯合思考混合模式
- 修正 qc Row-1 排序（flex-nowrap + inline order 修復 Tailwind order class 失效）
- 修正 rd API↔API 自動分派不同 Profile（ensureAltProfileDistinct + Modal 作用對象 A/B 切換列）
- 修正 qa 視覺左右順序：A 永遠左 922px / B 永遠右
- 修正 qb 切換 engineMode 後版面刷新（dualEngineSubMode 重置 + isSupervise 單一判斷）
- 新增 de-nest 6 處巢狀 template literal，V8 parser 11/11 OK
- 新增 ph Row-1 控制項搬移到 Router 右側、4 toggle 到 Row-2
- 3 層防重複死循環 guard：END marker + maxTokens 1800 + 4-line sim≥0.92

### `v1.0.0-Dual-Engine-WebGPU-RAG` — 2026-08-29
- 初始公開版本：單檔 index.html 雙引擎主控台
- 多協定終端機（WSL/SSH/Telnet/Web Serial/後端 Serial + 虛擬鍵盤）
- LM Studio/API Router 設定（多 Profile + 匯入匯出 JSON）
- WebGPU 5 模型 + ONNX 4 模型本地推理（雙後端 CPU/WebGPU）
- RAG 知識庫：Chunk 分段 + 向量索引 + 即時檢索測試
- MCP 工具面板 + WinPE 自動執行 batch + 純斷網模擬開關
- 內建 6 頁 zh-TW / English 雙語使用手冊

---

## 📜 License / 授權

- **整體專案**：GNU GPL v3.0 （本軟體開源可修改，所有商業或衍生腳本 **必須保留此版權聲明與 GPLv3**）
- **第三方套件致謝清單**（請見程式內 **⚖️ 版權 & 致謝** 頁，所有套件各自保留原授權）：
  - **前端 (Frontend)**：
    - [wterm](https://github.com/vercel-labs/wterm) (Vercel Labs, Apache 2.0) — 瀏覽器 DOM + WASM 終端模擬器
    - [@mlc-ai/web-llm](https://github.com/mlc-ai/web-llm) (MLC AI, Apache 2.0) — 瀏覽器 WebGPU 本機推論引擎
    - [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) (Tailwind Labs, MIT) — Utility-First CSS 框架
    - [Lucide Icons](https://github.com/lucide-icons/lucide) (Lucide Contributors, ISC) — 開源 SVG 圖示庫
    - [marked.js](https://github.com/markedjs/marked) (markedjs, MIT) — Markdown 解析與渲染
    - [markitdown-website](https://github.com/GoneTone/markitdown-website) (GoneTone, MIT) — 線上文件轉 Markdown Web 應用 (雙欄預覽、批次轉換、ZIP 打包)
  - **後端 (Backend · Python)**：
    - [FastAPI](https://github.com/fastapi/fastapi) (Sebastián Ramírez, MIT) — 高效能 Python Web API 框架
    - [uvicorn](https://github.com/encode/uvicorn) (Encode, BSD 3-Clause) — ASGI 超高速 HTTP 伺服器
    - [Paramiko](https://github.com/paramiko/paramiko) (Jeff Forcier et al., LGPL 2.1) — Python SSH2 通訊協定實作
    - [pyserial](https://github.com/pyserial/pyserial) (Chris Liechti, BSD 3-Clause) — Python 串口 (COM / UART) 通訊
    - [markitdown](https://github.com/microsoft/markitdown) (Microsoft, MIT) — 全能多格式文件轉 Markdown 核心引擎 (PDF/Office/HTML/CSV)

---

---

<a id="english"></a>
# Webcom — Dual-Engine AI Console (English)

> 🎯 **Current Release:** `v1.0.7-Dual-Engine-WebGPU-RAG-Supervise` ・ **Released:** `2026-09-14`
> 📝 **Changelog:** [Jump to Changelog ↓](#-changelog)

**Webcom** is a single-file (`index.html`) **Dual-Engine AI Console** that combines a **multi-protocol terminal (WSL / SSH / Telnet / Web Serial / Backend Serial)**, **LM Studio / API** and **WebGPU browser-local LLM** inference engines, **RAG Knowledge Base**, **MCP tool panel**, **pure-offline simulation switch**, and **WinPE autorun** for real-world on-site / offline ops.

Licensed under **GNU GPL v3.0**. See the built-in User Guide tab 6 *License & Credits* or the [License & Credits section](#-license--credits) below for full third-party acknowledgements.

---

## ✨ Highlights

- 🎛️ **Triple LLM Engine & Hybrid Modes (Co-Think / Supervised-Mutual-Debug)**
  - LM Studio / any OpenAI-compatible API endpoint
  - ⚡ **WebGPU browser-local inference** (WebLLM MLC: Qwen 2.5 0.5B / 1.5B / 3B, Llama-3.2-1B, SmolLM2-360M)
  - 📦 **ONNX Runtime + Transformers.js browser-local inference** (dual backends: 💻 CPU High-Perf SIMD OR ⚡ WebGPU GPU acceleration)
    - 4 built-in models: Qwen2.5-0.5B (350 MB ultra-fast ⭐), Bonsai-1.7B, Qwen3-VL-2B (Vision), Gemma-4-2B (Google)
    - "Custom HuggingFace onnx-community model ID" tab for user-added models
  - 5 selectable top-level modes: `API → WebGPU → ONNX → Co-Think (hybrid) → Supervised-Mutual-Debug (4-Stage SRE Pipeline)`
- 🖥️ **Left Multi-Mode Workspace (Terminal / noVNC Remote Desktop / Xorg GUI Display)**
  - **Multi-Protocol Terminal** (WASM, powered by [wterm](https://github.com/vercel-labs/wterm))
    - Local Shell via WSL
    - SSH / Telnet remote login
    - **Web Serial** (Chrome/Edge built-in — no driver, no daemon, direct COM/UART control)
    - Backend Serial (serial ports routed through port-8001 Daemon for AI Agent mode)
    - Virtual keypad: `Ctrl+A / Ctrl+C / Ctrl+V / Ctrl+X` + arrow keys
    - **Export Log / Clear Buffer**: one-click export the entire terminal scrollback as `.log` / reset scrollback
  - 🌐 **noVNC HTML5 Remote Desktop**
    - Bundled `@novnc/novnc` self-contained offline ES module
    - Supports native RFB Canvas WebSocket direct connection & Web Iframe embed modes
    - Key actions: `Ctrl+Alt+Del` trigger, Fullscreen toggle, quick presets (Local 6080 / VNC 5900 / LAN 6080)
    - Integrated with backend `/api/vnc/probe` TCP probe for instant port diagnostics
  - 🖼️ **Xorg GUI Display Environment (DISPLAY=:0)**
    - Designed for seamless Linux GUI applications inside Windows/WSL2 and Docker
    - Supports 1080p / 720p / 4:3 resolutions and Fluxbox / XFCE4 / Openbox / Direct App modes
    - Window shortcuts: `Alt+Tab` window switcher, `Alt+F4` close window
    - Built-in **WSL2 / Linux Xorg Quick Launch Wizard** (one-click command copy & direct dispatch to WSL terminal)
- 📚 **RAG Knowledge Base Manager** (chunked indexing + live search test)
  - **Supported formats**: `.txt` / `.md` / `.json` / **`.pdf`** / **`.docx` (Word)** / **`.xlsx` (Excel)** / **`.pptx` (PowerPoint)** / raw source code (`.py/.js/.sh/.bat/.ps1/…`)
  - Configurable chunk size (default 512, 25% overlap) with live "ingested files + chunk count" indicator
- 🔧 **MCP Tools Panel**: Model Context Protocol server configuration + discovery (one-click scan for registered MCP servers / explore tools)
- ⚙️ **4 System Settings tabs** (Router / Knowledge Base / MCP Tools / Daemon):
  - **🛰️ Router**: 4+ API Router Profiles (LM Studio / Ollama / OpenRouter / OpenAI + Custom); Target-slot A/B assignment row (A-only / B-only / A+B sync, Shift+Click = A+B simultaneously); Save / Import / Export JSON; ONNX hardware 3-pick dropdown; Custom Models 3-sub-tabs (API / WebGPU / 📦 ONNX); Test Connection button
  - **📚 Knowledge Base**: file upload → chunk size pick → index build; files list with chunk count; live query retrieval test
  - **🔧 MCP Tools**: MCP Servers config / scan / list-ready-tools
  - **🩺 Daemon (Port 8001)**: live health indicator; **1-click restart/enable** (auto-kill stale :8001 process, relaunch `daemon.py`); View Logs; Download Models / Assets bundle; copy-paste manual `cmd.exe` launcher
- 🛜 **Simulated Offline Mode toggle**: one-click block ALL non-`127.0.0.1` traffic; test offline scenarios without unplugging cables
- 🖹 **6-page User Guide** (bilingual zh-TW / EN): Quick Start, Terminal Protocols, AI+RAG, Offline & WinPE, **FAQ**, **License & Credits**
- 🌍 **Full zh-TW ↔ English bilingual UI** — live switch from the top bar
- 🪟 **WinPE Autorun**: `WinPE_Autorun.bat` starts the Daemon & launches UI automatically when the ISO boots

---
<img width="2551" height="1302" alt="image" src="https://github.com/user-attachments/assets/6a82b437-c9d2-4238-807f-f26e54d920bd" />


## 🧱 Repository Layout

```
webcom/
├── index.html                  ← Frontend single-file app (open directly or via :8001 daemon)
├── daemon.py                   ← Backend FastAPI daemon (default port 8001)
├── start_daemon.bat            ← Windows one-click daemon starter (auto python, auto deps)
├── requirements.txt            ← Python deps
├── .gitignore                  ← ignores model weights / wasm / zip / embedded python
│
├── download_offline_assets.bat ← download required frontend JS/CSS bundle
├── download_offline_assets.py
├── download_offline_models.bat ← download WebGPU LLM weights + *.wasm engines
├── download_offline_models.py
│
├── WinPE_Autorun.bat           ← WinPE autorun script
├── mcp/mcp_servers.json        ← MCP server definitions
└── assets/                     ← frontend deps (NO *.wasm engines — see below)
    ├── lucide.min.js / marked.min.js / tailwindcss.js
    ├── webllm.js / webllm.bundle.js
    └── wterm.bundle.js / wterm.css
```

> ⚠️ **This GitHub repo intentionally does NOT ship `assets/*.wasm` or `/models/**`** (a single Qwen 3B shard alone exceeds 5 GB). Follow the commands below to obtain them on-demand.

---

## 🚀 Quick Start

### ① Install backend Python deps (only required to use Daemon features)

```powershell
pip install -r requirements.txt
```

| Package | Purpose |
|---|---|
| FastAPI / Uvicorn | Port-8001 daemon web framework + ASGI server |
| Pydantic | Request / response schema validation |
| Paramiko | SSH remote connectivity |
| PySerial | Backend serial-port R/W (for AI Agent mode outside Web Serial scope) |

### ② Start the Daemon (recommended — avoids WebGPU Cache API restrictions under `file://`)

```powershell
# Option A — wrapped batch (auto-detects python, auto-retry on port conflicts)
start_daemon.bat

# Option B — direct execution
python daemon.py
```

Then open in your browser:
👉 **<http://127.0.0.1:8001>**

> You CAN also just double-click `index.html` to open under `file://`, but then:
> - Local Shell / SSH / Telnet / Backend Serial are disabled
> - RAG document parsing is disabled
> - WebGPU caching may be restricted in some browsers — so opening via the :8001 daemon is still recommended.

### ③ Download WebGPU LLM weights + WASM engines (optional — only required if you use `WebGPU Browser Local` mode)

```powershell
# Get required frontend JS/CSS bundle (lucide / marked / tailwind / wterm / webllm ...)
download_offline_assets.bat

# Get WebGPU LLM weights (Qwen / Llama series) + matching *.wasm engines
download_offline_models.bat
```

Your folder will then contain:

```
webcom/
├── assets/
│   ├── Qwen2.5-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm   ← added
│   ├── ... (more wasm engines)
│   └── (existing JS/CSS)
└── models/                                                    ← added
    ├── Qwen2.5-{0.5B,1.5B,3B}-Instruct-q4f16_1-MLC/
    ├── Llama-3.2-1B-Instruct-q4f16_1-MLC/
    └── SmolLM2-360M-Instruct-q0f16_1-MLC/
```

After that switch the top-bar **Engine Mode Select** to `⚡ WebGPU Browser Local` and pick your model.

### ④ (Optional) Enable 📦 ONNX Runtime + Transformers.js local models (dual backend: 💻 CPU SIMD / ⚡ WebGPU)

**No manual batch download required** — the first time you flip **Engine Mode Select** → `📦 ONNX Browser Local (ONNX Runtime)` it auto:
1. loads the ONNX Runtime Web + Transformers.js WASM modules;
2. downloads the selected ONNX weights directly from HuggingFace `onnx-community` (progress bar appears above the user input row: "📦 Initializing ONNX Runtime & Model… %").

**4 built-in ONNX models** (ready-to-pick, ⭐ = recommended default):

| Model ID (onnx-community/…) | Size / GPU req. | Typical use |
|---|---|---|
| Qwen2.5-0.5B-Instruct | 350 MB ⭐ (CPU-friendly, smooth on iGPU only) | General chat / quick triage / legacy PCs without discrete GPU |
| Bonsai-1.7B-ONNX | ~1.0 GB (WebGPU recommended) | Complex reasoning / code patching |
| Qwen3-VL-2B-Instruct-ONNX | ~1.6 GB (WebGPU **strongly** recommended) | **Image / screenshot / fault-photo visual diagnostics** (after Agent uploads a picture) |
| gemma-4-E2B-it-ONNX | ~1.5 GB (WebGPU recommended) | Google official — stable code generation / debugging quality |

**📦 ONNX Hardware Acceleration — 3 options** (Router Settings → "ONNX Hardware" dropdown):
- ⚙️ **Auto Detect** (default) → WebGPU first, seamless fallback to CPU SIMD
- 💻 **CPU High-Perf SIMD** → **Strongly recommended** on iGPU-only laptops / PCs that stutter under WebGPU
- ⚡ **WebGPU GPU Acceleration** → needs mid/high-end discrete GPU (RTX / RX / Apple M Pro class)

> 💡 **Custom ONNX models**: Router Settings → *Custom Models* tab → flip to the 📦 ONNX sub-tab → paste any HuggingFace `onnx-community/<model-id>`.

### ⑤ (Optional / WSL) Run the daemon inside WSL + reach Port 8001 on Windows

If you plan to use the **Local Shell (WSL)** terminal protocol, or just prefer running the FastAPI daemon on Linux, follow the full guide:
👉 **[docs/wsl_port_8001.md](docs/wsl_port_8001.md)** (bilingual: English + 繁體中文)

One-click launch (directly from Windows — double-click or run from PowerShell):

```powershell
scripts\start_daemon_wsl.bat                    # uses your default WSL distro
scripts\start_daemon_wsl.bat Ubuntu-22.04       # or pass an explicit distro name
```

It automatically:
1. verifies the WSL distro boots;
2. copies the project to `~/workspace/webcom/` (native Linux FS — 10~30× faster than `/mnt/c`);
3. calls [scripts/start_daemon_wsl.sh](scripts/start_daemon_wsl.sh) which locates the venv / installs deps / launches `daemon.py` listening on `0.0.0.0:8001`;
4. keeps Windows `http://127.0.0.1:8001` accessible via WSL2 localhost forwarding.

> If your browser on Windows can't reach `127.0.0.1:8001`, follow [§4 of the WSL guide](docs/wsl_port_8001.md#4-troubleshooting-windows-cant-reach-1270018001-inside-wsl) → enable **mirrored networking** (most reliable), or set up a manual `netsh interface portproxy` forward.

---

## 🌍 Language Switch

Top-right picker, live-reload:

- 🈶 **繁體中文** (default)
- 🌐 **English**

Covers all tab buttons, 6-page guide, Daemon diagnostics, terminal banner, offline-mock, protocol selector, virtual keypad, WebGPU model options, router settings, RAG & MCP panels, etc.

---

## 🧪 Three Engine Modes

Use the top-right **Engine Mode Select**:

| Mode | What it does | Requirements |
|---|---|---|
| 🖥️ LM Studio / API Mode | Calls any OpenAI-compatible endpoint (configure a Router Profile first) | Daemon running or a local LM Studio instance |
| ⚡ WebGPU Browser Local | 100% offline. In-browser inference via WebLLM (MLC) | Run `download_offline_models.bat` first; WebGPU-capable GPU |
| 📦 ONNX Browser Local | 100% offline. In-browser inference via **ONNX Runtime + Transformers.js** — dual backends: **💻 CPU SIMD** or **⚡ WebGPU** | No batch download needed; first load auto-fetches 4 built-in ONNX models from HuggingFace onnx-community |
| 🧠 Co-Think (hybrid) | Tries the primary strong-model endpoint first, falls back to WebGPU/ONNX automatically | At least two engines configured |
| 🛡️ Supervised-Mutual-Debug (4-Stage SRE Pipeline) | Dual-LLM cross review → Detect failures → Produce executable patches → Audit sign-off. **Logs & structured reports always generated, even when stages fail** | Any 2 models picked from 3 engine kinds: API ↔ API / WGPU ↔ API / WGPU ↔ WGPU / **ONNX ↔ API / ONNX ↔ WGPU / ONNX ↔ ONNX** |

---

## 🛡️ Supervised Mutual-Debug Mode: 4-Stage SRE Troubleshooting Pipeline (v1.0.0 added)

Solves 4 common single-LLM failure classes: **hallucinated commands, missed P0/P1 risks, dangerous destructive ops (rm -rf), and timeouts/stuck iterators**.

### Pipeline Flow
```
User query
  │
  ▼
Stage-A (Engine-A independent answer) ──► output + self-reported blind spots
Stage-B (Engine-B independent answer) ──► output + self-reported blind spots
  │
  ▼  _stageDiagnostics() auto-generates structured diagA / diagB
  │
  ▼
Stage-C (🛠️ Patch Engineer — always runs)
  ① 🔍 Issue detection (maps against diagA/diagB table)
  ② 🔧 Executable patches (MUST be `bash / cmd / powershell` fenced code; NEVER empty prose)
  ③ 🧐 Blind-spot audit of Stage-A claims (real issues vs. hallucinations)
  ④ 📋 Fixed 7-line Stage-C diagnostic report
  │
  ▼  (If Stage-C TIMEOUT / useful chars < 100 / manual stop → Stage-D SKIPPED with reason logged)
  ▼
Stage-D (🛡️ Audit Sign-off SRE)
  ① Patch verification, line-by-line:  VERIFIED✅ / NEEDS-EDIT⚠️ / DANGEROUS❌
  ② Residual-risk scan (P0/P1 MUST be disclosed — silent escalate is forbidden)
  ③ 🛡️ Fixed 5-section Final Audit Report
  │
  ▼
Final Summary Card (official log report — ALWAYS produced)
  📊 4-stage diagnostics table (Status / Tokens / Useful chars / Truncation reason)
  📌 Pipeline metadata (Pairing config · AnyFail flag)
  🔎 Stage-C Patch Engineering output (full)
  🛡️ Stage-D 5-section Audit (or ⚠️ D-skipped reason)
  🧭 Final executable plan (priority: D's plan → C's patches → B's original answer)

※ If **BOTH sides independently emit `❗CLARIFY_NEEDED`** → `bothWantClarify = true` short-circuit triggers: Stage-C/D are SKIPPED entirely, Final card becomes an 🟡 **Amber Clarify Card** that merges the two sides' questions and asks the user to answer before the pipeline re-runs.
```

### ≥ 27 Pairing Configurations (Side-A / Side-B Independent Selectors — 3 engine kinds × multi-model)

No hardcoded "A=WGPU / B=API" assumption. 3 engine kinds × 4+ Router profiles × 5+ WGPU models × 4+ ONNX models × 2 roles freely combinable: **9 base pairings × model swaps = ≥ 27 configurations**.

| Selector | Available Types (pick 1 of 3) |
|----------|--------------------------------|
| Side-A (left)  | 🖥️ API Profile OR ⚡ WebGPU Model OR **📦 ONNX Model** |
| Side-B (right) | 🖥️ API Profile OR ⚡ WebGPU Model OR **📦 ONNX Model** |

Recommended scenarios (new ONNX set added):
- `WGPU 0.5B ↔ LM Studio Qwen 14B` — fast local triage + strong deep-audit model
- `OpenRouter Claude ↔ OpenAI GPT-4o` — cross-vendor audit; single-vendor outage degrades gracefully
- `WGPU 3B ↔ WGPU 0.5B` — 100% offline dual-engine mutual review
- `API A (Profile X) ↔ API B (Profile Y)` — force-distinct endpoints via Router Modal **Target slot (A-only / B-only / A+B sync)** row (Shift+Click = A+B simultaneously)
- `📦 ONNX Qwen2.5-0.5B (CPU SIMD) ↔ API GPT-4o` — **non-discrete-GPU legacy PCs**, CPU-only ONNX lightweight triage works out of the box
- `📦 ONNX Bonsai-1.7B (WebGPU) ↔ WGPU Qwen2.5-3B` — cross-engine ONNX/WebGPU mutual audit, 100% offline
- `📦 ONNX Qwen3-VL-2B (Vision) ↔ API GPT-4V` — **visual/photo troubleshooting** (paste screenshots) dual-model cross-verify
- `📦 ONNX Gemma-4-2B ↔ 📦 ONNX Qwen2.5-0.5B` — **100% pure-ONNX dual-engine audit** (for locked-down browsers where WebLLM/WASM load is blocked)

### Structured Report Snippets

**📊 Per-Stage Diagnostics Dashboard** (auto-generated **every run** — guaranteed log even under worst-case C/D total failure):

| Stage | Status | Tokens | Useful chars | Truncated reason |
|-------|--------|--------|--------------|------------------|
| Stage A (Side-A) | ✅ OK | 412 | 588 | — |
| Stage B (Side-B) | ✅ OK | 520 | 701 | — |
| Stage C (Patch Eng) | ⚠️ TIMEOUT/TRUNCATED | 0 | 22 | watchdog-idle-30s |
| Stage D (Audit) | 🛑 SKIPPED (C failed) | 0 | 0 | stage-c-threw-timeout |

**📋 Stage-C Diagnostic Report (7 lines fixed)**:
```
📋 Stage-C Diagnostic Report
============================
Issues detected:            3
Patches authored:           3
Patch confidence:           HIGH (all use official apt/systemctl verbs)
Severity blocker level:     P1-DEGRADED (SSH server socket disabled)
Recommended next action:    accept-B-apply-patches
Escalate 1-line question:   —
```

**🛡️ Stage-D Final Audit Report (5 sections fixed)**:
```
🛡️ Final Audit Report (Supervised Mutual Debug)
================================================
✅ Executive summary:   PARTIALLY PASSED (3 patches · 2 VERIFIED✅ / 1 NEEDS-EDIT⚠️)
🔍 Confirmed issues:    P1-001 (sshd off) · P2-002 (ufw default deny) · P2-003 (apt cache stale)
🔧 Verified patches:    Patch-001 [VERIFIED✅] final → systemctl enable --now ssh.socket
⚠️ Residual risks:      Patch-003 NEEDS-EDIT (apt → apt-get for 20.04 compat; add -y non-interactive)
🧭 Final executable plan:  Execute Patch-001 + Patch-002 VERIFIED now; hold Patch-003 until distro confirmed
```

### 12-Layer Timeout / Stuck-Iterator Kill Chain (stop-timer + watchdog v26)

Targets: **WebGPU for-await iterator ignores AbortSignal · API SSE 0-token half-dead conn · stop btn pressed but idle tick still jumps**

| # | Guard | Threshold / Behaviour |
|---|-------|----------------------|
| 1 | removeAllByStageId BEFORE new card mount | Eliminates "3 identical Stage-C cards rendered concurrently" |
| 2 | CustomEvent `webcom-stage-killed` → closure `_killedFlag=true` + 4 timers cleared INSTANTLY | Crosses async-closure boundary that AbortSignal alone can't reach |
| 3 | WebGPU watchdog tick: 350 ms (prev 700 ms) | idle/0-tok reaction time halved |
| 4 | Review-stage (C/D) idle: 30 s · Independent-stage (A/B) idle: 35 s | Abort BEFORE user sees 38 s+ idle |
| 5 | On TIMEOUT/IDLE/WDOG → `webllmEngine = null` (invalidate cached engine instance) | Fixes "first run stuck → second run ALSO stuck forever" |
| 6 | API observeTimer 420ms body-scan: idle>50 s (review) / 60 s (indep) → abort | API branch gets idle protection (not only total-timeout) |
| 7 | API branch 0-tokens ≥ 15 s FAST abort (early-exit bypass of 200s+ grand timeout) | Dead OpenRouter / bad key exits instantly |
| 8 | `stageTimersRegistry` global Map holds 4 timers + 2 rejects → `stopOneStage()` clears/rejects OUTSIDE closure | Idle stops jumping WITHOUT waiting for finally block |
| 9 | Closure `_onKilledEvt` handler: 4 timers clear + both rejects + `stageAC.abort()` | Dual guarantee no ghost tick survives |
| 10 | In-loop badge write guard: `if (!_killedFlag && !perStageStopFlags.get(stageId))` | Stopped cards cannot be overwritten back to "streaming…" by a stale tick |
| 11 | `awaitStageSettled(stageId, 450 ms)` pipeline barrier: next card waits until AC+registry fully empty | Fixes "Stage-A still halting → Stage-B already appears" |
| 12 | `finally` double-clean: closure timers + `_treg.*` + delete global registry entry | Prevents memory leak & phantom ticks |

### Per-Stage Independent Action Buttons

Each of the 4 Stage cards footer row (right→left order):
- 🛑 **Stop Stage**: aborts ONLY that stage (siblings continue)
- 🔄 **Retry Stage**: re-runs that stage in-place; auto removes the old card; result written back to answerA/B/reviewBA/reviewAB
- 📋 **Copy Stage Body**: copies ONLY the prose body; never the badge or action buttons

User bubbles & assistant bubbles also each get independent 🔄 Retry / 📋 Copy action bars.

### Anti-Repeat / Infinite-Loop 3-Tier Guards
1. Prompt rule: every stage must end with explicit `--- END STAGE ---` marker
2. Stream meta: `superviseGuards = { maxTokens:1800, endMarker, repeatStreak:4, repeatSim:0.92 }`
3. Per-chunk: END marker / 4-line sim ≥ 0.92 repeat / maxTokens — ANY triggers immediate truncate + `⚠️ [Guard: …reason…]`

### Stage 5 — CLARIFY Short-Circuit (ask user, don't hallucinate patches)

If Stage-A and Stage-B **independently** append `❗CLARIFY_NEEDED <one or more closed-end questions the user MUST answer first>` at the end of their own prose:
- `bothWantClarify = true` is asserted;
- **Stage-C (Patch Eng) and Stage-D (Audit) are skipped** (patching under ambiguous inputs only produces hallucinations);
- Final Summary Card is replaced by an **🟡 Amber Clarify Card** that auto-merges both sides' questions, waits for user reply, then re-runs the full 4-Stage pipeline.

---

## ⚙️ 4 System Settings Tabs (Router / Knowledge Base / MCP Tools / Daemon)

Open any of the 4 rounded-icon buttons in the lower toolbar:

| Tab | Contents |
|---|---|
| 🛰️ **Router Settings** | 4+ API Router Profiles (Local LM Studio / Ollama / OpenRouter / OpenAI / Custom); URL/Key/Model triples; **Target-slot (A-only / B-only / A+B sync)** row; Save/Import/Export JSON; ONNX Hardware Acceleration 3-picker; Custom Models 3-sub-tabs (API / WebGPU / 📦 ONNX); Test Connection button |
| 📚 **Knowledge Base** | File upload (txt/md/json/pdf/docx/xlsx/pptx/code) → Chunk size picker → Build Index; Ingested files + chunk count live indicator; Live query Retrieval-Test button |
| 🔧 **MCP Tools** | MCP Servers definition / Scan / Ready tools browser |
| 🩺 **Daemon (Port 8001)** | Live health indicator; **1-click Restart/Enable** (auto kill stale :8001 process → relaunch `daemon.py`); View Logs; Download Models / Assets bundles; copy `cmd.exe` manual launcher command |

---

## 🛠️ Troubleshooting FAQ (added Q4 / Q5 / Q6)

Q1~Q3 live inside the built-in User Guide Tab 5 *FAQ*. The Q4~Q6 below cover v1.0.0's new SRE pipeline, ONNX backend, and WebGPU edge cases:

**Q4: WebGPU mode throws "Program terminated with exit(1)" / "MLCEngine exception" OR Stage-D progress freezes at 0%?**
> Classic WebGPU driver / OOM / stale WebLLM cached-engine reuse pattern. 3-step recovery:
> 1. Hit the stage card's **🛑 Stop Stage** (or the global Stop) — this also runs `webllmEngine = null` to invalidate the cached engine instance;
> 2. Flip Engine Mode to `🖥️ LM Studio / API` and back to `⚡ WebGPU` to force unload stale weights;
> 3. If still failing, swap the WebGPU model to `Qwen2.5-0.5B` (350 MB, lowest hang rate), or migrate to **📦 ONNX Qwen2.5-0.5B CPU High-Perf SIMD** (bypasses WebGPU driver stack completely).

**Q5: LM Studio reports tokens in its UI but Webcom assistant bubble shows blank / 0 chars?**
> Root cause: LM Studio's default SSE streaming sometimes omits the `choices[].delta.content` field in non-OpenAI-compatible streams. Fix:
> - In LM Studio → enable **OpenAI API compatibility mode → Include raw stream payloads**;
> - Or switch to Supervised-Mutual-Debug mode — any stage that reports **0 tokens ≥ 15 s** gets aborted by the 0-token-fast-abort guard immediately (does not wait the 200s+ grand timeout).

**Q6: After switching UI to English the LLM outputs 0 tokens / empty response?**
> Supervise pipeline prompts contain fixed-format report headings; mixing a zh-format prompt template with an en UI can confuse the model. Recovery:
> - After flipping the language picker, open Router Settings and hit **Save** (forces reload of the i18n-defaulted prompt templates);
> - Or send `/reset` once inside Supervise mode to flush the per-session prompt cache.

---

<a id="changelog"></a>
## 🕓 Changelog

### `v1.0.7-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-14 **Collapsible Dual Panels, Streamlined Artifact Drawer & Full Bilingual i18n Release**
> 🚀 Major update: Bidirectional panel collapsing tailored for 1366×768 (Asus VS229) compact displays + Overhauled Artifact Workbench drawer with pinned exit button + Streamlined Xorg app/control dropdowns + Complete bilingual (zh-TW / en) i18n translation coverage for 54+ newly added UI controls + 55/55 automated system diagnostics passing.

- **🖥️ Bidirectional Panel Collapsing (1366×768 Compact Screen Optimization)**:
  1. **Independent Panel Collapse**: Left workspace (Terminal / noVNC / Xorg) collapses to an ultra-thin vertical strip, allowing the AI chat area to expand to 100% width; right AI chat panel can likewise collapse to grant the terminal/desktop full screen space.
  2. **1366×768 (Asus VS229) Tailored Layout**: Prevents UI clipping and horizontal scrollbars on compact and standard resolution screens.
  3. **Strip Quick-Expand Controls**: Collapsed vertical strip provides intuitive tooltips and one-click restoration or jumping directly into Terminal, noVNC, Xorg, Chat, or Settings.
- **🎨 Artifact Workbench Drawer & Navigation Overhaul**:
  1. **Pinned Exit & "Actions ▾" Menu**: Fixed pinned "Exit (Esc)" button alongside a grouped "Actions ▾" dropdown on top right of the Artifact Workbench drawer to eliminate button overflow.
  2. **Consolidated Action List**: Reload Sandbox, Open in New Tab, Copy Complete Code, Download File, Save to App Library, Version Diff, and LLM Continuation are neatly accessible from the dropdown.
- **🖼️ Streamlined Xorg Toolbar Dropdown Menus**:
  1. **Compact Dropdowns**: Consolidated crowded Xorg buttons into two intuitive dropdowns: "🚀 Launch App ▾" and "⚙️ Controls & Setup ▾", saving essential workspace height.
  2. **One-Click Linux GUI Launchers**: Quick-launch Terminal, Thunar File Manager, Mousepad Text Editor, Calculator, and custom commands directly on the HTML5 canvas.
- **🌐 Complete Bilingual (zh-TW / en) i18n Coverage**:
  1. **54+ Missing UI Keys Added**: Thoroughly audited and translated all newly introduced UI buttons, collapsed strip tooltips, dropdown actions, MarkItDown converter triggers, and WSL control buttons in both Traditional Chinese (`zh-TW`) and English (`en`).
  2. **Dynamic Menu Language Synchronization**: Ensured dynamically rendered menus correctly invoke `t(...)` during runtime language switching.
- **🩺 Automated Diagnostic Suite 55/55 PASS**:
  - Full test suite in `diagnose_system.py` and `self_test.bat` passed 55 out of 55 checks with 100% SHA256 file parity across the project repository.

### `v1.0.6-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-11 **Feature, Self-Diagnostics & Cross-Platform Compatibility Release**
> 🚀 Major update: Microsoft MarkItDown full document conversion & upload integration + Dual-mode self-diagnostic suite + Windows batch launcher overhaul + UI button optimization & terminal fixes

- **📄 Integrated Microsoft MarkItDown Document Conversion Center & Upload**:
  1. **Bottom-Right Upload Conversion to LLM**: Compacted bottom-right action bar to 2 core buttons (Upload Document & Clear Chat). Uploading PDF, DOCX, XLSX, PPTX, HTML, CSV, or EPUB automatically triggers Microsoft MarkItDown backend parsing to feed structured Markdown directly to the LLM, with smart chunking for long documents.
  2. **Self-Contained Conversion Center Bundle**: Zero Docker / zero Node.js / zero global Python requirement. Complete 1.8MB web app bundled directly under `webcom/markitdown/` for out-of-the-box readiness.
  3. **Native Conversion Engine**: Backed directly by Microsoft MarkItDown 0.1.7 (`/api/convert`), rapidly converting PDF, DOCX, XLSX, PPTX, HTML, CSV, and EPUB into clean, standard Markdown.
  4. **Smart Auto-Wakeup Header Button**: Dedicated `[MarkItDown]` button in the top navigation bar automatically verifies Port 8001 daemon health, silently wakes up the service in background via `webcom://` if stopped, and automatically opens the converter tab.
  5. **Seamless Two-Way Navigation**: Quick link back to "Webcom Console" from the MarkItDown header for smooth multitasking.
  6. **Service Worker Dynamic Subpath Fix**: Enhanced `sw.js` precaching and `manifest.json` to dynamically resolve `/markitdown/` subpath hosting without 404 asset errors.
- **🩺 Dual-Mode Self-Diagnostic System (CLI & In-Browser)**:
  1. **CLI Full-Suite Automation (`diagnose_system.py` / `self_test.bat`)**: Automated 32-point diagnostic covering hardware environment, Python dependencies, 8001/8002 port bindings, frontend/backend syntax checks, and file hash parity.
  2. **In-Browser Interactive Modal (`[🩺 自我檢測]`)**: Dedicated header button triggers a visual diagnostic popup checking WebGPU support, daemon connectivity, MarkItDown engine readiness, and API router health in real time.
- **🩹 UI Button Hardening, Terminal Init & Daemon Indicator Fixes**:
  1. **Button Trigger Hardening**: Hardened file upload and toolbar controls using native elements to prevent synthetic click events from being blocked.
  2. **Daemon Status Indicator**: Restored real-time polling and visual indicator lights for daemon health.
  3. **WTerm Terminal Init**: Fixed terminal initialization and canvas sizing quirks across modern Chromium-based browsers.
- **🛡️ Windows Cross-Machine Batch Launcher Overhaul (Pure ASCII & Strict CRLF)**:
  1. **Fixed cmd.exe Buffer Byte-Shift Parsing Crash**: Eliminated the infamous Windows cmd block-read offset bug triggered by Unix LF line endings combined with multibyte UTF-8 em-dashes (which clipped `REM` -> `'M'`, `setlocal` -> `'tlocal'`, `cd /d` -> `'/d'`).
  2. **Added `.gitattributes`**: Explicitly enforces `eol=crlf` for all `*.bat`, `*.cmd`, `*.vbs`, `*.ps1`, and `*.reg` files.
  3. **Multi-Tier Python Detection & Flat Architecture**: Rewrote `start_daemon.bat` in pure ASCII with flat `goto` control flow, **prioritizing the root `%~dp0python\python.exe` portable environment** (runs out-of-the-box on clean PCs with no system Python installed), followed by `uv`, system `python`, and `py -3`.
  4. **Auto Protocol Registration**: Automatically registers the `webcom://` URL protocol in `HKCU` on startup (no admin rights required), allowing browser buttons to wake up daemon silently.
- **⚖️ Open-Source License & Acknowledgements**: Full attribution for Microsoft MarkItDown and GoneTone/markitdown-website across bilingual guides, drawer panels, and `README.md`.
- **🧾 Global Version Bump v1.0.5 → v1.0.6**: Unified all 11 occurrences in `index.html`, bilingual `README.md` banners, user guides, and acknowledgements.

### `v1.0.5-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-11 **Version-Bump Maintenance Release**
> 🔖 Stability freeze: all v1.0.4 fixes (daemon.py / webcom:// / silent_daemon) have been validated and formally promoted
- **🧾 Global version bump v1.0.4 → v1.0.5**: all 10 occurrences inside `index.html` (Meta/Title/Badge/Footer/bilingual-manual/ANSI-welcome/JSON-demo), plus both `README.md` banners and Changelog headers, unified to `v1.0.5`
- **🧪 v1.0.4 three stability fixes marked STABLE**:
  1. daemon.py auto-release 8001 + pythonw stdout/stderr redirect → **STABLE**
  2. `webcom://` protocol `<a>.click()` bypassing CSP iframe block → **STABLE**
  3. `silent_daemon.vbs` wscript fully background zero-popups → **STABLE**
- **📄 Docs**: bilingual Changelog v1.0.5 maintenance entries added

### `v1.0.4-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-09 **Bugfix Release**
> 🐛 Addresses 3 stability regressions reported in v1.0.3 + 2 asset/doc sync items
- **🩹 4 fixes in daemon.py (8001 port-claim + silent startup + pythonw crash)**
  1. Pre-launch auto-check `127.0.0.1:8001 LISTEN` — if owned by a *different* PID → `psutil.kill()` the stale process (fixes "Daemon 1-click Restart fails / Address already in use")
  2. `delayed_exit()` 0.5 s → 0.3 s + writes `.stop_daemon` stop-marker file + also terminates the parent `cmd.exe` wrapper (fixes zombie cmd black window after close)
  3. `pythonw.exe` / windowless service mode: when `sys.stdout/sys.stderr is None` → auto-redirect both to `daemon.log` (fixes crashes under Task Scheduler / silent launcher because stderr was unavailable)
  4. CWD hardening: at startup, force `os.chdir(__file__ dir)` + `sys.path.insert(0, __dir__)` (fixes imports when daemon is launched from a different working directory)
- **🩹 `webcom://` custom protocol launcher now uses `<a>.click()` instead of `iframe.src`**: newer Edge/Chromium CSP policies block iframe-loading custom protocols (caused a 3000 ms ghost-flash / no-launch). Replaced with `<a href="webcom://…">` + programmatic `.click()` + removal after 2000 ms — works on Chrome / Edge / Firefox.
- **🩹 Download-register `.reg.bat` now launches via `wscript.exe silent_daemon.vbs` (truly silent)**: the previous `start_daemon.bat` route popped a cmd black console; the new `HKCU\…\webcom\shell\open\command = wscript.exe silent_daemon.vbs %1` runs **fully in background, zero windows, zero user disruption**.
- **📦 Asset sync**: `assets/webllm.bundle.js` (WebGPU loader callback priority tweak — 78-byte delta)
- **📄 Docs**: bilingual Changelog entries + top banner version bumped v1.0.3 → v1.0.4

### `v1.0.3-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-09
- **Docs-consolidation maintenance release** (feature parity with v1.0.2; version bump marks the following **STABLE** freeze points):
  - 🛡️ Supervised-Mutual-Debug 4-Stage SRE pipeline + stop-timer v26 12-layer stuck-kill chain → marked **STABLE**
  - 📦 ONNX Runtime + Transformers.js: 4 built-in models doc / 3-way hardware picker / first-launch HuggingFace auto-fetch → marked **STABLE**
  - FAQ Q4/Q5/Q6 (WebGPU exit-1 / LM Studio empty SSE payload / language-switch 0-token) resolution docs stabilized
  - "4 System Settings tabs" table / "RAG PDF/Word/Excel/PPT format list" / "Terminal Export Log / Clear Buffer" docs fully synchronized
  - Full version-string **consistency pass** (all 11 places — 4× License & Credits tabs / footer brand / 2× ANSI terminal welcome banner / JSON validator demo / HTML comment meta / `<title>` / Banner badge) bumped to `v1.0.3`
  - Fixed v1.0.2 README trailing whitespace inside the English Supervise section and zh/en Changelog line-width alignment

### `v1.0.2-Dual-Engine-WebGPU-RAG-Supervise` — 2026-09-09
- **🛡️ Supervised-Mutual-Debug mode fully upgraded to 4-Stage SRE Troubleshooting Pipeline** (diag-1~4 complete):
  - Stage-C (Patch Engineer) forced 4-step flow: Issue Detection → Executable bash/cmd fenced patches → Stage-A blind-spot audit → 📋 fixed 7-line Diagnostic Report
  - Stage-D (Audit Sign-off SRE) forced 3-step flow: Per-patch VERIFIED✅/NEEDS-EDIT⚠️/DANGEROUS❌ tags → Residual risk scan → 🛡️ fixed 5-section Final Audit Report
  - Final Summary card **always leads with** 📊 A/B/C/D full-stage Diagnostic Dashboard (worst-case failure guarantee: structured log is NEVER blank)
  - CLARIFY_NEEDED both-sides short-circuit → 🟡 Amber Clarify Card emitted, Stage-C/D skipped entirely
- **stop-timer v26 12-layer stuck-iterator kill chain**: stageTimersRegistry + CustomEvent cross-closure broadcast + 450ms settle barrier + skip-D gate (C TIMEOUT ⇒ D card never appears)
- **Per-Stage independent 3-button footer**: 🛑 Stop / 🔄 Retry / 📋 Copy body; user+assistant chat bubbles also get retry+copy action bars
- **UX fixes 1/2/3**: Stage-D progress visible (N tok @ X t/s + idle seconds); footer DOM-flow buttons never overlap body; chat-box 88 px bottom padding
- **📦 ONNX Runtime + Transformers.js fully documented**: 4 built-in models table / CPU-SIMD vs WebGPU 3-way hardware picker / HuggingFace first-launch auto-fetch / custom onnx-community model ID
- **≥ 27 pairing configurations**: api/webgpu/onnx 3 engine kinds × Side-A/B freely combined; 4 new recommended scenarios added (pure-ONNX dual-audit / Qwen3-VL ↔ GPT-4V cross-vision / …)
- **Docs coverage**: 4 System Settings tabs table; FAQ Q4/Q5/Q6 (WebGPU exit-1 / LM Studio empty SSE payload / language-switch 0-token); RAG PDF/Word/Excel/PPT format list; terminal Export Log / Clear Buffer documented
- **stuckD root-cause fixes**: WebGPU for-await AbortSignal ignored → explicit chunks.return() + webllmEngine=null cache invalidate; 0-tokens 15s fast-abort; API-side idle watchdog

### `v1.0.1-Dual-Engine-WebGPU-RAG` — 2026-08-30
- First **🛡️ Supervise Mode** draft (Side-A/B dual-LLM 4-stage pipeline)
- Added **Co-Think** hybrid reasoning mode
- Fixed qc Row-1 reordering (flex-nowrap + inline order resolves Tailwind `order-*` class JIT non-determinism)
- Fixed rd API↔API distinct profile auto-assign (ensureAltProfileDistinct + Modal Target-slot A/B switch row)
- Fixed qa visual left/right order (Side-A always left @ 922px / Side-B always right)
- Fixed qb engine-mode-switch layout refresh (dualEngineSubMode reset + single isSupervise predicate)
- De-nested 6 template literal sites; V8 HTML-inline parser 11/11 pass
- Row-1 controls ph-movement: 4 controls to Router-right, 4 toggles to Row-2 gap
- 3-tier anti-repeat / infinite-loop guard: END marker + maxTokens 1800 + 4-line sim≥0.92

### `v1.0.0-Dual-Engine-WebGPU-RAG` — 2026-08-29
- Initial public release: single-file `index.html` Dual-Engine AI Console
- Multi-protocol terminal (WSL/SSH/Telnet/Web Serial/Backend Serial + virtual keypad)
- LM Studio/API Router multi-Profile setup with JSON Import/Export
- WebGPU 5 models + ONNX 4 models local inference (dual CPU/WebGPU backends)
- RAG Knowledge Base: Chunked indexing + vector store + live retrieval test
- MCP Tools panel + WinPE autorun batch + Offline simulation toggle
- Built-in 6-page zh-TW / English bilingual User Guide

---

## 📜 License / Credits

- **Project as a whole**: **GNU GPL v3.0** — open-source, remixable; any commercial/derivative scripts **must retain this copyright notice and GPLv3**.
- **Third-Party Acknowledgements** (see in-app **⚖️ License & Credits** tab, all packages retain original licenses):
  - **Frontend**:
    - [wterm](https://github.com/vercel-labs/wterm) (Vercel Labs, Apache 2.0) — Browser DOM + WASM terminal emulator
    - [@mlc-ai/web-llm](https://github.com/mlc-ai/web-llm) (MLC AI, Apache 2.0) — In-browser WebGPU local LLM inference
    - [Tailwind CSS](https://github.com/tailwindlabs/tailwindcss) (Tailwind Labs, MIT) — Utility-First CSS framework
    - [Lucide Icons](https://github.com/lucide-icons/lucide) (Lucide Contributors, ISC) — Open-source SVG icon library
    - [marked.js](https://github.com/markedjs/marked) (markedjs, MIT) — Markdown parser & renderer
    - [markitdown-website](https://github.com/GoneTone/markitdown-website) (GoneTone, MIT) — In-browser Document to Markdown Web Application (Live Preview / Batch Zip)
  - **Backend (Python)**:
    - [FastAPI](https://github.com/fastapi/fastapi) (Sebastián Ramírez, MIT) — High-performance Python Web API framework
    - [uvicorn](https://github.com/encode/uvicorn) (Encode, BSD 3-Clause) — Lightning-fast ASGI HTTP server
    - [Paramiko](https://github.com/paramiko/paramiko) (Jeff Forcier et al., LGPL 2.1) — Python SSH2 protocol implementation
    - [pyserial](https://github.com/pyserial/pyserial) (Chris Liechti, BSD 3-Clause) — Python serial (COM / UART) communication
    - [markitdown](https://github.com/microsoft/markitdown) (Microsoft, MIT) — Multi-format Document to Markdown conversion core (PDF/Office/HTML/CSV)
