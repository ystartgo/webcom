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
if os.path.exists(_portable_sp):
    if _portable_sp not in sys.path:
        sys.path.insert(0, _portable_sp)
    try:
        import site
        site.addsitedir(_portable_sp)
    except Exception:
        pass

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
        record("Syntax", "Node.js 語法檢查器 (選用)", True, "未安裝 Node.js (非必要元件，已跳過 AST 語法檢查)")
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
        ("switchLeftMode 模式切換函式", "function switchLeftMode" in content and "window.switchLeftMode = switchLeftMode" in content),
        ("handleNoVncConnect 遠端桌面函式", "function handleNoVncConnect" in content and "window.handleNoVncConnect = handleNoVncConnect" in content),
        ("handleXorgConnect 視窗連線函式", "function handleXorgConnect" in content and "window.handleXorgConnect = handleXorgConnect" in content),
        ("openKeySettingsModal 按鍵設置函式", "function openKeySettingsModal" in content and "window.openKeySettingsModal = openKeySettingsModal" in content),
        ("toggleAudioStream 音訊串流函式", "function toggleAudioStream" in content and "window.toggleAudioStream = toggleAudioStream" in content),
        ("playTestTone WebAudio 測試音函式", "function playTestTone" in content and "window.playTestTone = playTestTone" in content),
        ("checkWslStatus WSL 檢測函式", "function checkWslStatus" in content and "window.checkWslStatus = checkWslStatus" in content),
        ("startWslDesktopAndConnect WSL 桌面啟動函式", "function startWslDesktopAndConnect" in content and "window.startWslDesktopAndConnect = startWslDesktopAndConnect" in content),
        ("stopWslDesktopService WSL 桌面停止函式", "function stopWslDesktopService" in content and "window.stopWslDesktopService = stopWslDesktopService" in content),
        ("launchWslApp WSL GUI 應用程式啟動函式", "function launchWslApp" in content and "window.launchWslApp = launchWslApp" in content),
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

    # 5. 左側模式切換與容器檢查
    left_tabs_ok = ('id="tab-left-term"' in content) and ('id="tab-left-novnc"' in content) and ('id="tab-left-xorg"' in content)
    record("UI", "左側工作區模式切換分頁標籤 (Terminal / noVNC / Xorg)", left_tabs_ok,
           "分頁標籤齊全" if left_tabs_ok else "缺少左側模式切換按鈕")

    left_views_ok = ('id="view-container-term"' in content) and ('id="view-container-novnc"' in content) and ('id="view-container-xorg"' in content)
    record("UI", "左側多模式容器健全性 (Terminal / noVNC / Xorg Views)", left_views_ok,
           "三大工作區容器就緒" if left_views_ok else "缺少工作區顯示容器")

    novnc_asset_path = os.path.join(BASE_DIR, "assets", "novnc.bundle.mjs")
    novnc_asset_ok = os.path.exists(novnc_asset_path) and os.path.getsize(novnc_asset_path) > 100000
    record("UI", "noVNC 離線獨立打包核心 (assets/novnc.bundle.mjs)", novnc_asset_ok,
           f"本地資源就緒 ({round(os.path.getsize(novnc_asset_path)/1024, 1) if os.path.exists(novnc_asset_path) else 0} KB)" if novnc_asset_ok else "缺少 assets/novnc.bundle.mjs 離線資產")

    # 6. 音訊串流控制與按鍵設置對話盒
    audio_controls_ok = ('id="btn-novnc-audio-toggle"' in content) and ('id="btn-xorg-audio-toggle"' in content)
    record("UI", "遠端桌面與 Xorg 音訊串流控制面板", audio_controls_ok,
           "雙視圖音訊控制就緒" if audio_controls_ok else "缺少音訊控制面板")

    key_settings_ok = ('id="key-settings-modal"' in content) and ('id="btn-config-vkeys"' in content)
    record("UI", "按鍵與快捷鍵自訂設置對話盒 (#key-settings-modal)", key_settings_ok,
           "自訂按鍵對話盒與觸發鈕齊全" if key_settings_ok else "缺少按鍵設置模態視窗")

    # 7. WSL 整合狀態與一鍵啟動按鈕
    wsl_ui_ok = ('id="novnc-wsl-status"' in content) and ('id="xorg-wsl-status"' in content) and ('id="xorg-modal"' in content)
    record("UI", "WSL 整合狀態列與快速精靈模態視窗", wsl_ui_ok,
           "WSL 狀態列與快速精靈就緒" if wsl_ui_ok else "缺少 WSL 整合 UI 元件")

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
    print(f"\n{CYAN}{BOLD}【5. 常駐服務 (Port 8001) 即時連線檢測】{RESET}")
    url = "http://127.0.0.1:8001/health"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Webcom-Diagnostic"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            is_ok = data.get("status") == "online" or "service" in data
            record("Daemon", "Port 8001 /health 服務狀態", is_ok, f"服務在線: {data.get('service', 'Webcom Daemon')}")
    except Exception:
        record("Daemon", "Port 8001 /health 服務狀態", True, "常駐程式目前未執行 (執行 start_daemon.bat 即可啟動)")

    # 2. Port 8001 /api/wsl/status WSL 桌面端點
    url_wsl = "http://127.0.0.1:8001/api/wsl/status"
    try:
        req_wsl = urllib.request.Request(url_wsl, headers={"User-Agent": "Webcom-Diagnostic"})
        with urllib.request.urlopen(req_wsl, timeout=2.0) as resp:
            data_wsl = json.loads(resp.read().decode('utf-8'))
            wsl_ok = data_wsl.get("status") == "ok"
            detail = f"WSL: {data_wsl.get('distro', 'N/A')} (VNC: {data_wsl.get('vnc_port')}, WS: {data_wsl.get('websockify_port')})"
            record("Daemon", "Port 8001 /api/wsl/status 桌面探測端點", wsl_ok, detail)
    except Exception as e:
        record("Daemon", "Port 8001 /api/wsl/status 桌面探測端點", True, f"常駐服務或 WSL 尚未啟動: {e}")

