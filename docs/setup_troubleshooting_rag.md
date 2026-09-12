# Webcom 環境建置、WSL2 GUI/noVNC、多模態視覺與常見疑難排解指南 (RAG Knowledge Base)

本文件收錄 Webcom 在 Windows 10/11 本地環境部署、Python 虛擬環境配置、WSL2 整合、noVNC 與 Xorg 桌面串流、Gemma-4 ONNX 多模態影像處理時遇到的各類常見問題與標準解決方案，可作為 RAG 檢索資料庫及維護指南。

---

## 問題 1：Windows 批次檔 (.bat) 換行符與 Python 路徑偵測失敗

### 症狀
- 雙擊執行 `start_webcom.bat` 時視窗閃退，或提示 `'python' 不是內部或外部命令、可執行的程式或批次檔`。
- 在部分環境中執行 `.bat` 出現語法錯誤或標籤找不到。

### 根本原因
1. **CRLF 換行符遺失**：Windows cmd.exe 解析 `.bat` 檔時嚴格依賴 Windows CRLF (`\r\n`) 換行。若透過 Linux 工具、Git 誤轉換或編輯器存成 LF (`\n`)，批次檔中的括號區塊、`goto` 標籤將無法正確被解析。
2. **PATH 環境變數未包含 Python**：許多現代開發環境（如 Hermes Agent、conda、嵌入式 Python、使用者本機獨立安裝版）之 `python.exe` 位於特定目錄（例如 `AppData\Local\Programs\Python` 或 `AppData\Local\hermes\...\venv\Scripts\python.exe`），未被加入全域 PATH。

### 標準解決方案
在 `start_webcom.bat` 中加入動態 Python 路徑偵測回退機制：
```bat
@echo off
setlocal enabledelayedexpansion

:: 優先檢測 PATH 中的 python
where python >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    set PYTHON_CMD=python
    goto :run
)

:: 檢測常見虛擬環境與安裝路徑
if exist "%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe" (
    set PYTHON_CMD="%USERPROFILE%\AppData\Local\hermes\hermes-agent\venv\Scripts\python.exe"
    goto :run
)
if exist "C:\Python312\python.exe" (
    set PYTHON_CMD="C:\Python312\python.exe"
    goto :run
)
if exist "C:\Python311\python.exe" (
    set PYTHON_CMD="C:\Python311\python.exe"
    goto :run
)

echo [ERROR] 找不到可用的 Python 解譯器，請安裝 Python 3.10+ 並勾選 Add to PATH。
pause
exit /b 1

:run
%PYTHON_CMD% daemon.py
```
**檔案編碼檢查**：確保 `.bat` 檔案結尾為 CRLF (`\r\n`)，且無 UTF-8 BOM。

---

## 問題 2：Pip 套件版本依賴衝突 (如 youtube-transcript-api)

### 症狀
- 執行 `pip install -r requirements.txt` 時報錯，或安裝 `youtube-transcript-api` 等套件時與其他庫產生衝突。

### 根本原因
- 舊版相依檔案過度嚴苛綁定特定子套件小版本（例如鎖定已廢棄相依或不相容 Python 3.12+ 的輪子檔）。

### 標準解決方案
1. **解耦極簡化 `requirements.txt`**：移除不必要的次要鎖定，採用寬鬆版本宣告。
2. **核心依賴清單**：
   - `fastapi` / `uvicorn` (Daemon 核心服務)
   - `psutil` (系統硬體監控)
   - `pillow` (影像多模態前處理)
   - `onnxruntime` (本地端推論)
   - `requests` (外部 API 呼叫)
3. **動態按需載入 (Dynamic Lazy Import)**：在 `daemon.py` 中將非必要套件（如 YouTube 字幕擷取、PyAudio）以 `try...except ImportError` 包裹，缺套件時優雅降級並提示使用者。

---

## 問題 3：Gemma-4 ONNX 多模態視覺影像輸入遺失與解析

### 症狀
- 在聊天介面中上傳圖片並提問後，模型僅回答文字或提示看不到圖片。
- 終端機日誌顯示只有文字 token，無影像特徵注入。

### 根本原因
1. **前端訊息結構遺失**：前端在呼叫 `/api/generate` 或組裝 prompt 時，上傳的 base64 影像資料在 `handleSend` 流程中被重新序列化成純字串，遺失了 `images` 陣列屬性。
2. **Token 標籤未正確對齊**：Gemma-4 / PaliGemma 視覺模型要求影像位置需有特定的 `<|image|>` 或 `<image>` 預留 token，若直接將 base64 混入純文本，Tokenizer 無法辨識。
3. **色彩通道解碼錯誤**：前端 Canvas 或 Base64 傳入為 RGBA，若直接轉 numpy array 未轉換為 RGB，會導致影像通道維度與正規化錯誤。

### 標準解決方案
1. **前端資料保護**：
   在發送至後端前確保訊息結構包含完整的影像列表：
   ```javascript
   const payload = {
       prompt: userText,
       images: uploadedImages.map(img => img.base64), // 確保乾淨 base64 陣列
       stream: true
   };
   ```
2. **後端多模態預處理 (`daemon.py`)**：
   使用 Pillow 解碼並轉為 RGB，配合 ONNX Runtime 視覺特徵抽取：
   ```python
   from PIL import Image
   import io, base64

   def process_image_input(b64_string):
       if "," in b64_string:
           b64_string = b64_string.split(",", 1)[1]
       image_bytes = base64.b64decode(b64_string)
       image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
       return image
   ```

