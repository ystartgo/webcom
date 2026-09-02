# Webcom — Dual-Engine AI Console

> **繁體中文** ・ [English](#english)

**Webcom** 是一套單檔 `index.html` 就能啟動的 **雙引擎 AI 主控台**，整合 **多協定終端機（WSL / SSH / Telnet / Web Serial / 後端 Serial）**、**LM Studio / API** 與 **WebGPU 瀏覽器本地 LLM** 兩種推理引擎、**RAG 知識庫管理**、**MCP 協定工具面板**、**純斷網模擬**、**WinPE 開機自動執行** 等常見的現場維運／離線操作需求。

採用 **GNU GPL v3.0** 開源授權（詳見內建手冊第 6 頁「版權 & 致謝」）。

---

## ✨ 功能亮點

- 🎛️ **三 LLM 引擎 & 混合模式（Co-Think / Supervise）**
  - LM Studio / 任意 OpenAI 相容 API Endpoint
  - ⚡ **WebGPU 純瀏覽器本地推理**（WebLLM MLC：Qwen 2.5 0.5B / 1.5B / 3B、Llama-3.2-1B、SmolLM2-360M）
  - 📦 **ONNX Runtime + Transformers.js 本地推理**（雙後端：💻 CPU SIMD 高效運算 或 ⚡ WebGPU 顯卡加速）
    - 內建 4 模型：Qwen2.5-0.5B (350MB 極速⭐)、Bonsai-1.7B、Qwen3-VL-2B 視覺、Gemma-4-2B (Google)
    - 支援「自訂 HuggingFace onnx-community 模型 ID」手動加載
  - 可切換：「API → WebGPU → ONNX → 雙引擎聯合思考 → 監督排查流水線」共 5 模式
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

- 🎛️ **Triple LLM Engine & Hybrid Modes (Co-Think / Supervised-Mutual-Debug)**
  - LM Studio / any OpenAI-compatible API endpoint
  - ⚡ **WebGPU browser-local inference** (WebLLM MLC: Qwen 2.5 0.5B / 1.5B / 3B, Llama-3.2-1B, SmolLM2-360M)
  - 📦 **ONNX Runtime + Transformers.js browser-local inference** (dual backends: 💻 CPU High-Perf SIMD OR ⚡ WebGPU GPU acceleration)
    - 4 built-in models: Qwen2.5-0.5B (350 MB ultra-fast ⭐), Bonsai-1.7B, Qwen3-VL-2B (Vision), Gemma-4-2B (Google)
    - "Custom HuggingFace onnx-community model ID" tab for user-added models
  - 5 selectable top-level modes: `API → WebGPU → ONNX → Co-Think (hybrid) → Supervised-Mutual-Debug (4-Stage SRE Pipeline)`
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

---

## 📜 License / Credits

- **Project as a whole**: **GNU GPL v3.0** — open-source, remixable; any commercial/derivative scripts **must retain this copyright notice and GPLv3**.
- Third-party package acknowledgements: open the app and navigate to **⚖️ License & Credits** tab (front-end 5 libs, back-end 4 libs — Apache 2.0 / MIT / ISC / BSD-3-Clause / LGPL 2.1 individually).