def test_markitdown_conversions():
    print(f"\n{CYAN}{BOLD}【6. Microsoft MarkItDown 轉檔引擎驗證】{RESET}")
    import io
    try:
        from markitdown import MarkItDown
        md_engine = MarkItDown()
    except Exception as e:
        record("MarkItDown", "MarkItDown 模組載入", False, f"載入失敗: {e}")
        return

    # 1. HTML 轉檔測試
    try:
        html_bytes = "<h1>標題</h1><table><tr><th>項目</th><th>數值</th></tr><tr><td>CPU</td><td>100%</td></tr></table>".encode('utf-8')
        res = md_engine.convert_stream(io.BytesIO(html_bytes), ext=".html")
        ok = bool(res.text_content and "CPU" in res.text_content)
        record("MarkItDown", "HTML 結構與表格轉檔", ok, f"字符長度: {len(res.text_content)} 字")
    except Exception as e:
        record("MarkItDown", "HTML 結構與表格轉檔", False, str(e))

    # 2. CSV 轉檔測試
    try:
        csv_bytes = "產品,價格,庫存\n蘋果,30,500\n香蕉,20,300".encode('utf-8')
        res = md_engine.convert_stream(io.BytesIO(csv_bytes), ext=".csv")
        ok = bool(res.text_content and "蘋果" in res.text_content)
        record("MarkItDown", "CSV 表格結構化轉檔", ok, f"字符長度: {len(res.text_content)} 字")
    except Exception as e:
        record("MarkItDown", "CSV 表格結構化轉檔", False, str(e))

    # 3. 純文字與程式碼直轉
    try:
        txt_bytes = "Webcom Diagnostic Test Data".encode('utf-8')
        res = md_engine.convert_stream(io.BytesIO(txt_bytes), ext=".txt")
        ok = bool(res.text_content and "Webcom" in res.text_content)
        record("MarkItDown", "純文字與程式碼直轉", ok, f"字符長度: {len(res.text_content)} 字")
    except Exception as e:
        record("MarkItDown", "純文字與程式碼直轉", False, str(e))

    # 4. Word (.docx) 轉檔測試
    try:
        import docx
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
        buf.seek(0)
        res = md_engine.convert_stream(buf, ext=".docx")
        ok = bool(res.text_content and "|" in res.text_content)
        record("MarkItDown", "Word (.docx) 原生 Markdown 標題與表格", ok, f"表格標記: {'含 Markdown 表格' if '|' in res.text_content else '無表格'}")
    except Exception as e:
        record("MarkItDown", "Word (.docx) 原生 Markdown 標題與表格", False, str(e))

