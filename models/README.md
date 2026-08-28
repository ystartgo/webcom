# /models — WebGPU LLM 權重存放區（本倉庫不隨附）

## 🈶 繁體中文說明

這個資料夾是 **WebGPU 瀏覽器本地推理引擎（WebLLM / MLC）** 會讀取的模型權重目錄。

因為單一 3B 模型的 shard 就超過 5 GB，**本 GitHub 倉庫 intentionally 不隨附任何模型權重**（也已寫入 `.gitignore`），請使用本專案根目錄內的下載腳本取得：

```powershell
# 在 webcom 根目錄執行
download_offline_models.bat
# 或 python download_offline_models.py
```

下載完成後，此資料夾應包含以下子目錄（每個子目錄內皆有 `mlc-chat-config.json`、`ndarray-cache.json` / `tensor-cache.json`、多個 `params_shard_N.bin`、`tokenizer.json/ config.json` 等）：

```
models/
├── Qwen2.5-0.5B-Instruct-q4f16_1-MLC/
├── Qwen2.5-1.5B-Instruct-q4f16_1-MLC/
├── Qwen2.5-3B-Instruct-q4f16_1-MLC/
├── Llama-3.2-1B-Instruct-q4f16_1-MLC/
└── SmolLM2-360M-Instruct-q0f16_1-MLC/
```

> 後端 Daemon（[daemon.py](../daemon.py)）同時會在此目錄提供 `/models/{model}/resolve/main/*` 靜態路由，讓 WebLLM 能以相容 HuggingFace 的路徑直接讀取權重，無需改成即時連線。

### 📁 對應的 WASM 引擎檔案

模型權重之外，每個量化版本還需要一個對應的 `*.wasm` 引擎檔（約數百 MB 至 1.8 GB），放在上一層 `../assets/` 目錄中，同樣由 `download_offline_models.bat` 自動放置。

---

## 🌐 English

This folder is where the **WebGPU browser-local inference engine (WebLLM / MLC)** loads model weights from.

A single 3B-model shard already exceeds 5 GB, so **this GitHub repo intentionally ships with NO model weights** (they are also excluded via `.gitignore`). Obtain them using the bundled download scripts in the project root:

```powershell
# run from the webcom root
download_offline_models.bat
# or  python download_offline_models.py
```

After a successful download this folder should contain the following sub-folders (each holds `mlc-chat-config.json`, `ndarray-cache.json` / `tensor-cache.json`, many `params_shard_N.bin`, `tokenizer.json / tokenizer_config.json`, etc.):

```
models/
├── Qwen2.5-0.5B-Instruct-q4f16_1-MLC/
├── Qwen2.5-1.5B-Instruct-q4f16_1-MLC/
├── Qwen2.5-3B-Instruct-q4f16_1-MLC/
├── Llama-3.2-1B-Instruct-q4f16_1-MLC/
└── SmolLM2-360M-Instruct-q0f16_1-MLC/
```

> The backend daemon ([daemon.py](../daemon.py)) also serves this folder under `/models/{model}/resolve/main/*` so WebLLM can consume weights via HuggingFace-compatible paths, fully offline.

### 📁 Companion WASM engine files

Each quantization still needs its matching `*.wasm` engine (hundreds of MB – 1.8 GB) in the parent folder [`../assets/`](../assets/). The same `download_offline_models.bat` places them there automatically.
