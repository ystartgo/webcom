#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Webcom 系統與功能自我檢測工具 (System Self-Diagnostic Tool)
=========================================================
用途：自動化驗證 Webcom 關鍵核心功能，避免先前發生的基礎功能失靈問題：
  1. HTML 腳本語法 (Node.js --check)
  2. 核心全域函式完整性 (checkDaemonHealth, handleSend, initWTerm 等)
  3. UI 元素與原生標籤正確性 (label for, 無預防事件干擾)
  4. Python 相依套件完整度 (markitdown[all], fastapi, uvicorn, pymupdf 等)
  5. Port 8001 常駐服務即時健康狀態
  6. Microsoft MarkItDown 實機全格式轉檔驗證 (DOCX, HTML, CSV)
  7. 雙目錄檔案一致性雜湊比對 (C:\\Apps\\Webcom vs github\\)
"""

import os
import sys

# 確保 Windows 控制台使用 UTF-8 輸出，避免 CP950 特殊字元報錯
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8', errors='replace')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8', errors='replace')

import json
import base64
import hashlib
import tempfile
import subprocess
import urllib.request
import urllib.error

# Windows 控制台彩色輸出
os.system('')
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
BOLD = '\033[1m'
RESET = '\033[0m'

# 動態偵測工作目錄，相容跨機、可攜式 USB 或非 C:\Apps\Webcom 部署環境
_current_script_dir = os.path.dirname(os.path.abspath(__file__))
if os.path.basename(_current_script_dir).lower() == 'github':
    BASE_DIR = os.path.dirname(_current_script_dir)
else:
    BASE_DIR = _current_script_dir

GITHUB_DIR = os.path.join(BASE_DIR, 'github')
INDEX_HTML = os.path.join(BASE_DIR, 'index.html')

# 優先載入本機可攜式 Python 套件庫 (若存在，免全域 pip install)
_portable_sp = os.path.join(BASE_DIR, "python", "Lib", "site-packages")
if os.path.exists(_portable_sp) and _portable_sp not in sys.path:
    sys.path.insert(0, _portable_sp)

results = []

def record(category, test_name, passed, detail=""):
    results.append({
        "category": category,
        "name": test_name,
        "passed": passed,
        "detail": detail
    })
    status_icon = f"{GREEN}✔ 通過 (PASS){RESET}" if passed else f"{RED}✖ 異常 (FAIL){RESET}"
    print(f"  [{status_icon}] {BOLD}{test_name}{RESET}")
    if detail:
        color = GREEN if passed else RED
        print(f"        └─ {color}{detail}{RESET}")

def test_syntax():
    print(f"\n{CYAN}{BOLD}【1. HTML 與 JavaScript 腳本語法檢測】{RESET}")
    if not os.path.exists(INDEX_HTML):
        record("Syntax", "index.html 存在性檢查", False, f"找不到 {INDEX_HTML}")
        return

    try:
        from bs4 import BeautifulSoup
        with open(INDEX_HTML, 'r', encoding='utf-8', errors='ignore') as f:
            soup = BeautifulSoup(f.read(), 'html.parser')
        scripts = soup.find_all('script')
    except Exception as e:
        record("Syntax", "HTML 解析器檢驗", False, str(e))
        return

    # 檢驗 Node.js 是否可用
    has_node = False
    try:
        res = subprocess.run(['node', '-v'], capture_output=True, text=True)
        if res.returncode == 0:
            has_node = True
    except Exception:
        pass

    if not has_node:
        record("Syntax", "Node.js 語法檢查器", False, "系統未找到 Node.js，跳過進階 AST 檢查")
        return

    all_syntax_pass = True
    err_msgs = []
    inline_count = 0

    for idx, s in enumerate(scripts):
        if s.get('src'): continue
        code = s.string or ''
        if not code.strip(): continue
        inline_count += 1
        with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as tf:
            tf.write(code)
            tname = tf.name
        try:
            res = subprocess.run(['node', '--check', tname], capture_output=True, text=True)
            if res.returncode != 0:
                all_syntax_pass = False
                err_msgs.append(f"Script #{idx}: {res.stderr.strip()[:100]}")
        finally:
            try: os.unlink(tname)
            except Exception: pass

    record("Syntax", f"全檔案 {inline_count} 個行內 JavaScript 語法檢查", all_syntax_pass, 
           "100% 語法驗證無錯誤" if all_syntax_pass else " | ".join(err_msgs))

def test_core_functions():
    print(f"\n{CYAN}{BOLD}【2. 核心關鍵函式定義與全域暴露檢測】{RESET}")
    with open(INDEX_HTML, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    core_checks = [
        ("checkDaemonHealth 定義", "function checkDaemonHealth" in content or "checkDaemonHealth = async" in content),
        ("checkDaemonHealth 全域暴露", "window.checkDaemonHealth = checkDaemonHealth" in content),
        ("handleSend 定義", "async function handleSend" in content or "function handleSend" in content),
        ("handleSendMessage 定義", "function handleSendMessage" in content),
        ("initWTerm 終端機啟動函式", "async function initWTerm" in content or "function initWTerm" in content),
        ("processDocumentFile MarkItDown 轉檔函式", "async function processDocumentFile" in content),
        ("btn-send 監聽器綁定", "btn-send" in content and "addEventListener('click', handleSend)" in content),
    ]

    for name, ok in core_checks:
        record("CoreFunctions", name, ok, "函式結構完整" if ok else "缺少函式定義，將導致前端流程崩潰！")

def test_ui_elements():
    print(f"\n{CYAN}{BOLD}【3. UI 原生標籤與按鈕防禦性檢測】{RESET}")
    with open(INDEX_HTML, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    # 1. 圖片按鈕原生 label 檢查
    img_label_ok = ('<label for="file-upload-image"' in content) and ('id="btn-upload-image"' in content)
    record("UI", "圖片按鈕 HTML5 原生 <label for> 標籤", img_label_ok, 
           "原生 label 保證點擊觸發檔案視窗" if img_label_ok else "非原生 label，可能遭瀏覽器安全性阻擋")

    # 2. 文件按鈕原生 label 檢查
    doc_label_ok = ('<label for="file-upload-doc"' in content) and ('id="btn-upload-doc"' in content)
    record("UI", "文件按鈕 HTML5 原生 <label for> 標籤", doc_label_ok,
           "原生 label 保證點擊觸發檔案視窗" if doc_label_ok else "非原生 label，可能遭瀏覽器安全性阻擋")

    # 3. 確保沒有在按鈕上調用 e.preventDefault() 阻擋原生點擊
    no_prevent_img = 'btnUploadImage.onclick = (e) => {\n                e.preventDefault();' not in content
    no_prevent_doc = 'btnUploadDoc.onclick = (e) => {\n                e.preventDefault();' not in content
    record("UI", "上傳按鈕無阻擋預設事件 (No preventDefault)", no_prevent_img and no_prevent_doc,
           "原生點擊穿透無阻礙" if (no_prevent_img and no_prevent_doc) else "存在 e.preventDefault()，會干擾原生選檔視窗")

    # 4. 頂部 MarkItDown 獨立鏈結檢查
    nav_link_ok = '<a id="btn-open-markitdown"' in content and 'target="_blank"' in content
    record("UI", "頂部 MarkItDown 原生 <a> 標籤 (防 Popup Blocker)", nav_link_ok,
           "原生超連結開啟新分頁" if nav_link_ok else "使用 window.open，可能被瀏覽器阻擋彈出")

def test_python_deps():
    print(f"\n{CYAN}{BOLD}【4. Python 環境與 MarkItDown 依賴檢測】{RESET}")
    packages = [
        ("markitdown", "Microsoft MarkItDown 核心"),
        ("mammoth", "Word .docx 轉換依賴"),
        ("cobble", "Docx 格式相依"),
        ("pdfminer", "PDF 結構化提取依賴"),
        ("pdfplumber", "PDF 表格提取依賴"),
        ("pypdfium2", "PDF 渲染相依"),
        ("fastapi", "後端 API 伺服器框架"),
        ("uvicorn", "ASGI 服務引擎"),
        ("pymupdf", "PDF 多模態圖片抽取 (Vision)")
    ]

    for mod, desc in packages:
        try:
            __import__(mod)
            record("Dependencies", f"{mod} ({desc})", True, "已正確安裝")
        except ImportError:
            record("Dependencies", f"{mod} ({desc})", False, f"未安裝，請執行: pip install -r requirements.txt (或執行 install_dependencies.bat)")

def test_daemon_service():
    print(f"\n{CYAN}{BOLD}【5. 常駐服務 (Port 8001) 即時健康檢測】{RESET}")
    url = "http://127.0.0.1:8001/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Webcom-Diagnostic"})
        with urllib.request.urlopen(req, timeout=3) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            is_ok = data.get("status") == "online" or "service" in data
            record("Daemon", "Port 8001 /health 探針", is_ok, f"回應: {data}")
    except Exception as e:
        record("Daemon", "Port 8001 /health 探針", False, f"無法連線 (可能是常駐程式未啟動: {e})")

def test_markitdown_conversions():
    print(f"\n{CYAN}{BOLD}【6. Microsoft MarkItDown 實機轉檔驗證】{RESET}")
    api_url = "http://127.0.0.1:8001/tools/parse_document"

    test_cases = [
        ("HTML 結構與表格轉檔", "sample.html", "<h1>標題</h1><table><tr><th>項目</th><th>數值</th></tr><tr><td>CPU</td><td>100%</td></tr></table>", "markitdown"),
        ("CSV 表格結構化轉檔", "sample.csv", "產品,價格,庫存\n蘋果,30,500\n香蕉,20,300", "markitdown"),
        ("純文字與程式碼直轉", "sample.txt", "Webcom Diagnostic Test Data", "markitdown"),
    ]

    for title, fname, content, expected_engine in test_cases:
        b64 = base64.b64encode(content.encode('utf-8')).decode('ascii')
        payload = json.dumps({"filename": fname, "data_base64": b64}).encode('utf-8')
        try:
            req = urllib.request.Request(api_url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                status = data.get("status")
                engine = data.get("engine")
                md = data.get("markdown", "")
                passed = (status == "success" and engine == expected_engine and len(md) > 0)
                detail = f"Engine: {engine} | 字符長度: {len(md)} 字"
                record("MarkItDown", title, passed, detail)
        except Exception as e:
            record("MarkItDown", title, False, f"請求失敗: {e}")

    # 實機 DOCX 測試 (利用 python-docx 現場產生檔案)
    try:
        import docx, io
        doc = docx.Document()
        doc.add_heading('診斷報告標題', level=1)
        doc.add_paragraph('這是自我檢測自動產生的測試段落。')
        t = doc.add_table(rows=2, cols=2)
        t.cell(0, 0).text = '項目'
        t.cell(0, 1).text = '狀態'
        t.cell(1, 0).text = 'MarkItDown'
        t.cell(1, 1).text = '正常'
        buf = io.BytesIO()
        doc.save(buf)
        b64_docx = base64.b64encode(buf.getvalue()).decode('ascii')

        payload = json.dumps({"filename": "test.docx", "data_base64": b64_docx}).encode('utf-8')
        req = urllib.request.Request(api_url, data=payload, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            status = data.get("status")
            engine = data.get("engine")
            md = data.get("markdown", "")
            passed = (status == "success" and engine == "markitdown" and "|" in md)
            detail = f"Engine: {engine} | 表格標記: {'含 Markdown 表格' if '|' in md else '無表格'}"
            record("MarkItDown", "Word (.docx) 原生 Markdown 標題與表格", passed, detail)
    except Exception as e:
        record("MarkItDown", "Word (.docx) 原生 Markdown 標題與表格", False, f"測試異常: {e}")

def test_sync():
    print(f"\n{CYAN}{BOLD}【7. 雙目錄檔案一致性同步比對】{RESET}")
    if not os.path.exists(GITHUB_DIR):
        print(f"  {YELLOW}ℹ 獨立部署環境（未包含 github 子目錄），跳過雙目錄一致性比對{RESET}")
        return

    files_to_check = ['index.html', 'daemon.py', 'start_daemon.bat', 'README.md', 'diagnose_system.py', 'self_test.bat']

    for fn in files_to_check:
        p1 = os.path.join(BASE_DIR, fn)
        p2 = os.path.join(GITHUB_DIR, fn)

        if not os.path.exists(p1) or not os.path.exists(p2):
            record("Sync", f"{fn} 檔案存在性", False, "其中一側目錄缺少此檔案")
            continue

        h1 = hashlib.sha256(open(p1, 'rb').read()).hexdigest()
        h2 = hashlib.sha256(open(p2, 'rb').read()).hexdigest()

        match = (h1 == h2)
        record("Sync", f"{fn} 雙向雜湊比對", match, 
               f"SHA256: {h1[:12]}... (完全一致)" if match else "雜湊不符，需要同步！")

def main():
    print(f"{BOLD}================================================================{RESET}")
    print(f"{BOLD}{CYAN}      Webcom AI 控制台 — 系統與功能自我健康檢測工具 (v1.0.6)     {RESET}")
    print(f"{BOLD}================================================================{RESET}")

    test_syntax()
    test_core_functions()
    test_ui_elements()
    test_python_deps()
    test_daemon_service()
    test_markitdown_conversions()
    test_sync()

    print(f"\n{BOLD}================================================================{RESET}")
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    if failed == 0:
        print(f"{BOLD}{GREEN}🎉 全數通過！共 {total} 項測試全部正常，系統與基礎功能運作無虞！{RESET}")
    else:
        print(f"{BOLD}{RED}⚠️ 檢測完成：共 {total} 項測試，{passed} 項通過，{failed} 項異常！{RESET}")
        print(f"{YELLOW}請檢視上方標記為 [✖ 異常] 的項目進行修正。{RESET}")
    print(f"{BOLD}================================================================{RESET}\n")

    return 0 if failed == 0 else 1

if __name__ == '__main__':
    sys.exit(main())
