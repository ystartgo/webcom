# Webcom — Dual-Engine AI Console

> **繁體中文** ・ [English](#english)

**Webcom** 是一套單檔 `index.html` 就能啟動的 **雙引擎 AI 主控台**，整合 **多協定終端機（WSL / SSH / Telnet / Web Serial / 後端 Serial）**、**LM Studio / API** 與 **WebGPU 瀏覽器本地 LLM** 兩種推理引擎、**RAG 知識庫管理**、**MCP 協定工具面板**、**純斷網模擬**、**WinPE 開機自動執行** 等常見的現場維運／離線操作需求。

採用 **GNU GPL v3.0** 開源授權（詳見內建手冊第 6 頁「版權 & 致謝」）。

---

## ✨ 功能亮點

- 🎛️ **雙 LLM 引擎 & 聯合思考（Co-Think）**
  - LM Studio / 任意 OpenAI 相容 API
  - WebGPU 純瀏覽器本地推理（Qwen 2.5 0.5B / 1.5B / 3B、Llama-3.2-1B、SmolLM2-360M）
  - 可切換「API → WebGPU → 雙引擎聯合思考」三種模式
- 🖥️ **多協定終端機**（以 [wterm](https://github.com/vercel-labs/wterm) 為基礎的 WASM 終端）
  - 本地 Shell（WSL）
  - SSH / Telnet 遠端登入
  - Web Serial（Chrome/Edge 內建，免驅動免 Daemon，直接操作 COM 埠）
  - 後端 Serial（透過 Daemon 遠端寫入序列埠）
  - 虛擬鍵盤：`Ctrl+A / Ctrl+C / Ctrl+V / Ctrl+X` + 方向鍵
- 📚 **RAG 知識庫管理員**（Chunk 分段 + 向量索引 + 即時搜尋測試）
- 🔧 **MCP 工具面板**：Model Context Protocol Server 設定與發現
- 🛜 **純斷網模擬開關**：一鍵封鎖所有非 `127.0.0.1` 外部請求，免拔網路線測試離線情境
- 🖹 **6 頁完整使用手冊**（雙語 zh-TW / EN）：快速上手、終端機協定、AI + RAG、離線 WinPE、常見問題、版權致謝
- 🌍 **完整 zh-TW / English 雙語 UI**：頂部語言切換鈕即時生效
- 🪟 **WinPE 自動執行**：`WinPE_Autorun.bat` 掛載 ISO 即可自動啟動 Daemon 並開啟介面

---

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

### ④ (可選 / WSL) 在 WSL 啟動 Daemon 並開通 Port 8001

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

## 🧪 三種引擎模式

在右上角 Engine Mode Select 切換：

| 模式 | 說明 | 需求 |
|---|---|---|
| 🖥️ LM Studio / API | 呼叫任何 OpenAI 相容 Endpoint（需在 Router Settings 設定 profile）| 有 Daemon 或 LM Studio 本機執行中 |
| ⚡ WebGPU 瀏覽器純本機 | 100% 離線，瀏覽器內推理 | 需先執行 `download_offline_models.bat` |
| 🧠 Co-Think（雙引擎聯合思考）| 先問 API，無回應時自動 fallback WebGPU | 兩者皆需設定 |

---

## 📜 License / 授權

- **整體專案**：GNU GPL v3.0 （本軟體開源可修改，所有商業或衍生腳本 **必須保留此版權聲明與 GPLv3**）
- 第三方套件致謝清單：請見程式內 **⚖️ 版權 & 致謝** 頁（含前端 5 套件、後端 4 套件個別授權：Apache 2.0 / MIT / ISC / BSD-3-Clause / LGPL 2.1）

---

---

<a id="english"></a>
# Webcom — Dual-Engine AI Console (English)

**Webcom** is a single-file (`index.html`) **Dual-Engine AI Console** that combines a **multi-protocol terminal (WSL / SSH / Telnet / Web Serial / Backend Serial)**, **LM Studio / API** and **WebGPU browser-local LLM** inference engines, **RAG Knowledge Base**, **MCP tool panel**, **pure-offline simulation switch**, and **WinPE autorun** for real-world on-site / offline ops.

Licensed under **GNU GPL v3.0**. See the built-in User Guide tab 6 *License & Credits* for full third-party acknowledgements.

---

## ✨ Highlights

- 🎛️ **Dual LLM Engine & Co-Think hybrid mode**
  - LM Studio / any OpenAI-compatible API endpoint
  - WebGPU pure-browser local inference (Qwen 2.5 0.5B/1.5B/3B, Llama-3.2-1B, SmolLM2-360M)
  - Switchable: `API` → `WebGPU` → `Co-Think (hybrid)`
- 🖥️ **Multi-Protocol Terminal** (WASM, powered by [wterm](https://github.com/vercel-labs/wterm))
  - Local Shell via WSL
  - SSH / Telnet remote login
  - **Web Serial** (Chrome/Edge built-in — no driver, no daemon, direct COM/UART control)
  - Backend Serial (serial ports routed through port-8001 Daemon for AI Agent mode)
  - Virtual keypad: `Ctrl+A / Ctrl+C / Ctrl+V / Ctrl+X` + arrow keys
- 📚 **RAG Knowledge Base Manager** (chunked indexing + live search test)
- 🔧 **MCP Tools Panel** (Model Context Protocol server configuration + discovery)
- 🛜 **Simulated Offline Mode toggle**: one-click block ALL non-`127.0.0.1` traffic; test offline scenarios without unplugging cables
- 🖹 **6-page User Guide** (bilingual zh-TW / EN): Quick Start, Terminal Protocols, AI+RAG, Offline & WinPE, FAQ, License & Credits
- 🌍 **Full zh-TW ↔ English bilingual UI** — live switch from the top bar
- 🪟 **WinPE Autorun**: `WinPE_Autorun.bat` starts the Daemon & launches UI automatically when the ISO boots

---

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

### ④ (Optional / WSL) Run the daemon inside WSL + reach Port 8001 on Windows

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
| ⚡ WebGPU Browser Local | 100% offline. In-browser inference via WebLLM | Run `download_offline_models.bat` first |
| 🧠 Co-Think (hybrid) | Tries API endpoint first, falls back to WebGPU automatically | Both engines configured |

---

## 📜 License / Credits

- **Project as a whole**: **GNU GPL v3.0** — open-source, remixable; any commercial/derivative scripts **must retain this copyright notice and GPLv3**.
- Third-party package acknowledgements: open the app and navigate to **⚖️ License & Credits** tab (front-end 5 libs, back-end 4 libs — Apache 2.0 / MIT / ISC / BSD-3-Clause / LGPL 2.1 individually).
