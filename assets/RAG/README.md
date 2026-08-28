# /assets/RAG — RAG 靜態知識庫資源（範例 / 快取）

## 🈶 繁體中文說明

此資料夾用於存放 **RAG 知識庫管理員** 相關的靜態資源，包含但不限於：

- 🖼️ 使用者自行上傳、作為知識庫文件附圖的 SVG / PNG 資源
- 📄 離線情境下預先寫好的 Markdown / TXT / JSON 文件範本（可直接在「上傳知識文件」中選取）
- 💾 RAG 分段與向量 embedding 的離線快取檔（若後續導入 Chroma / FAISS 本地快取時使用）

內建範例：

```
assets/RAG/
└── Animals/
    └── cat_00001.svg   ← 示範向量圖
```

### ⚠️ 與「上傳到 RAG 面板」的文件快取不同

在前端「RAG Base」中上傳的文件，**預設不會寫入此資料夾**，而是直接存在瀏覽器 `localStorage` / IndexedDB 中（單檔使用）。

若你的使用情境需要 **多位使用者共用同一組靜態知識文件**，建議將 `.md / .txt / .json` 檔案放在 `assets/RAG/` 目錄下，後端 Daemon 會自動以靜態檔案方式提供。

---

## 🌐 English

This folder holds static assets used by the **RAG Knowledge Base Manager**:

- 🖼️ User-supplied figures (SVG / PNG) referenced in knowledge documents
- 📄 Pre-written offline Markdown / TXT / JSON document templates that you can later re-select in the *Upload File* dialog
- 💾 Optional offline chunk / vector-embedding cache (for future Chroma / FAISS local cache support)

Built-in sample:

```
assets/RAG/
└── Animals/
    └── cat_00001.svg   ← sample vector graphic
```

### ⚠️ Distinct from the in-browser RAG upload cache

Documents uploaded through the front-end **RAG Base** panel are NOT written here by default. They live inside browser `localStorage` / IndexedDB on a per-user basis.

If your use-case calls for **a shared static knowledge library across multiple end-users**, drop your `.md / .txt / .json` files into this folder — the backend daemon serves them as static files automatically.
