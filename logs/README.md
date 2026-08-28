# /logs — 執行期日誌檔輸出區

## 🈶 繁體中文說明

此資料夾為 **執行期 log 檔** 的預設輸出位置，可包含：

- `daemon.log` — 由 [start_daemon.bat](../start_daemon.bat) 或手動執行 `python daemon.py > logs/daemon.log 2>&1` 時，後端 FastAPI 的 stdout / stderr 完整輸出（包含啟動紀錄、HTTP 路由請求、SSH/Telnet/Serial 通聯錯誤等）。
- `webcom_*.log` — 前端若啟用除錯模式時額外輸出的 RAG 分段、模型載入、API 回應等除錯紀錄。

### 🚫 不要把 logs 推上 GitHub

`.gitignore` 已將此目錄下所有 `*.log` 與 `*.tmp` 忽略。
- 此 `.gitkeep` 與 `README.md` 純粹用來保留「空目錄」，讓第一次 clone 下來的使用者不用手動 `mkdir logs` 就能啟動 Daemon 並將 log 導入正確位置。
- 若需要除錯後送出，建議匿名化 IP / 金鑰後，改成 `.zip` 或 GitHub Issue 附件方式分享。

### 🖱️ 建議的啟動方式（同時寫入 daemon.log）

```powershell
# Windows PowerShell — 即時輸出到螢幕 + 存檔
python -u daemon.py 2>&1 | Tee-Object -FilePath logs\daemon.log
```

---

## 🌐 English

Default output folder for **runtime log files**:

- `daemon.log` — full stdout/stderr of the backend FastAPI daemon when launched with redirected output from [`start_daemon.bat`](../start_daemon.bat) or manually via `python daemon.py > logs/daemon.log 2>&1`. Includes startup messages, HTTP requests, SSH/Telnet/Serial connection diagnostics, etc.
- `webcom_*.log` — optional front-end debug logs (RAG chunking, model loading, API traces) when the debug flag is toggled.

### 🚫 Never commit real logs

All `*.log` and `*.tmp` files under this folder are excluded via the root `.gitignore`.
- The `.gitkeep` + this `README.md` only exist so the folder is part of the clone — first-time users do not need to `mkdir logs` before redirecting the daemon's output.
- If you need to send logs for debugging, anonymize IPs / API keys first and share as a `.zip` or GitHub Issue attachment.

### 🖱️ Recommended launch (live screen + file log)

```powershell
# PowerShell — live output AND saved to disk
python -u daemon.py 2>&1 | Tee-Object -FilePath logs\daemon.log
```
