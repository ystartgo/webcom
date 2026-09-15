import os
import sys
import re
import shutil
import zipfile

# Ensure standard UTF-8 console output (prevent CP950 / Big5 encoding errors on Windows)
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

BASE_DIR = "C:/Apps/Webcom"
EXT_DIR = os.path.join(BASE_DIR, "extension")
INDEX_PATH = os.path.join(BASE_DIR, "index.html")

def build_extension():
    print("==================================================")
    print("      Webcom Chrome Extension (MV3) Builder       ")
    print("==================================================")
    
    os.makedirs(EXT_DIR, exist_ok=True)
    os.makedirs(os.path.join(EXT_DIR, "icons"), exist_ok=True)
    os.makedirs(os.path.join(EXT_DIR, "assets"), exist_ok=True)
    os.makedirs(os.path.join(EXT_DIR, "pyodide"), exist_ok=True)

    with open(INDEX_PATH, "r", encoding="utf-8") as f:
        html = f.read()

    # 1. 抽取所有行內腳本 (<script>...</script> 且無 src)
    script_pattern = re.compile(r'<script(?:\s+type="[^"]*")?>([\s\S]*?)</script>', re.IGNORECASE)
    extracted_scripts = []

    def script_extractor(match):
        code = match.group(1).strip()
        if code:
            # 移除在 Chrome Extension 外部腳本中會拋出 DOMException 與違反 CSP 的 document.write CDN 備援碼
            code = re.sub(r"document\.write\(['\"]<script src=['\"]https://[^'\"]+['\"]><\\/script>['\"]\);?", "// [MV3 Cleaned] CDN document.write removed", code)
            extracted_scripts.append(code)
        return "" # 從 HTML 中移除行內腳本

    # 替換不含 src 的 script 標籤
    # 注意：保留有 src 的標籤如 <script src="./assets/tailwindcss.js">
    clean_html = re.sub(
        r'<script(?![^>]*\bsrc=)[^>]*>([\s\S]*?)</script>',
        script_extractor,
        html,
        flags=re.IGNORECASE
    )

    # 合併為 extension/app.js
    app_js_content = "\n\n/* ── Extracted Webcom Application Logic for Chrome MV3 ── */\n\n" + "\n\n".join(extracted_scripts)
    app_js_path = os.path.join(EXT_DIR, "app.js")
    with open(app_js_path, "w", encoding="utf-8") as f:
        f.write(app_js_content)
    print(f"  [✔] 成功抽取行內腳本至 {app_js_path} ({len(app_js_content):,} 字元)")

    # 2. 將 HTML 內的行內事件處理器轉換為宣告式 data-on-* 屬性 (合規 Chrome MV3 CSP)
    event_replacements = [
        (r'\bonclick=(["\'])(.*?)\1', r'data-on-click=\1\2\1'),
        (r'\boninput=(["\'])(.*?)\1', r'data-on-input=\1\2\1'),
        (r'\bonkeydown=(["\'])(.*?)\1', r'data-on-keydown=\1\2\1'),
        (r'\bonchange=(["\'])(.*?)\1', r'data-on-change=\1\2\1')
    ]

    for pattern, repl in event_replacements:
        clean_html = re.sub(pattern, repl, clean_html, flags=re.IGNORECASE)

    # 3. 確保 html2canvas 引用本機資產
    clean_html = clean_html.replace(
        'https://cdn.jsdelivr.net/npm/html2canvas@1.4.1/dist/html2canvas.min.js',
        './assets/html2canvas.min.js'
    )

    # 4. 在 </body> 結束前注入合規外部腳本引用
    script_injections = '''
    <!-- Chrome Extension MV3 CSP-Compliant Script Imports -->
    <script src="event_bridge.js"></script>
    <script src="pyodide/pyodide_runner.js"></script>
    <script src="app.js"></script>
</body>'''
    
    clean_html = re.sub(r'</body>', script_injections, clean_html, flags=re.IGNORECASE)

    ext_index_path = os.path.join(EXT_DIR, "index.html")
    with open(ext_index_path, "w", encoding="utf-8") as f:
        f.write(clean_html)
    print(f"  [✔] 成功生成 Chrome MV3 合規入口 {ext_index_path}")

    # 5. 複製必備靜態資產 (JS/CSS)
    src_assets = os.path.join(BASE_DIR, "assets")
    dst_assets = os.path.join(EXT_DIR, "assets")
    essential_assets = [
        "tailwindcss.js",
        "lucide.min.js",
        "marked.min.js",
        "html2canvas.min.js",
        "wterm.bundle.js",
        "wterm.css",
        "novnc.bundle.mjs",
        "webllm.bundle.js"
    ]
    for asset in essential_assets:
        s_path = os.path.join(src_assets, asset)
        d_path = os.path.join(dst_assets, asset)
        if os.path.exists(s_path):
            shutil.copy2(s_path, d_path)
    print("  [✔] 成功同步必備 assets (Tailwind, Lucide, Marked, WTerm, noVNC, WebLLM, html2canvas)")

    # 6. 同步 pyodide 子專案核心
    src_pyodide = os.path.join(BASE_DIR, "pyodide")
    dst_pyodide = os.path.join(EXT_DIR, "pyodide")
    for item in os.listdir(src_pyodide):
        s_item = os.path.join(src_pyodide, item)
        d_item = os.path.join(dst_pyodide, item)
        if os.path.isfile(s_item):
            shutil.copy2(s_item, d_item)
        elif os.path.isdir(s_item) and item == "dist":
            shutil.copytree(s_item, d_item, dirs_exist_ok=True)
    print("  [✔] 成功同步 Pyodide 獨立子專案腳本至 extension/pyodide")

    # 7. 打包為 webcom_chrome_extension.zip
    zip_path = os.path.join(BASE_DIR, "webcom_chrome_extension.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(EXT_DIR):
            for file in files:
                abs_path = os.path.join(root, file)
                rel_path = os.path.relpath(abs_path, EXT_DIR)
                zf.write(abs_path, rel_path)
    print(f"  [✔] 成功建立可發布之擴充功能壓縮包: {zip_path} ({os.path.getsize(zip_path):,} bytes)")
    print("==================================================")
    print("🎉 Chrome 擴充功能建構完成！可在 chrome://extensions 開啟未封裝載入。")
    print("==================================================")

if __name__ == "__main__":
    build_extension()