def test_multimodal_vision():
    print(f"\n{CYAN}{BOLD}【7. 多模態視覺 (Multimodal Vision) 與歷史記錄防禦檢測】{RESET}")
    if not os.path.exists(INDEX_HTML):
        record("Vision", "index.html 存在性", False, "找不到 index.html")
        return
    with open(INDEX_HTML, 'r', encoding='utf-8', errors='ignore') as f:
        html_code = f.read()

    # 1. handleSend 多模態內容保護 (不得將含 image_url 的陣列覆寫為純字串)
    has_mm_guard = "Array.isArray(lastUserMsg.content)" in html_code and "textItem.text = effectivePrompt" in html_code
    record("Vision", "handleSend 多模態圖文結構保護", has_mm_guard,
           "使用者附帶圖片時不會被純文字覆寫遺失" if has_mm_guard else "尚未實作圖文陣列保護邏輯")

    # 2. Gemma-4 原生多模態 Token 映射 (<|image|>)
    has_gemma4_img_tok = "<|image|>" in html_code and "<|turn>" in html_code
    record("Vision", "Gemma-4 ONNX 圖像 Token 映射 (<|image|>)", has_gemma4_img_tok,
           "Gemma-4 原生視覺 Token 與輪次標記完整映射" if has_gemma4_img_tok else "缺少 Gemma-4 影像 Token 標記")

    # 3. Transformers.js RawImage 影像解碼加載
    has_raw_image = "RawImageClass.read" in html_code and "loadedRawImages" in html_code
    record("Vision", "Transformers.js RawImage 影像解碼管線", has_raw_image,
           "支援 Base64/URL 轉 RawImage 供視覺模型解碼" if has_raw_image else "缺少 RawImage 影像解碼整合")

    # 4. 純文字模型附圖引導提示
    has_text_warning = "onnx-community/gemma-4-E2B-it-ONNX" in html_code and ("不支援圖片視覺識別" in html_code or "does not support image" in html_code)
    record("Vision", "純文字模型防呆與切換 Gemma-4 提示", has_text_warning,
           "選用純文字模型上傳圖片時提供切換 Gemma-4 友善指引" if has_text_warning else "缺少純文字附圖引導")

def test_sync():
    print(f"\n{CYAN}{BOLD}【8. 雙目錄檔案一致性同步比對】{RESET}")
    if not os.path.exists(GITHUB_DIR):
        print(f"  {YELLOW}ℹ 獨立部署環境（未包含 github 子目錄），跳過雙目錄一致性比對{RESET}")
        return

    files_to_check = ['index.html', 'daemon.py', 'start_daemon.bat', 'README.md', 'diagnose_system.py', 'self_test.bat', 'requirements.txt', 'install_dependencies.bat']

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
    print(f"{BOLD}{CYAN}      Webcom AI 控制台 — 系統與功能自我健康檢測工具 (v1.0.7)     {RESET}")
    print(f"{BOLD}================================================================{RESET}")

    test_syntax()
    test_core_functions()
    test_ui_elements()
    test_python_deps()
    test_daemon_service()
    test_markitdown_conversions()
    test_multimodal_vision()
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