---

## 問題 4：WSL2 noVNC 遠端桌面連線黑畫面排查

### 症狀
- 瀏覽器開啟 `http://localhost:6080/vnc.html`，連線成功但畫面全黑（或僅有預設點狀背景），無法顯示任何 Linux GUI 應用。

### 根本原因
1. **WSLg Wayland DISPLAY 衝突**：WSL2 預設啟用 WSLg，佔用 `DISPLAY=:0` 與 `/tmp/.X11-unix`。此時若直接啟動 VNC 伺服器掛載到 `:0`，會因為 Wayland 合成器權限鎖定導致黑畫面。
2. **無獨立虛擬顯示器**：缺少 Xvfb (X Virtual Framebuffer) 或桌面環境，連線時沒有任何視窗輸出畫面。
3. **x11vnc 參數不當**：若缺少 `-forever -shared -noxrandr`，客戶端中斷連線後 VNC 立即退出；且 xrandr 輪詢失敗會導致黑屏。

### 標準解決方案
1. **建立獨立的虛擬 X 顯示器 `:1`**：
   在 WSL 中啟動 Xvfb：
   ```bash
   Xvfb :1 -screen 0 1280x720x24 -ac +extension GLX +render -noreset &
   ```
2. **配置 x11vnc 綁定 `:1`**：
   ```bash
   x11vnc -display :1 -rfbport 5901 -forever -shared -bg -noxrandr -nopw
   ```
3. **啟動 websockify 橋接 WebSocket 與 VNC**：
   ```bash
   websockify --web=/usr/share/novnc 6080 localhost:5901 &
   ```
4. **指定應用程式輸出至 DISPLAY `:1`**：
   所有要投影到 noVNC 的程式必須帶有環境變數：
   ```bash
   DISPLAY=:1 GDK_BACKEND=x11 mousepad &
   ```

---

## 問題 5：左側 Xorg 模式無法運作與改進

### 症狀
- 點擊介面左側工具列的「Xorg 桌面」模式，畫面顯示空白或連線失敗。
- 啟動 Linux GUI 程式（如 Terminal、Thunar）後立刻自動關閉。
- 前端 RFB 出現 `Ignoring unsupported SetDesktopSize` 警告。

### 根本原因
1. **連線端口與顯示代號不符**：前端預設連接 `:0`，但 WSLg 阻擋了 `:0`，真正的 Xvfb/VNC 運行在 `:1` (Port 5901 / Websockify 6080)。
2. **前端缺乏一鍵快捷發射器 (App Launcher)**：Xorg 模式進入後若無啟動任何 GUI 視窗，使用者只會看到黑色背景，誤以為當機。
3. **行程隨子 shell 退出**：後端若使用 `wsl.exe` 執行指令而未分離 Session，指令結束時 GUI 行程會收到 SIGHUP 被一併殺死。
4. **前端 noVNC 設定問題**：啟用 `resizeSession = true` 會向 VNC 伺服器發送 `SetDesktopSize`，若 x11vnc 未配置 xrandr 支援則報錯。

### 標準解決方案
1. **後端提供專屬 `/api/wsl/launch-app` API**：
   在 `daemon.py` 中使用 `setsid` 或 `nohup` 脫離終端機控制，並強制帶入 `DISPLAY=:1`：
   ```python
   @app.post("/api/wsl/launch-app")
   async def launch_wsl_app(req: AppLaunchRequest):
       cmd = f"DISPLAY=:1 GDK_BACKEND=x11 nohup {req.app} >/dev/null 2>&1 &"
       subprocess.Popen(["wsl", "-e", "sh", "-c", cmd])
       return {"status": "ok", "app": req.app}
   ```
2. **前端 Xorg 視窗加入快速啟動工具列**：
   提供一鍵啟動終端機 (`xfce4-terminal`)、檔案管理員 (`thunar`)、文字編輯器 (`mousepad`)、計算機 (`xcalc`) 與自訂指令輸入框。
3. **前端 RFB 配置調整**：
   設定 `scaleViewport = true` 啟用自適應縮放，關閉 `resizeSession = false`，避免發送不支援的 SetDesktopSize 協議封包。

---

## 問題 6：診斷指令與系統速查表 (Cheat Sheet)

### Windows 快速排查指令 (PowerShell)
```powershell
# 檢查連接埠 8001 (Daemon), 5901 (VNC), 6080 (noVNC) 是否正在接聽
Get-NetTCPConnection -LocalPort 8001, 5901, 6080 -State Listen -ErrorAction SilentlyContinue

# 檢查 WSL 狀態與發行版本
wsl --list --verbose

# 執行 Webcom 完整自檢腳本 (55 項檢查)
python diagnose_system.py
```

### Linux / WSL 快速排查與修復指令 (Bash)
```bash
# 檢查 Xvfb、x11vnc、websockify 行程
ps aux | grep -E 'Xvfb|x11vnc|websockify'

# 一鍵啟動 WSL noVNC 完整圖形環境服務
export DISPLAY=:1
Xvfb :1 -screen 0 1280x720x24 -ac +extension GLX +render -noreset >/dev/null 2>&1 &
x11vnc -display :1 -rfbport 5901 -forever -shared -bg -noxrandr -nopw >/dev/null 2>&1
websockify --web=/usr/share/novnc 6080 localhost:5901 >/dev/null 2>&1 &

# 在 DISPLAY :1 啟動測試視窗
DISPLAY=:1 GDK_BACKEND=x11 xcalc &
```
