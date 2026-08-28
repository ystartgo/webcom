# /python — Python 內嵌執行環境（可選，建議直接用系統 Python）

## 🈶 繁體中文說明

此資料夾預留作「**可攜式內嵌 Python 執行環境**」存放位置——也就是一般 Windows 使用者 **未安裝 Python 時**，可將獨立的 embeddable Python（例如 [python-3.11.x-embed-amd64.zip](https://www.python.org/downloads/windows/)）解壓到這裡，並把 `Lib/site-packages` 放在 `python/Lib/site-packages/` 裡面。

但 **一般使用情境（你電腦有裝 Python 3.10+）完全不需要此資料夾**，只要在專案根目錄執行：

```powershell
pip install -r ../requirements.txt
start_daemon.bat
```

就可以啟動 Daemon。

### 🤔 為什麼倉庫不放內容？

1. 單一 embeddable Python + FastAPI/uvicorn/paramiko 依賴就超過 **400 MB**，會讓倉庫肥大。
2. `.gitignore` 已將 `/python/**` 整個忽略，避免有人不小心把機敏的 venv 或 `.pyc` 推上去。
3. 開發者的 Python 版本、32/64 位元、VC Runtime 相依性各自不同，預打包通常會帶來更多問題。

### 📦 真的要內嵌時的步驟（離線 / WinPE 情境）

```
webcom/python/
├── python.exe / python311.dll / *.pyd              ← embeddable python 解壓後的檔案
├── python311._pth                                   ← 要加上 . 與 Lib/site-packages 讓它能讀 site-packages
└── Lib/site-packages/
    ├── fastapi/ uvicorn/ pydantic/ paramiko/ …     ← 以 pip install --target=./python/Lib/site-packages -r requirements.txt 安裝
```

完成後 `start_daemon.bat` 裡的 `where python` 找不到系統 Python 時，可自行在最前方加：

```batch
set PATH=%~dp0python;%PATH%
```

---

## 🌐 English

This folder is reserved for an **optional portable / embedded Python runtime** — useful on Windows machines that do NOT have Python installed, where you would otherwise unzip an embeddable package (e.g. [python-3.11.x-embed-amd64.zip](https://www.python.org/downloads/windows/)) here with `Lib/site-packages` populated.

**For normal usage (Python 3.10+ already installed system-wide) you do NOT need this folder at all.** Just run from the repo root:

```powershell
pip install -r ../requirements.txt
start_daemon.bat
```

### 🤔 Why is this folder empty in the repo?

1. A single embeddable Python + FastAPI/uvicorn/paramiko stack already exceeds **400 MB** and would bloat the repo.
2. `.gitignore` already excludes `/python/**` so nobody accidentally pushes a personal venv or `.pyc` cache.
3. Python version / architecture / VC Runtime dependencies differ wildly per machine — shipping a pre-built embedded env causes more issues than it solves.

### 📦 If you really need an embedded env (offline / WinPE)

```
webcom/python/
├── python.exe / python311.dll / *.pyd            ← unzip embeddable python here
├── python311._pth                                 ← add . and Lib/site-packages entries
└── Lib/site-packages/
    ├── fastapi/ uvicorn/ pydantic/ paramiko/ …   ← pip install --target=./python/Lib/site-packages -r requirements.txt
```

After that prepend the folder to `PATH` at the top of [`start_daemon.bat`](../start_daemon.bat):

```batch
set PATH=%~dp0python;%PATH%
```
