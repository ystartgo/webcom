import os
import sys
import subprocess
import shutil

# Ensure working directory is always script directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Ensure standard UTF-8 console output and environment (prevent CP950 / Big5 encoding errors)
os.environ["PYTHONIOENCODING"] = "utf-8"
os.environ["PYTHONUTF8"] = "1"
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
if hasattr(sys.stderr, 'reconfigure'):
    try:
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Support windowless execution (pythonw / hidden background service)
if sys.stdout is None or sys.stderr is None:
    try:
        _log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daemon.log")
        _log_f = open(_log_path, "a", encoding="utf-8", buffering=1)
        if sys.stdout is None:
            sys.stdout = _log_f
        if sys.stderr is None:
            sys.stderr = _log_f
    except Exception:
        pass
if os.path.dirname(os.path.abspath(__file__)) not in sys.path:
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 確保載入 Webcom 可攜式環境的 site-packages (支援 markitdown、mammoth、pdfminer 等)
_portable_sp = os.path.join(os.path.dirname(os.path.abspath(__file__)), "python", "Lib", "site-packages")
if os.path.exists(_portable_sp):
    if _portable_sp not in sys.path:
        sys.path.insert(0, _portable_sp)
    try:
        import site
        site.addsitedir(_portable_sp)
    except Exception:
        pass
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="Webcom Multi-Protocol Backend Daemon", version="1.0.8")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Type", "X-Original-Url"],
)

@app.middleware("http")
async def add_security_headers_middleware(request: Request, call_next):
    response: Response = await call_next(request)
    path = request.url.path
    if path.startswith("/markitdown") or path.startswith("/api/fetch-url"):
        response.headers["Cross-Origin-Opener-Policy"] = "same-origin"
        response.headers["Cross-Origin-Embedder-Policy"] = "require-corp"
        response.headers["Cross-Origin-Resource-Policy"] = "cross-origin"
    return response

models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models")
os.makedirs(models_dir, exist_ok=True)

from fastapi.responses import FileResponse

@app.get("/models/{model_name}/resolve/main/{filepath:path}")
def serve_model_resolve_main(model_name: str, filepath: str):
    """相容 WebLLM 請求 HuggingFace resolve/main 格式路徑"""
    target = os.path.join(models_dir, model_name, filepath)
    if os.path.exists(target) and os.path.isfile(target):
        return FileResponse(target)
    if filepath == "tensor-cache.json":
        fallback = os.path.join(models_dir, model_name, "ndarray-cache.json")
        if os.path.exists(fallback) and os.path.isfile(fallback):
            return FileResponse(fallback)
    raise HTTPException(status_code=404, detail=f"File not found: {filepath}")


app.mount("/models", StaticFiles(directory=models_dir), name="models")


# ── 根目錄靜態服務 (index.html 透過 http://127.0.0.1:8001 開啟，解決 file:// Cache API 限制) ──
webcom_dir = os.path.dirname(os.path.abspath(__file__))

@app.get("/")
def serve_index():
    """提供 Webcom index.html 根頁面，讓瀏覽器可以透過 HTTP 協議存取，解決 WebGPU Cache API 在 file:// 下被封鎖的問題"""
    from fastapi.responses import FileResponse
    index_path = os.path.join(webcom_dir, "index.html")
    if os.path.exists(index_path):
        return FileResponse(index_path, media_type="text/html")
    raise HTTPException(status_code=404, detail="index.html not found")

# 掛載 assets 子目錄（JS/圖片等靜態資源）
assets_dir = os.path.join(webcom_dir, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

# 掛載 rag_docs 子目錄 (儲存 PDF/文件轉換後之 Markdown 文件)
rag_docs_dir = os.path.join(webcom_dir, "rag_docs")
os.makedirs(rag_docs_dir, exist_ok=True)
app.mount("/rag_docs", StaticFiles(directory=rag_docs_dir), name="rag_docs")

# 掛載 MarkItDown Website (提供 http://127.0.0.1:8001/markitdown/)
markitdown_dir = os.path.join(webcom_dir, "markitdown")
if not os.path.exists(markitdown_dir):
    markitdown_dir = os.path.abspath(os.path.join(webcom_dir, "..", "markitdown-website"))
if not os.path.exists(markitdown_dir):
    markitdown_dir = r"C:\Apps\markitdown-website"

if os.path.exists(markitdown_dir):
    import mimetypes
    mimetypes.add_type("application/wasm", ".wasm")
    mimetypes.add_type("application/octet-stream", ".whl")
    app.mount("/markitdown", StaticFiles(directory=markitdown_dir, html=True), name="markitdown")

# ── URL 代理與 SSRF 防護 (/api/fetch-url) ──────────────────────────────────
import ipaddress, socket, urllib.request, urllib.parse

def _is_private_ip(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
        return addr.is_private or addr.is_loopback or addr.is_link_local or addr.is_reserved or addr.is_multicast
    except Exception:
        return True

@app.get("/api/fetch-url")
def fetch_url(url: str):
    if not url:
        raise HTTPException(status_code=400, detail="缺少 url 參數")
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in ["http", "https"]:
        raise HTTPException(status_code=400, detail="只允許 http 與 https 協定")
    hostname = parsed.hostname
    if not hostname:
        raise HTTPException(status_code=400, detail="無效的網址")
    try:
        addrinfo = socket.getaddrinfo(hostname, None)
        for ai in addrinfo:
            if _is_private_ip(ai[4][0]):
                raise HTTPException(status_code=403, detail="禁止存取內部或私有網路位址 (SSRF 防護)")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"網址解析失敗: {e}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 MarkItDown-Proxy/1.0",
        "Accept": "*/*",
    }
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as resp:
            content_type = resp.headers.get("Content-Type", "application/octet-stream")
            content = resp.read()
            if len(content) > 50 * 1024 * 1024:
                raise HTTPException(status_code=413, detail="檔案超過 50MB 上限")
            return Response(
                content=content,
                media_type=content_type,
                headers={
                    "Content-Type": content_type,
                    "X-Original-Url": url,
                    "Access-Control-Expose-Headers": "Content-Type, X-Original-Url"
                }
            )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"抓取網址失敗: {e}")

# ── Microsoft MarkItDown 轉檔 API ──────────────────────────────────────────
class MarkItDownConvertRequest(BaseModel):
    filename: str
    data_base64: str


def save_converted_markdown(filename: str, markdown_content: str):
    """
    將 MarkItDown / PDF 轉檔後的 Markdown 永久儲存至本機檔案系統：
    1. C:\Apps\Webcom\rag_docs\<filename>.md (使用者最直覺的一級資料夾)
    2. C:\Apps\Webcom\assets\RAG\Converted\<filename>.md (RAG 知識庫內建歸檔資料夾)
    """
    stem = os.path.splitext(filename)[0]
    safe_stem = "".join(c for c in stem if c.isalnum() or c in (" ", "-", "_", "(", ")", ".", "（", "）", "【", "】")).strip() or "document"
    md_filename = f"{safe_stem}.md"

    rag_docs_dir = os.path.join(webcom_dir, "rag_docs")
    os.makedirs(rag_docs_dir, exist_ok=True)
    rag_converted_dir = os.path.join(webcom_dir, "assets", "RAG", "Converted")
    os.makedirs(rag_converted_dir, exist_ok=True)

    path_root = os.path.join(rag_docs_dir, md_filename)
    path_conv = os.path.join(rag_converted_dir, md_filename)

    try:
        with open(path_root, "w", encoding="utf-8", errors="replace") as f_out:
            f_out.write(markdown_content)
        with open(path_conv, "w", encoding="utf-8", errors="replace") as f_out:
            f_out.write(markdown_content)
        logging.info(f"MarkItDown converted {filename} -> saved to {path_root} and {path_conv}")
    except Exception as e:
        logging.warning(f"Failed to persist converted markdown: {e}")

    return {
        "saved_path": os.path.abspath(path_conv).replace("\\", "/"),
        "saved_root_path": os.path.abspath(path_root).replace("\\", "/"),
        "saved_filename": md_filename,
        "download_url": f"/rag_docs/{md_filename}"
    }

@app.post("/api/convert")
@app.post("/api/convert_markitdown")
def convert_markitdown(req: MarkItDownConvertRequest):
    try:
        from markitdown import MarkItDown
    except ImportError:
        raise HTTPException(status_code=500, detail="本地未安裝 markitdown 套件")

    raw_b64 = req.data_base64
    if "base64," in raw_b64:
        raw_b64 = raw_b64.split("base64,", 1)[1]
    try:
        file_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Base64 解碼失敗: {e}")

    ext = os.path.splitext(req.filename)[1] or ".txt"
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
            f.write(file_bytes)
            temp_path = f.name
        md_engine = MarkItDown()
        result = md_engine.convert(temp_path)
        markdown_text = result.text_content or ""
        title = getattr(result, "title", None) or os.path.splitext(req.filename)[0]
        save_info = save_converted_markdown(req.filename, markdown_text)
        return {
            "status": "success",
            "filename": req.filename,
            "title": title,
            "markdown": markdown_text,
            "charCount": len(markdown_text),
            "lineCount": len(markdown_text.splitlines()),
            **save_info
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"MarkItDown 轉換失敗: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try: os.remove(temp_path)
            except Exception: pass


# ── PCB DXF <-> GeoJSON 高精度微型尺寸轉檔 API ─────────────────────────────────
class PcbDxfToGeoJsonRequest(BaseModel):
    filename: Optional[str] = "pcb.dxf"
    dxf_content: Optional[str] = None
    data_base64: Optional[str] = None
    unit: Optional[str] = "mm"
    tolerance: Optional[float] = 0.01
    precision: Optional[int] = 6

class PcbGeoJsonToDxfRequest(BaseModel):
    geojson: dict
    filename: Optional[str] = "pcb_converted.dxf"
    unit: Optional[str] = "mm"

class PcbDxfAnalyzeRequest(BaseModel):
    dxf_content: Optional[str] = None
    data_base64: Optional[str] = None


@app.post("/api/pcb/dxf2geojson")
def api_pcb_dxf2geojson(req: PcbDxfToGeoJsonRequest):
    """
    將 PCB DXF 格式轉檔為高精度 GeoJSON FeatureCollection：
    - 精確保留微米級幾何特徵 (BGA 焊盤、0.1mm 走線、爬電間距)
    - 重構圓角與走線弧度 (Bulge 圓弧精算)
    - 完整提取 Edge.Cuts、F.Cu、Drill、F.SilkS 等電路板圖層
    """
    try:
        from scripts.pcb_dxf_geojson import PcbDxfGeoJsonConverter
        converter = PcbDxfGeoJsonConverter(
            target_unit=req.unit or "mm",
            default_tolerance=req.tolerance or 0.01,
            precision=req.precision or 6
        )

        dxf_bytes = None
        if req.data_base64:
            raw_b64 = req.data_base64
            if "base64," in raw_b64:
                raw_b64 = raw_b64.split("base64,", 1)[1]
            dxf_bytes = base64.b64decode(raw_b64)
        elif req.dxf_content:
            dxf_bytes = req.dxf_content.encode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="請提供 dxf_content 或 data_base64")

        geojson_result = converter.dxf_to_geojson(dxf_bytes)
        return {
            "status": "success",
            "filename": req.filename,
            "data": geojson_result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PCB DXF 轉換失敗: {e}")


@app.post("/api/pcb/analyze")
def api_pcb_analyze(req: PcbDxfAnalyzeRequest):
    """
    快速分析 PCB DXF 電路板尺寸、面積 (mm² / cm²) 與圖層實體統計
    """
    try:
        from scripts.pcb_dxf_geojson import analyze_pcb_dxf
        dxf_bytes = None
        if req.data_base64:
            raw_b64 = req.data_base64
            if "base64," in raw_b64:
                raw_b64 = raw_b64.split("base64,", 1)[1]
            dxf_bytes = base64.b64decode(raw_b64)
        elif req.dxf_content:
            dxf_bytes = req.dxf_content.encode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="請提供 dxf_content 或 data_base64")

        analysis = analyze_pcb_dxf(dxf_bytes)
        return {
            "status": "success",
            "data": analysis
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PCB 分析失敗: {e}")


@app.post("/api/pcb/geojson2dxf")
def api_pcb_geojson2dxf(req: PcbGeoJsonToDxfRequest):
    """
    將 GeoJSON FeatureCollection 重新匯出為標準 AutoCAD DXF 檔案
    """
    temp_path = None
    try:
        from scripts.pcb_dxf_geojson import PcbDxfGeoJsonConverter
        converter = PcbDxfGeoJsonConverter(target_unit=req.unit or "mm")

        with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False) as f:
            temp_path = f.name

        converter.geojson_to_dxf(req.geojson, temp_path)
        with open(temp_path, "r", encoding="utf-8", errors="ignore") as f:
            dxf_text = f.read()

        return {
            "status": "success",
            "filename": req.filename,
            "dxf_content": dxf_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GeoJSON 轉 DXF 失敗: {e}")
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass


@app.get("/api/local_models")
def get_local_models():
    """Detect and return locally downloaded WebLLM model folders"""
    installed = []
    if os.path.exists(models_dir):
        for item in os.listdir(models_dir):
            item_path = os.path.join(models_dir, item)
            if os.path.isdir(item_path):
                # Check for mlc-chat-config.json or ndarray-cache.json
                has_config = os.path.exists(os.path.join(item_path, "mlc-chat-config.json")) or os.path.exists(os.path.join(item_path, "ndarray-cache.json"))
                size_mb = 0
                try:
                    total_bytes = sum(os.path.getsize(os.path.join(item_path, f)) for f in os.listdir(item_path) if os.path.isfile(os.path.join(item_path, f)))
                    size_mb = round(total_bytes / (1024 * 1024), 1)
                except Exception:
                    pass
                installed.append({
                    "id": item,
                    "name": item,
                    "ready": has_config,
                    "size_mb": size_mb,
                    "url": f"http://127.0.0.1:8001/models/{item}/"
                })
    return {"models": installed}


@app.get("/api/vnc/probe")
def probe_vnc_port(host: str = "127.0.0.1", port: int = 6080):
    """探測特定 TCP 主機與埠號是否處於監聽中 (供 noVNC / websockify / Xorg 連線診斷使用)"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        err = s.connect_ex((host, int(port)))
        is_open = (err == 0)
        return {
            "status": "ok",
            "host": host,
            "port": int(port),
            "open": is_open,
            "message": "Port is listening and reachable" if is_open else f"Port is closed or unreachable (code: {err})"
        }
    except Exception as ex:
        return {
            "status": "error",
            "host": host,
            "port": int(port),
            "open": False,
            "message": str(ex)
        }
    finally:
        try:
            s.close()
        except Exception:
            pass


@app.get("/api/audio/probe")
def probe_audio_port(host: str = "127.0.0.1", port: int = 8000):
    """探測音訊串流伺服器 (PulseAudio/HTTP/GStreamer) 埠號是否處於監聽中"""
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(1.0)
    try:
        err = s.connect_ex((host, int(port)))
        is_open = (err == 0)
        return {
            "status": "ok",
            "host": host,
            "port": int(port),
            "open": is_open,
            "message": "Audio stream port is listening" if is_open else f"Audio port is closed or unreachable (code: {err})"
        }
    except Exception as ex:
        return {
            "status": "error",
            "host": host,
            "port": int(port),
            "open": False,
            "message": str(ex)
        }
    finally:
        try:
            s.close()
        except Exception:
            pass


@app.get("/api/audio/stream")
def proxy_audio_stream(url: str = "http://127.0.0.1:8000/audio"):
    """代理後端音訊串流 (MP3/OGG/WAV) 避免瀏覽器 CORS 與 Mixed-Content 限制"""
    from fastapi.responses import StreamingResponse
    import urllib.request
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Webcom-Audio-Proxy"})
        resp = urllib.request.urlopen(req, timeout=5)
        def iter_audio():
            try:
                while True:
                    chunk = resp.read(4096)
                    if not chunk:
                        break
                    yield chunk
            except Exception:
                pass
            finally:
                try: resp.close()
                except Exception: pass
        content_type = resp.headers.get("Content-Type", "audio/mpeg")
        return StreamingResponse(iter_audio(), media_type=content_type)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Audio proxy failed: {e}")


def _is_tcp_port_open(port: int, host: str = "127.0.0.1") -> bool:
    import socket
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.settimeout(0.2)
    try:
        err = s.connect_ex((host, int(port)))
        return err == 0
    except Exception:
        return False
    finally:
        try:
            s.close()
        except Exception:
            pass


@app.get("/api/wsl/status")
def get_wsl_desktop_status():
    """檢查 WSL 運行狀態、Linux 發行版以及 VNC/websockify/音訊埠狀態"""
    has_wsl = False
    distro = "None"
    if shutil.which("wsl.exe"):
        try:
            out = subprocess.run(["wsl.exe", "-l", "-q"], capture_output=True, text=True, timeout=3)
            distros = [d.replace('\x00', '').strip() for d in out.stdout.splitlines() if d.replace('\x00', '').strip()]
            if distros:
                has_wsl = True
                distro = distros[0]
        except Exception:
            pass
            
    vnc_open = _is_tcp_port_open(5901)
    ws_open = _is_tcp_port_open(6080)
    audio_open = _is_tcp_port_open(8000)

    return {
        "status": "ok",
        "has_wsl": has_wsl,
        "distro": distro,
        "vnc_open": vnc_open,
        "vnc_port": 5901,
        "websockify_open": ws_open,
        "websockify_port": 6080,
        "audio_open": audio_open,
        "audio_port": 8000,
        "ready": (vnc_open and ws_open)
    }


@app.post("/api/wsl/start-desktop")
def start_wsl_desktop_service():
    """一鍵於 WSL 背景拉起 TigerVNC、XFCE 桌面、websockify 與音訊轉發"""
    if not shutil.which("wsl.exe"):
        raise HTTPException(status_code=400, detail="本地未偵測到 WSL 環境")
    
    import time
    try:
        # 0. 確保 /tmp/.X11-unix 在 WSL2 下可讀寫 (WSLg 預設可能掛載為唯讀)
        subprocess.run(
            ["wsl.exe", "-u", "root", "-e", "bash", "-c",
             "mount -o remount,rw /tmp/.X11-unix 2>/dev/null || true; chmod 1777 /tmp/.X11-unix 2>/dev/null || true; chmod 1777 /tmp/.ICE-unix 2>/dev/null || true"],
            capture_output=True, timeout=5
        )

        # 1. 確保 VNC 桌面服務在 :1 (5901) 運行 (使用 Xvfb + x11vnc -noxrandr -noxdamage，解除 WAYLAND_DISPLAY 防止黑畫面)
        if not _is_tcp_port_open(5901):
            # 清理可能殘留的舊服務與鎖
            cleanup_cmd = (
                "systemctl --user stop webcom-xvfb webcom-x11vnc 2>/dev/null || true; "
                "systemctl --user reset-failed 2>/dev/null || true; "
                "pkill -9 -x Xvfb 2>/dev/null || true; "
                "pkill -9 -x x11vnc 2>/dev/null || true; "
                "rm -f /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null || true"
            )
            subprocess.run(["wsl.exe", "-e", "bash", "-c", cleanup_cmd], capture_output=True, timeout=5)

            # 啟動 Xvfb :1 虛擬顯示器
            xvfb_cmd = "mkdir -p ~/.vnc && systemd-run --user --unit=webcom-xvfb Xvfb :1 -screen 0 1920x1080x24 -ac"
            subprocess.run(["wsl.exe", "-e", "bash", "-c", xvfb_cmd], capture_output=True, timeout=5)

            # 等待虛擬顯示器 socket 建立
            subprocess.run(
                ["wsl.exe", "-e", "bash", "-c", "for i in {1..20}; do [ -e /tmp/.X11-unix/X1 ] && break; sleep 0.05; done"],
                capture_output=True, timeout=5
            )

            # 啟動 x11vnc
            x11vnc_cmd = "systemd-run --user --unit=webcom-x11vnc env -u WAYLAND_DISPLAY x11vnc -display :1 -rfbport 5901 -nopw -listen 0.0.0.0 -forever -shared -noxrandr -noxdamage"
            subprocess.run(["wsl.exe", "-e", "bash", "-c", x11vnc_cmd], capture_output=True, timeout=5)

            # 啟動 XFCE4 桌面會話
            xfce_cmd = "systemd-run --user --unit=webcom-xfce env -u WAYLAND_DISPLAY GDK_BACKEND=x11 DISPLAY=:1 XDG_SESSION_TYPE=x11 XDG_CURRENT_DESKTOP=XFCE DESKTOP_SESSION=xfce QT_QPA_PLATFORM=xcb dbus-run-session -- xfce4-session"
            subprocess.run(["wsl.exe", "-e", "bash", "-c", xfce_cmd], capture_output=True, timeout=5)

        # 2. 確保 websockify 在 6080 運行 (提供 noVNC HTML5 WebSocket 與 Web 伺服器)
        if not _is_tcp_port_open(6080):
            subprocess.run(["wsl.exe", "-e", "bash", "-c", "systemctl --user stop webcom-websockify 2>/dev/null || true; systemctl --user reset-failed 2>/dev/null || true"], capture_output=True, timeout=5)
            ws_cmd = "systemd-run --user --unit=webcom-websockify websockify --web /usr/share/novnc 6080 localhost:5901"
            subprocess.run(["wsl.exe", "-e", "bash", "-c", ws_cmd], capture_output=True, timeout=5)

        # 3. 確保 PulseAudio 串流在 8000 運行
        if not _is_tcp_port_open(8000):
            audio_cmd = "pulseaudio --start --exit-idle-time=-1 >/dev/null 2>&1; pactl load-module module-simple-protocol-tcp rate=48000 format=s16le channels=2 source=@DEFAULT_SOURCE@ record=true port=8000 listen=0.0.0.0 >/dev/null 2>&1 || true"
            subprocess.run(["wsl.exe", "-e", "bash", "-c", audio_cmd], capture_output=True, timeout=5)

        # 輪詢等待連接埠就緒 (最多 3 秒)
        for _ in range(15):
            if _is_tcp_port_open(5901) and _is_tcp_port_open(6080):
                break
            time.sleep(0.2)

    except Exception as e:
        logging.warning(f"WSL 啟動桌面服務時產生警告/異常: {e}")

    return get_wsl_desktop_status()


@app.post("/api/wsl/stop-desktop")
def stop_wsl_desktop_service():
    """停止 WSL 背景的 VNC、Xvfb、XFCE 與 websockify 桌面服務"""
    if shutil.which("wsl.exe"):
        import time
        try:
            stop_cmd = (
                "systemctl --user stop webcom-xvfb webcom-x11vnc webcom-websockify webcom-xfce 2>/dev/null || true; "
                "systemctl --user reset-failed 2>/dev/null || true; "
                "pkill -9 -x Xvfb 2>/dev/null || true; "
                "pkill -9 -x x11vnc 2>/dev/null || true; "
                "pactl unload-module module-simple-protocol-tcp 2>/dev/null || true; "
                "rm -f /tmp/.X1-lock /tmp/.X11-unix/X1 2>/dev/null || true"
            )
            subprocess.run(["wsl.exe", "-e", "bash", "-c", stop_cmd], capture_output=True, timeout=5)
            subprocess.run(["wsl.exe", "-u", "root", "-e", "bash", "-c", stop_cmd], capture_output=True, timeout=5)
            time.sleep(0.3)
        except Exception as e:
            logging.warning(f"WSL 停止桌面服務時產生警告/異常: {e}")

    return get_wsl_desktop_status()


class LaunchAppRequest(BaseModel):
    cmd: str
    display: Optional[str] = ":1"


@app.post("/api/wsl/launch-app")
def launch_wsl_app(req: LaunchAppRequest):
    """在 WSL 虛擬 X11 顯示器 (預設 :1) 啟動指定的 Linux GUI 應用程式"""
    if not shutil.which("wsl.exe"):
        raise HTTPException(status_code=400, detail="本地未偵測到 WSL 環境")
    
    clean_cmd = req.cmd.strip()
    if not clean_cmd:
        raise HTTPException(status_code=400, detail="指令不能為空")

    # 確保桌面服務處於運行狀態，若未啟動則先自動啟動
    if not _is_tcp_port_open(5901) or not _is_tcp_port_open(6080):
        start_wsl_desktop_service()

    import time
    display = (req.display or ":1").strip() or ":1"
    run_cmd = f"setsid env -u WAYLAND_DISPLAY GDK_BACKEND=x11 DISPLAY={display} QT_QPA_PLATFORM=xcb {clean_cmd} </dev/null >/dev/null 2>&1 &"
    try:
        subprocess.run(["wsl.exe", "-e", "bash", "-c", run_cmd], capture_output=True, timeout=5)
    except Exception as e:
        logging.warning(f"WSL 啟動應用程式異常: {e}")
    return {"status": "ok", "cmd": clean_cmd, "display": display}


def _ensure_wsl_xinit_config():
    """確保 WSL 內部的 xinit、startx、xserverrc 與 xinitrc 已正確配置為支援 Webcom 虛擬顯示器"""
    if not shutil.which("wsl.exe"):
        return
    try:
        check_cmd = "[ -x /usr/local/bin/xinit ] && [ -f /etc/X11/xinit/xserverrc ] && grep -q 'Xvfb' /etc/X11/xinit/xserverrc 2>/dev/null"
        res = subprocess.run(["wsl.exe", "-e", "bash", "-c", check_cmd], capture_output=True, timeout=3)
        if res.returncode == 0:
            return
        
        # 透過 root 寫入配置
        init_script = (
            "mount -o remount,rw /tmp/.X11-unix 2>/dev/null || true; chmod 1777 /tmp/.X11-unix 2>/dev/null || true; "
            "cat << 'EOF' > /etc/X11/xinit/xserverrc\n"
            "#!/bin/bash\n"
            "mount -o remount,rw /tmp/.X11-unix 2>/dev/null || true; chmod 1777 /tmp/.X11-unix 2>/dev/null || true;\n"
            "DPY=':1'\n"
            "for arg in \"$@\"; do if [[ \"$arg\" =~ ^:[0-9]+$ ]]; then DPY=\"$arg\"; break; fi; done\n"
            "DPY_NUM=$(echo \"$DPY\" | sed 's/[^0-9]//g'); [ -z \"$DPY_NUM\" ] && DPY_NUM=1;\n"
            "VNC_PORT=$((5900 + DPY_NUM)); WS_PORT=6080;\n"
            "rm -f \"/tmp/.X${DPY_NUM}-lock\" \"/tmp/.X11-unix/X${DPY_NUM}\" 2>/dev/null || true;\n"
            "(\n"
            "  for i in $(seq 1 40); do [ -S \"/tmp/.X11-unix/X${DPY_NUM}\" ] || [ -e \"/tmp/.X11-unix/X${DPY_NUM}\" ] && break; sleep 0.05; done;\n"
            "  if ! pgrep -f \"x11vnc.*${DPY}\" >/dev/null 2>&1; then env -u WAYLAND_DISPLAY x11vnc -display \"$DPY\" -rfbport \"$VNC_PORT\" -nopw -listen 0.0.0.0 -forever -shared -bg -noxrandr -noxdamage >/dev/null 2>&1 || true; fi;\n"
            "  if ! pgrep -f \"websockify.*${WS_PORT}\" >/dev/null 2>&1; then websockify -D --web /usr/share/novnc \"$WS_PORT\" \"localhost:$VNC_PORT\" >/dev/null 2>&1 || true; fi;\n"
            ") &\n"
            "exec /usr/bin/Xvfb \"$DPY\" -screen 0 1920x1080x24 -ac \"$@\"\n"
            "EOF\n"
            "chmod 755 /etc/X11/xinit/xserverrc;\n"
            "cat << 'EOF' > /usr/local/bin/xinit\n"
            "#!/bin/bash\n"
            "has_server_args=0; for arg in \"$@\"; do if [ \"$arg\" = \"--\" ]; then has_server_args=1; break; fi; done;\n"
            "is_d1=0; if [ -e /tmp/.X11-unix/X1 ] || ss -tlpn 2>/dev/null | grep -q \":5901 \"; then is_d1=1; fi;\n"
            "if [ \"$is_d1\" -eq 1 ] && [ \"$#\" -gt 0 ] && [ \"$has_server_args\" -eq 0 ]; then\n"
            "  echo '================================================================';\n"
            "  echo 'ℹ️  [Webcom Xinit] X 伺服器已在運行中 (DISPLAY=:1, Port: 5901, WS: 6080)';\n"
            "  echo '🚀 正在將應用程式傳送至現有的 DISPLAY=:1 顯示器執行...';\n"
            "  echo '================================================================';\n"
            "  export DISPLAY=:1; unset WAYLAND_DISPLAY; export GDK_BACKEND=x11; export QT_QPA_PLATFORM=xcb; exec \"$@\";\n"
            "elif [ \"$is_d1\" -eq 1 ] && [ \"$#\" -eq 0 ]; then\n"
            "  echo '================================================================';\n"
            "  echo 'ℹ️  [Webcom Xinit] X 桌面環境已在運行中！';\n"
            "  echo '📺 虛擬顯示器: DISPLAY=:1 | RFB 埠: 5901 | WebSocket: 6080';\n"
            "  echo '👉 請在 Webcom 左側視窗點擊 [noVNC] 或 [Xorg] 分頁直接檢視與操作。';\n"
            "  echo '================================================================';\n"
            "  exit 0;\n"
            "fi;\n"
            "echo '================================================================';\n"
            "echo '🚀 [Webcom Xinit] 初始化虛擬 X11 顯示環境 (DISPLAY=:1)';\n"
            "echo '📺 虛擬顯示器: DISPLAY=:1 | 支援 Xvfb + x11vnc (5901) + WebSockify (6080)';\n"
            "echo '👉 執行中，請在 Webcom 左側切換至 [noVNC] 或 [Xorg] 分頁！';\n"
            "echo '================================================================';\n"
            "if [ \"$has_server_args\" -eq 0 ]; then exec /usr/bin/xinit \"$@\" -- :1; else exec /usr/bin/xinit \"$@\"; fi;\n"
            "EOF\n"
            "chmod 755 /usr/local/bin/xinit;\n"
            "echo '#!/bin/bash\nexec /usr/local/bin/xinit \"$@\"' > /usr/local/bin/startx && chmod 755 /usr/local/bin/startx;\n"
        )
        subprocess.run(["wsl.exe", "-u", "root", "-e", "bash", "-c", init_script], capture_output=True, timeout=5)
    except Exception as e:
        logging.warning(f"WSL xinit 配置初始化異常: {e}")


class XinitRequest(BaseModel):
    client: Optional[str] = "xfce4-session"
    display: Optional[str] = ":1"


@app.post("/api/wsl/xinit")
def api_wsl_xinit(req: Optional[XinitRequest] = None):
    """透過 xinit 啟動 WSL X 視窗會話 (支援自訂 client 如 xfce4-session, thunar 等)"""
    if not shutil.which("wsl.exe"):
        raise HTTPException(status_code=400, detail="本地未偵測到 WSL 環境")
    
    _ensure_wsl_xinit_config()
    client = (req.client if req and req.client else "xfce4-session").strip()
    display = (req.display if req and req.display else ":1").strip() or ":1"

    # 若服務已運行且請求為完整桌面，直接回傳就緒狀態
    if (_is_tcp_port_open(5901) and _is_tcp_port_open(6080)) and (client in ("xfce4-session", "startxfce4", "")):
        return get_wsl_desktop_status()

    # 確保 /tmp/.X11-unix 讀寫
    subprocess.run(
        ["wsl.exe", "-u", "root", "-e", "bash", "-c", "mount -o remount,rw /tmp/.X11-unix 2>/dev/null || true; chmod 1777 /tmp/.X11-unix 2>/dev/null || true"],
        capture_output=True, timeout=5
    )

    # 透過 xinit 啟動
    run_cmd = f"setsid /usr/local/bin/xinit {client} -- {display} </dev/null >/dev/null 2>&1 &"
    try:
        subprocess.run(["wsl.exe", "-e", "bash", "-c", run_cmd], capture_output=True, timeout=5)
    except Exception as e:
        logging.warning(f"WSL xinit 啟動異常: {e}")

    import time
    for _ in range(10):
        if _is_tcp_port_open(5901) and _is_tcp_port_open(6080):
            break
        time.sleep(0.2)

    return get_wsl_desktop_status()


import logging
import threading
import urllib.request
import json

downloading_models = set()

def _bg_download_model_worker(model_name: str):
    try:
        logging.info(f"Auto-caching model '{model_name}' to local disk...")
        target_dir = os.path.join(models_dir, model_name)
        os.makedirs(target_dir, exist_ok=True)
        
        if os.path.exists(os.path.join(target_dir, "ndarray-cache.json")):
            has_shards = any(f.startswith("params_shard") for f in os.listdir(target_dir))
            if has_shards:
                logging.info(f"Model '{model_name}' already complete on disk.")
                downloading_models.discard(model_name)
                return

        hf_base = f"https://huggingface.co/mlc-ai/{model_name}/resolve/main"
        
        cache_json_url = f"{hf_base}/ndarray-cache.json"
        cache_json_path = os.path.join(target_dir, "ndarray-cache.json")
        req = urllib.request.Request(cache_json_url, headers={'User-Agent': 'Webcom-AutoCache/1.0'})
        with urllib.request.urlopen(req, timeout=20) as resp, open(cache_json_path, 'wb') as f:
            f.write(resp.read())

        for fn in ["mlc-chat-config.json", "tokenizer.json", "tokenizer_config.json", "vocab.json", "merges.txt"]:
            try:
                url = f"{hf_base}/{fn}"
                dest = os.path.join(target_dir, fn)
                req = urllib.request.Request(url, headers={'User-Agent': 'Webcom-AutoCache/1.0'})
                with urllib.request.urlopen(req, timeout=20) as resp, open(dest, 'wb') as f:
                    f.write(resp.read())
            except Exception:
                pass

        with open(cache_json_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        records = cache_data.get("records", [])
        for r in records:
            sf = r.get("dataPath")
            if sf:
                shard_url = f"{hf_base}/{sf}"
                shard_dest = os.path.join(target_dir, sf)
                req = urllib.request.Request(shard_url, headers={'User-Agent': 'Webcom-AutoCache/1.0'})
                with urllib.request.urlopen(req, timeout=60) as resp, open(shard_dest, 'wb') as f:
                    f.write(resp.read())

        wasm_url = "https://raw.githubusercontent.com/mlc-ai/binary-mlc-llm-libs/main/web-llm-models/v0_2_48/Qwen2-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm"
        wasm_dest = os.path.join(target_dir, "Qwen2-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm")
        try:
            req = urllib.request.Request(wasm_url, headers={'User-Agent': 'Webcom-AutoCache/1.0'})
            with urllib.request.urlopen(req, timeout=30) as resp, open(wasm_dest, 'wb') as f:
                f.write(resp.read())
        except Exception:
            pass

        logging.info(f"✅ Model '{model_name}' successfully cached to local disk: {target_dir}!")
    except Exception as e:
        logging.error(f"Failed to auto-cache model '{model_name}': {e}")
    finally:
        downloading_models.discard(model_name)

class AutoCacheRequest(BaseModel):
    model_name: Optional[str] = "Qwen2.5-0.5B-Instruct-q4f16_1-MLC"

@app.post("/api/auto_cache_model")
def auto_cache_model(req: AutoCacheRequest):
    model_name = req.model_name or "Qwen2.5-0.5B-Instruct-q4f16_1-MLC"
    if model_name in downloading_models:
        return {"status": "in_progress", "model": model_name}
    
    target_dir = os.path.join(models_dir, model_name)
    if os.path.exists(os.path.join(target_dir, "ndarray-cache.json")) and any(f.startswith("params_shard") for f in os.listdir(target_dir)):
        return {"status": "already_cached", "model": model_name}

    downloading_models.add(model_name)
    t = threading.Thread(target=_bg_download_model_worker, args=(model_name,), daemon=True)
    t.start()
    return {"status": "started", "model": model_name}

log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daemon.log")
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logging.info("==================================================")
logging.info("Webcom Daemon server process initialized on port 8001")
logging.info("==================================================")

@app.get("/api/logs")
def get_daemon_logs(lines: int = 100):
    """Return latest lines from daemon.log for LLM diagnostics"""
    if not os.path.exists(log_file_path):
        return {"status": "success", "logs": "No logs recorded yet."}
    try:
        with open(log_file_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            tail = "".join(all_lines[-lines:])
            return {"status": "success", "total_lines": len(all_lines), "logs": tail}
    except Exception as e:
        return {"status": "error", "error": str(e)}

class ShellRequest(BaseModel):
    command: str
    protocol: Optional[str] = "shell"
    target: Optional[str] = None

class FileReadRequest(BaseModel):
    filepath: str

class FileWriteRequest(BaseModel):
    filepath: str
    content: str

class SSHRequest(BaseModel):
    host: str
    username: str
    password: Optional[str] = ""
    command: str
    port: Optional[int] = 22

class TelnetRequest(BaseModel):
    host: str
    port: Optional[int] = 23
    username: Optional[str] = ""
    password: Optional[str] = ""
    command: str
    cmd_prompt: Optional[str] = "#"

class SerialRequest(BaseModel):
    port: str
    baudrate: Optional[int] = 115200
    command: Optional[str] = ""

@app.get("/")
@app.get("/health")
def health_check():
    return {"status": "online", "service": "Webcom Daemon", "port": 8001}

@app.get("/api/daemon/log")
def get_daemon_log(lines: int = 1000):
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daemon.log")
    if not os.path.exists(log_path):
        return {"status": "ok", "exists": False, "total_lines": 0, "returned_lines": 0, "log": "daemon.log 檔案尚未產生"}
    try:
        with open(log_path, "r", encoding="utf-8", errors="replace") as f:
            all_lines = f.readlines()
            recent = all_lines[-lines:] if len(all_lines) > lines else all_lines
            return {
                "status": "ok",
                "exists": True,
                "total_lines": len(all_lines),
                "returned_lines": len(recent),
                "log": "".join(recent)
            }
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.delete("/api/daemon/log")
def clear_daemon_log():
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "daemon.log")
    try:
        with open(log_path, "w", encoding="utf-8") as f:
            f.write("")
        return {"status": "ok", "message": "Log cleared"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/shutdown")
def shutdown_daemon():
    import threading, time
    def delayed_exit():
        time.sleep(0.3)
        stop_marker = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".stop_daemon")
        try:
            with open(stop_marker, "w", encoding="utf-8") as f:
                f.write("stop")
        except Exception:
            pass
        try:
            import psutil
            parent = psutil.Process(os.getpid()).parent()
            if parent and "cmd" in parent.name().lower():
                parent.kill()
        except Exception:
            pass
        os._exit(0)
    threading.Thread(target=delayed_exit).start()
    return {"status": "success", "message": "Daemon shutting down"}

@app.post("/tools/execute_shell")
def execute_shell(req: ShellRequest):
    cmd = req.command.strip()
    if not cmd:
        return {"status": "success", "stdout": "", "stderr": ""}
    
    try:
        is_windows = sys.platform.startswith("win")
        process = None

        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"

        # 優先將本專案目錄下之 ./python 與直譯器路徑置於 PATH 最前，確保指令一律優先使用專案 Python
        base_dir = os.path.dirname(os.path.abspath(__file__))
        extra_paths = []
        proj_py_dir = os.path.join(base_dir, "python")
        if os.path.isdir(proj_py_dir):
            extra_paths.append(proj_py_dir)
            extra_scripts = os.path.join(proj_py_dir, "Scripts")
            if os.path.isdir(extra_scripts):
                extra_paths.append(extra_scripts)
        if sys.executable and os.path.isfile(sys.executable):
            exe_dir = os.path.dirname(sys.executable)
            if exe_dir not in extra_paths and os.path.isdir(exe_dir):
                extra_paths.append(exe_dir)
        # 自動掃描並注入 Windows 常見應用程式目錄 (如 Notepad++, VS Code, Git 及 App Paths 登錄檔)
        if is_windows:
            candidate_dirs = [
                r"C:\Program Files\Notepad++",
                r"C:\Program Files (x86)\Notepad++",
                r"C:\Program Files\Git\bin",
                r"C:\Program Files\Git\cmd",
                os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\bin"),
            ]
            for c_dir in candidate_dirs:
                if os.path.isdir(c_dir) and c_dir not in extra_paths:
                    extra_paths.append(c_dir)
            
            try:
                import winreg
                for root_key in (winreg.HKEY_LOCAL_MACHINE, winreg.HKEY_CURRENT_USER):
                    try:
                        with winreg.OpenKey(root_key, r"SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths") as k:
                            for i in range(winreg.QueryInfoKey(k)[0]):
                                try:
                                    sub_name = winreg.EnumKey(k, i)
                                    with winreg.OpenKey(k, sub_name) as sk:
                                        val, _ = winreg.QueryValueEx(sk, "")
                                        if val and os.path.exists(val):
                                            app_dir = os.path.dirname(val)
                                            if app_dir and os.path.isdir(app_dir) and app_dir not in extra_paths:
                                                extra_paths.append(app_dir)
                                except Exception:
                                    pass
                    except Exception:
                        pass
            except Exception:
                pass

        if extra_paths:
            env["PATH"] = os.pathsep.join(extra_paths) + os.pathsep + env.get("PATH", "")

        def decode_stream(raw_bytes: bytes) -> str:
            if not raw_bytes:
                return ""
            for enc in ("utf-8", "cp950", "cp936", "gbk", "latin-1"):
                try:
                    return raw_bytes.decode(enc)
                except UnicodeDecodeError:
                    continue
            return raw_bytes.decode("utf-8", errors="replace")

        if is_windows and (req.protocol == "wsl" or req.target == "wsl" or cmd.startswith("wsl ") or cmd.startswith("xinit") or cmd.startswith("startx")):
            if shutil.which("wsl.exe"):
                actual_cmd = cmd[4:].strip() if cmd.startswith("wsl ") else cmd
                try:
                    process = subprocess.run(
                        ["wsl.exe", "-e", "bash", "-c", actual_cmd],
                        capture_output=True,
                        text=False,
                        timeout=30,
                        env=env
                    )
                except Exception:
                    process = None

        if process is None:
            if is_windows:
                # Fast-path for Windows: Common commands run directly via cmd.exe in ~30ms instead of waiting for PowerShell cold-start
                needs_ps = req.protocol == "powershell" or any(cmd.strip().startswith(p) for p in ["$", "Get-", "Set-", "New-", "Remove-", "Start-", "Stop-", "Restart-"]) or "| %" in cmd or "| ?" in cmd or "Select-Object" in cmd
                if not needs_ps:
                    # 偵測是否為獨立 GUI 視窗應用 (如 notepad++, notepad, calc, mspaint, code 等)
                    # 自動透過 Popen 進行非阻塞式背景啟動，防止前景進程阻塞 10-30 秒導致終端機或 AI 調用超時中斷
                    first_token = cmd.split()[0].lower() if cmd.split() else ""
                    if first_token.endswith(".exe"):
                        first_token = first_token[:-4]
                    is_gui_app = first_token in ("notepad", "notepad++", "calc", "mspaint", "code", "explorer", "vlc", "write")
                    if is_gui_app:
                        exe = shutil.which(first_token, path=env.get("PATH", "")) or shutil.which(first_token + ".exe", path=env.get("PATH", ""))
                        if exe:
                            args_part = cmd[len(first_token):].strip()
                            if args_part.lower().startswith(".exe"):
                                args_part = args_part[4:].strip()
                            run_target = f'"{exe}" {args_part}'.strip() if args_part else f'"{exe}"'
                            subprocess.Popen(run_target, shell=True, env=env, close_fds=True)
                            return {
                                "status": "success",
                                "returncode": 0,
                                "stdout": f"[✔ 桌面視窗應用已成功啟動]: {run_target}\n",
                                "stderr": ""
                            }

                    try:
                        process = subprocess.run(
                            f'cmd.exe /c "chcp 65001 >nul 2>&1 && {cmd}"',
                            shell=True,
                            capture_output=True,
                            text=False,
                            timeout=30,
                            env=env
                        )
                    except Exception:
                        process = None

                # Fallback to PowerShell if cmd failed or command specifically needs PowerShell
                if process is None or (needs_ps and shutil.which("powershell.exe")):
                    if shutil.which("powershell.exe"):
                        try:
                            ps_cmd = f"chcp 65001 >$null; $OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::OutputEncoding = [System.Text.Encoding]::UTF8; [Console]::InputEncoding = [System.Text.Encoding]::UTF8; {cmd}"
                            process = subprocess.run(
                                ["powershell.exe", "-NonInteractive", "-NoLogo", "-NoProfile", "-Command", ps_cmd],
                                capture_output=True,
                                text=False,
                                timeout=30,
                                env=env
                            )
                        except Exception:
                            process = None
            else:
                process = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=False,
                    timeout=30,
                    env=env
                )
        
        stdout_str = decode_stream(process.stdout)
        stderr_str = decode_stream(process.stderr)

        return {
            "status": "success" if process.returncode == 0 else "error",
            "returncode": process.returncode,
            "stdout": stdout_str,
            "stderr": stderr_str
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "指令執行超時 (Timeout 30s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

def resolve_python_interpreter(preference: str = "auto") -> tuple:
    """
    依照使用者指定與優先順序解析 Python 直譯器：
    1. 本專案目錄下的 ./python/python.exe (或 ./python/bin/python3) -> "project"
    2. 當前 daemon 執行的 Python 直譯器 (sys.executable) -> "project" 或 "daemon_venv"
    3. 系統 PATH 中的 python / python3 -> "system"
    4. 常見 Windows 安裝路徑 -> "system"
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # 1. 本專案自帶的嵌入式/可攜式 Python (最高優先)
    proj_candidates = [
        os.path.join(base_dir, "python", "python.exe"),
        os.path.join(base_dir, "python", "bin", "python3"),
        os.path.join(base_dir, "python", "bin", "python")
    ]
    for p in proj_candidates:
        if os.path.isfile(p):
            return p, "project"

    # 若 sys.executable 本身就在專案目錄內
    if sys.executable and os.path.isfile(sys.executable):
        try:
            rel = os.path.relpath(sys.executable, base_dir)
            if not rel.startswith(".."):
                return sys.executable, "project"
        except Exception:
            pass

    # 2. 如果偏好專案或自動，且 sys.executable 有效
    if preference != "system" and sys.executable and os.path.isfile(sys.executable):
        return sys.executable, "project"

    # 3. 系統環境中的 Python (preference == "system" 或無專案 Python)
    sys_candidates = []
    w_py = shutil.which("python")
    w_py3 = shutil.which("python3")
    if w_py: sys_candidates.append(w_py)
    if w_py3: sys_candidates.append(w_py3)

    common_win_dirs = [
        os.path.expandvars(r"%LocalAppData%\Programs\Python\Python313\python.exe"),
        os.path.expandvars(r"%LocalAppData%\Programs\Python\Python312\python.exe"),
        os.path.expandvars(r"%LocalAppData%\Programs\Python\Python311\python.exe"),
        os.path.expandvars(r"%LocalAppData%\Programs\Python\Python310\python.exe"),
        os.path.expandvars(r"%ProgramFiles%\Python313\python.exe"),
        os.path.expandvars(r"%ProgramFiles%\Python312\python.exe"),
        os.path.expandvars(r"%ProgramFiles%\Python311\python.exe"),
        os.path.expandvars(r"%ProgramFiles%\Python310\python.exe"),
        os.path.expandvars(r"%UserProfile%\miniconda3\python.exe"),
        os.path.expandvars(r"%UserProfile%\anaconda3\python.exe"),
    ]
    sys_candidates.extend(common_win_dirs)

    for p in sys_candidates:
        if os.path.isfile(p):
            # 排除 Windows Store 0-byte stub
            if "windowsapps" not in p.lower():
                return p, "system"

    # 4. 最後回退至 sys.executable 或 "python"
    return sys.executable or "python", "fallback"

@app.get("/tools/python_info")
def python_info_endpoint():
    py_exec, engine_type = resolve_python_interpreter("auto")
    base_dir = os.path.dirname(os.path.abspath(__file__))
    proj_py = os.path.join(base_dir, "python", "python.exe")
    return {
        "status": "success",
        "resolved_executable": py_exec,
        "engine_type": engine_type,
        "project_python_exists": os.path.isfile(proj_py),
        "project_python_path": proj_py,
        "daemon_executable": sys.executable,
        "version": sys.version
    }

@app.get("/tools/system_info")
@app.get("/tools/system_specs")
def system_info_endpoint():
    """查詢本機硬體與系統規格 (CPU、記憶體、GPU、磁碟、OS 及已安裝文字編輯器 Notepad++ 等)"""
    try:
        import platform, psutil
        is_win = sys.platform.startswith("win")

        # CPU
        cpu_info = {
            "processor": platform.processor(),
            "cores_physical": psutil.cpu_count(logical=False),
            "cores_logical": psutil.cpu_count(logical=True),
        }

        # RAM
        mem = psutil.virtual_memory()
        mem_info = {
            "total_gb": round(mem.total / (1024**3), 2),
            "available_gb": round(mem.available / (1024**3), 2),
            "percent_used": mem.percent
        }

        # GPU
        gpus = []
        if is_win:
            try:
                p = subprocess.run(["cmd.exe", "/c", "wmic path win32_VideoController get name"], capture_output=True, text=True, timeout=3)
                gpus = [line.strip() for line in p.stdout.splitlines() if line.strip() and line.strip() != "Name"]
            except Exception:
                pass

        # Disks
        disks = []
        for part in psutil.disk_partitions(all=False):
            if is_win and ("cdrom" in part.opts or part.fstype == ""):
                continue
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append({
                    "device": part.device,
                    "mountpoint": part.mountpoint,
                    "total_gb": round(usage.total / (1024**3), 2),
                    "free_gb": round(usage.free / (1024**3), 2),
                    "percent_used": usage.percent
                })
            except Exception:
                pass

        # Tools & Editors
        npp_candidate = r"C:\Program Files\Notepad++\notepad++.exe"
        npp_candidate_x86 = r"C:\Program Files (x86)\Notepad++\notepad++.exe"
        npp_path = npp_candidate if os.path.isfile(npp_candidate) else (npp_candidate_x86 if os.path.isfile(npp_candidate_x86) else None)

        tools = {
            "notepad": shutil.which("notepad") or "C:\\Windows\\System32\\notepad.exe",
            "notepad++": npp_path is not None,
            "notepad++_path": npp_path,
            "wsl": shutil.which("wsl.exe") is not None,
            "git": shutil.which("git") is not None,
            "python": sys.executable
        }

        return {
            "status": "success",
            "os": f"{platform.system()} {platform.release()} (Build {platform.version()}) {platform.machine()}",
            "hostname": platform.node(),
            "cpu": cpu_info,
            "memory": mem_info,
            "gpu": gpus,
            "disks": disks,
            "tools": tools
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}

class ScriptRunRequest(BaseModel):
    code: str
    language: Optional[str] = "py"
    engine_preference: Optional[str] = "auto"

@app.post("/tools/run_script")
def run_script_endpoint(req: ScriptRunRequest):
    code = req.code or ""
    lang = (req.language or "py").lower()

    if not code.strip():
        return {"status": "error", "error": "腳本內容為空"}

    ext_map = {"py": ".py", "python": ".py", "sh": ".sh", "bash": ".sh", "bat": ".bat", "cmd": ".bat", "ps1": ".ps1", "powershell": ".ps1"}
    ext = ext_map.get(lang, ".py")

    import tempfile
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", suffix=ext, delete=False, encoding="utf-8") as f:
            f.write(code)
            temp_path = f.name

        base_dir = os.path.dirname(os.path.abspath(__file__))
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"
        env["PYTHONUTF8"] = "1"
        env["LANG"] = "C.UTF-8"
        env["LC_ALL"] = "C.UTF-8"
        extra_paths = []
        proj_py_dir = os.path.join(base_dir, "python")
        if os.path.isdir(proj_py_dir):
            extra_paths.append(proj_py_dir)
            extra_scripts = os.path.join(proj_py_dir, "Scripts")
            if os.path.isdir(extra_scripts):
                extra_paths.append(extra_scripts)
        if sys.executable and os.path.isfile(sys.executable):
            exe_dir = os.path.dirname(sys.executable)
            if exe_dir not in extra_paths and os.path.isdir(exe_dir):
                extra_paths.append(exe_dir)
        if extra_paths:
            env["PATH"] = os.pathsep.join(extra_paths) + os.pathsep + env.get("PATH", "")

        engine_type = "project"
        py_exec = sys.executable
        if ext == ".py":
            py_exec, engine_type = resolve_python_interpreter(req.engine_preference or "auto")
            cmd = [py_exec, "-X", "utf8", "-u", temp_path]
        elif ext == ".sh":
            cmd = ["bash", temp_path] if shutil.which("bash") else ["wsl", "bash", temp_path]
        elif ext == ".bat":
            cmd = ["cmd.exe", "/c", temp_path]
        elif ext == ".ps1":
            cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", temp_path]
        else:
            py_exec, engine_type = resolve_python_interpreter(req.engine_preference or "auto")
            cmd = [py_exec, "-X", "utf8", "-u", temp_path]

        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30, encoding="utf-8", errors="replace", env=env)
        return {
            "status": "success" if proc.returncode == 0 else "error",
            "returncode": proc.returncode,
            "stdout": proc.stdout,
            "stderr": proc.stderr,
            "engine": engine_type,
            "executable": py_exec
        }
    except subprocess.TimeoutExpired:
        return {"status": "error", "error": "腳本執行超時 (Timeout 30s)"}
    except Exception as e:
        return {"status": "error", "error": str(e)}
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except Exception:
                pass

class SearchRequest(BaseModel):
    query: str

@app.post("/tools/web_search")
def web_search_endpoint(req: SearchRequest):
    query = req.query.strip()
    if not query:
        return {"status": "error", "error": "搜尋關鍵字不得為空"}
    
    # 優先處理直接網址抓取與結構化 Markdown 轉換 (Direct URL Fetch & MarkItDown Conversion)
    import re, ssl, tempfile
    url_match = re.search(r'https?://[^\s<>"]+', query)
    if url_match:
        target_url = url_match.group(0)
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': 'zh-TW,zh;q=0.9,en-US;q=0.8,en;q=0.7'
            }
            req_url = urllib.request.Request(target_url, headers=headers)
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            with urllib.request.urlopen(req_url, timeout=12, context=ctx) as resp:
                raw_bytes = resp.read()
                content_type = resp.headers.get('Content-Type', '')
                charset = 'utf-8'
                if 'charset=' in content_type.lower():
                    try:
                        charset = content_type.lower().split('charset=')[-1].split(';')[0].strip()
                    except Exception:
                        charset = 'utf-8'
                html_text = raw_bytes.decode(charset, errors='replace')

            md_text = ""
            # 優先使用 Microsoft MarkItDown 進行精準網頁結構化轉換
            try:
                from markitdown import MarkItDown
                md = MarkItDown()
                with tempfile.NamedTemporaryFile('w', suffix='.html', delete=False, encoding='utf-8') as f:
                    f.write(html_text)
                    tmp_path = f.name
                try:
                    res = md.convert(tmp_path)
                    md_text = res.text_content.strip()
                finally:
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
            except Exception as md_err:
                logging.warning(f"MarkItDown conversion error: {md_err}")

            # 若未安裝或轉換失敗，回退至 BeautifulSoup
            if not md_text:
                try:
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html_text, 'html.parser')
                    for tag in soup(['script', 'style', 'nav', 'footer', 'header', 'svg', 'noscript']):
                        tag.extract()
                    md_text = soup.get_text(separator='\n', strip=True)
                except Exception:
                    md_text = re.sub(r'<[^>]+>', ' ', html_text)
                    md_text = re.sub(r'\s+', ' ', md_text).strip()

            md_text = re.sub(r'\n{3,}', '\n\n', md_text).strip()
            if len(md_text) > 8000:
                md_text = md_text[:8000] + f"\n\n...[目標網頁全文共 {len(md_text)} 字元，已截取前 8000 字元核心內容]..."

            if md_text:
                info = (
                    f"【目標網頁即時抓取內容 ({target_url})】\n"
                    f"{md_text}\n\n"
                    f"【網頁內容分析與導讀指示】：以上為目標網頁之即時讀取內容。請依據上述內容詳細分析、導讀、歸納或回答使用者的問題。"
                )
                return {"status": "success", "query": query, "url": target_url, "is_direct_url": True, "result": info}
        except Exception as e:
            logging.warning(f"Direct URL fetch failed for {target_url}: {e}")

    # 優先處理天氣與 IP / GEO 地理位置查詢
    is_weather = any(k in query.lower() for k in ["天氣", "weather", "溫度", "氣溫", "降雨", "氣象"])
    is_geo_ip = any(k in query.lower() for k in ["ip", "geo", "地理位置", "經緯度", "所在城市", "定位", "電信業者", "isp"])

    if is_weather:
        geo_info_line = ""
        city_for_weather = "Hsinchu"
        lat, lon = 24.8065, 120.9706
        ip_addr = ""
        try:
            req_geo = urllib.request.Request("http://ip-api.com/json/?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query", headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req_geo, timeout=5) as resp:
                geo_data = json.loads(resp.read().decode('utf-8', errors='replace'))
                if geo_data.get("status") == "success":
                    city_for_weather = geo_data.get('city', 'Hsinchu')
                    lat = geo_data.get('lat', 24.8065)
                    lon = geo_data.get('lon', 120.9706)
                    ip_addr = geo_data.get('query', '')
                    geo_info_line = (
                        f"【本機外網 IP 與所在地資訊】\n"
                        f"- 外網 IP: {ip_addr}\n"
                        f"- 所在城市/區域: {geo_data.get('city')}, {geo_data.get('regionName')} ({geo_data.get('country')})\n"
                        f"- 經緯度座標: Lat {lat}, Lon {lon}\n"
                        f"- 網際網路供應商 (ISP): {geo_data.get('isp')}\n\n"
                    )
        except Exception:
            pass

        cities_map = ['台北', '新北', '基隆', '桃園', '新竹', '苗栗', '台中', '彰化', '南投', '雲林', '嘉義', '台南', '高雄', '屏東', '宜蘭', '花蓮', '台東', '澎湖', '金門', '連江', 'Taipei', 'Hsinchu', 'Taichung', 'Tainan', 'Kaohsiung', 'Tokyo', 'London', 'Paris', 'New York']
        target_city = None
        for c in cities_map:
            if c in query:
                target_city = c
                break
        if not target_city:
            target_city = city_for_weather or "Taipei"

        weather_text = ""
        try:
            om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,wind_speed_10m&timezone=auto"
            req_om = urllib.request.Request(om_url, headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req_om, timeout=6) as resp:
                om_data = json.loads(resp.read().decode('utf-8', errors='replace'))
                cur = om_data.get('current', {})
                temp_c = cur.get('temperature_2m', 'N/A')
                feels_c = cur.get('apparent_temperature', 'N/A')
                humidity = cur.get('relative_humidity_2m', 'N/A')
                precip = cur.get('precipitation', 0.0)
                wind = cur.get('wind_speed_10m', 'N/A')

                dressing = ""
                try:
                    t_val = float(temp_c)
                    p_val = float(precip)
                    if t_val < 15: dressing = "天氣偏冷，建議穿著保暖大衣、厚毛衣或防風外套。"
                    elif t_val < 22: dressing = "氣候微涼舒適，建議穿著長袖上衣搭配薄外套。"
                    elif t_val < 28: dressing = "氣候溫暖宜人，穿著休閒長短袖或舒適襯衫即可。"
                    else: dressing = "天氣炎熱，請穿著吸汗透氣短袖，注意防曬並多補充水分。"
                    if p_val > 0.3: dressing += " 當前有降雨，出門請務必攜帶雨具！"
                except Exception:
                    dressing = "建議根據體感溫度穿著適當衣物。"

                weather_text = (
                    f"【即時天氣與氣象資訊 ({target_city})】\n"
                    f"- 當前氣溫: {temp_c}°C\n"
                    f"- 體感溫度: {feels_c}°C\n"
                    f"- 相對濕度: {humidity}%\n"
                    f"- 降雨量: {precip} mm\n"
                    f"- 風速: {wind} km/h\n"
                    f"- 出門穿著建議: {dressing}"
                )
        except Exception:
            pass

        if not weather_text:
            try:
                req_w_json = urllib.request.Request(f"https://wttr.in/{urllib.parse.quote(target_city)}?format=j1", headers={'User-Agent': 'curl/7.68.0'})
                with urllib.request.urlopen(req_w_json, timeout=6) as resp:
                    wjson = json.loads(resp.read().decode('utf-8', errors='replace'))
                    cur = wjson['current_condition'][0]
                    weather_text = (
                        f"【即時天氣與氣象資訊 ({target_city})】\n"
                        f"- 當前氣溫: {cur.get('temp_C')}°C\n"
                        f"- 體感溫度: {cur.get('FeelsLikeC')}°C\n"
                        f"- 相對濕度: {cur.get('humidity')}%\n"
                        f"- 降雨量: {cur.get('precipMM')} mm\n"
                        f"- 風速: {cur.get('windspeedKmph')} km/h"
                    )
            except Exception:
                pass

        if weather_text:
            return {"status": "success", "query": query, "result": f"{geo_info_line}{weather_text}"}

    # 優先處理純 IP / GEO 地理位置查詢 (若未問天氣)
    if is_geo_ip:
        try:
            req_geo = urllib.request.Request("http://ip-api.com/json/?fields=status,message,country,countryCode,region,regionName,city,zip,lat,lon,timezone,isp,org,as,query", headers={'User-Agent': 'curl/7.68.0'})
            with urllib.request.urlopen(req_geo, timeout=6) as resp:
                geo_data = json.loads(resp.read().decode('utf-8', errors='replace'))
                if geo_data.get("status") == "success":
                    info = (
                        f"【本機外網 IP 與 GEO 地理位置資訊】\n"
                        f"- 外網 IP: {geo_data.get('query')}\n"
                        f"- 國家/地區: {geo_data.get('country')} ({geo_data.get('countryCode')})\n"
                        f"- 所在城市/區域: {geo_data.get('city')}, {geo_data.get('regionName')}\n"
                        f"- 經緯度座標: Lat {geo_data.get('lat')}, Lon {geo_data.get('lon')}\n"
                        f"- 系統時區: {geo_data.get('timezone')}\n"
                        f"- 網際網路供應商 (ISP): {geo_data.get('isp')} ({geo_data.get('org')})"
                    )
                    return {"status": "success", "query": query, "result": info}
        except Exception as e:
            logging.warning(f"IP Geo lookup failed: {e}")

    # 優先處理停班停課 (颱風假) 查詢
    if any(k in query.lower() for k in ["停班停課", "颱風假", "上班上課", "人事行政總處", "天災假", "停班", "停課"]):
        try:
            # 優先搜尋行政院人事行政總處與氣象最新通報
            dgpa_search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote('行政院人事行政總處 各縣市 停班停課 最新公告')}"
            headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
            req_dgpa = urllib.request.Request(dgpa_search_url, headers=headers)
            with urllib.request.urlopen(req_dgpa, timeout=8) as resp:
                html = resp.read().decode('utf-8', errors='replace')
                import re
                snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
                clean_snippets = [re.sub(r'<[^>]+>', '', s).strip() for s in snippets[:3] if re.sub(r'<[^>]+>', '', s).strip()]
                if clean_snippets:
                    return {"status": "success", "query": query, "result": f"【行政院人事行政總處與天然災害停班停課最新通報】\n" + "\n---\n".join(clean_snippets)}
        except Exception as e:
            logging.warning(f"DGPA search error: {e}")

    # DuckDuckGo HTML 網頁搜尋 (後端執行無 CORS 限制)
    try:
        search_url = f"https://html.duckduckgo.com/html/?q={urllib.parse.quote(query)}"
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'}
        req_obj = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req_obj, timeout=8) as resp:
            html = resp.read().decode('utf-8', errors='replace')
            import re
            snippets = re.findall(r'<a class="result__snippet[^>]*>(.*?)</a>', html, re.DOTALL)
            clean_snippets = []
            for snip in snippets[:4]:
                clean_text = re.sub(r'<[^>]+>', '', snip).strip()
                if clean_text:
                    clean_snippets.append(clean_text)
            if clean_snippets:
                return {"status": "success", "query": query, "result": "\n---\n".join(clean_snippets)}
    except Exception as e:
        logging.warning(f"DuckDuckGo search error: {e}")

    # 維基百科 API 備援
    try:
        wiki_url = f"https://zh.wikipedia.org/w/api.php?action=query&list=search&srsearch={urllib.parse.quote(query)}&format=json"
        req_wiki = urllib.request.Request(wiki_url, headers={'User-Agent': 'Webcom/1.0'})
        with urllib.request.urlopen(req_wiki, timeout=6) as resp:
            wiki_json = json.loads(resp.read().decode('utf-8', errors='replace'))
            items = wiki_json.get("query", {}).get("search", [])
            if items:
                import re
                results = [f"【{it.get('title')}】 {re.sub(r'<[^>]+>', '', it.get('snippet', ''))}" for it in items[:3]]
                return {"status": "success", "query": query, "result": "\n---\n".join(results)}
    except Exception as e:
        logging.warning(f"Wikipedia search error: {e}")

    return {"status": "error", "error": f"搜尋失敗或網路無法連線"}

# ─────────────────────────────────────────────────────────────
# 📄 Document Parser Endpoint (PDF / Word / Excel / PPT → Text)
# ─────────────────────────────────────────────────────────────
import base64
import tempfile

class DocumentParseRequest(BaseModel):
    filename: str       # 原始檔名 (判斷副檔名用)
    data_base64: str    # 前端 FileReader.readAsDataURL → base64 部分

@app.post("/tools/parse_document")
def parse_document(req: DocumentParseRequest):
    """
    接收 Base64 編碼的文件，優先使用 Microsoft MarkItDown 轉換為結構化 Markdown。
    支援: .pdf, .docx, .doc, .xlsx, .xls, .pptx, .ppt, .epub, .html, .htm, .csv, .tsv, .txt, .md 等。
    """
    ext = os.path.splitext(req.filename.lower())[1]
    try:
        # 解碼 base64 (支援 data:...;base64,<data> 或純 base64)
        raw_b64 = req.data_base64
        if "base64," in raw_b64:
            raw_b64 = raw_b64.split("base64,", 1)[1]
        file_bytes = base64.b64decode(raw_b64)
    except Exception as e:
        return {"status": "error", "error": f"Base64 解碼失敗: {e}"}

    text = ""
    extracted_images = []
    tables_count = 0
    engine_used = "fallback"

    try:
        # ── 1. 優先使用 Microsoft MarkItDown 進行全格式原生 Markdown 轉檔 ────────
        # 支援 PDF, Word (.docx/.doc), Excel (.xlsx/.xls), PPT (.pptx/.ppt), EPUB, HTML, CSV 等
        try:
            from markitdown import MarkItDown
            temp_path = None
            try:
                with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
                    f.write(file_bytes)
                    temp_path = f.name
                md_engine = MarkItDown()
                result = md_engine.convert(temp_path)
                md_text = (result.text_content or "").strip()
                if md_text:
                    text = md_text
                    engine_used = "markitdown"
            finally:
                if temp_path and os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except Exception: pass
        except Exception as md_err:
            logging.warning(f"MarkItDown conversion attempt warning: {md_err}")

        # ── 2. 若為 PDF，仍額外提取內嵌圖片與表格供 Vision 多模態 LLM 使用 ────────
        if ext == ".pdf":
            try:
                import pymupdf
                doc = pymupdf.open(stream=file_bytes, filetype="pdf")
                for page_idx in range(len(doc)):
                    page = doc[page_idx]
                    try:
                        tabs = page.find_tables()
                        tables_count += len(tabs.tables)
                    except Exception: pass

                    try:
                        for img_info in page.get_images():
                            if len(extracted_images) >= 15:
                                break
                            xref = img_info[0]
                            base_img = doc.extract_image(xref)
                            w, h = base_img.get("width", 0), base_img.get("height", 0)
                            img_data = base_img.get("image", b"")
                            img_ext = base_img.get("ext", "png")
                            if w >= 25 and h >= 25 and len(img_data) > 80:
                                b64 = f"data:image/{img_ext};base64," + base64.b64encode(img_data).decode("ascii")
                                extracted_images.append(b64)
                    except Exception: pass

                # 若 MarkItDown 未成功輸出文字，使用 PyMuPDF4LLM 作為 PDF 備援
                if not text:
                    try:
                        import pymupdf4llm
                        text = pymupdf4llm.to_markdown(doc, embed_images=True)
                    except Exception:
                        page_parts = [p.get_text("text").strip() for p in doc if p.get_text("text").strip()]
                        text = "\n\n---\n\n".join(page_parts)
            except Exception as pdf_err:
                logging.warning(f"PyMuPDF parse warning: {pdf_err}")
                if not text:
                    try:
                        import io, pypdf
                        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
                        text = "\n\n".join(p.extract_text() or "" for p in reader.pages)
                    except Exception: pass

        # ── 3. 其他格式之備援解析器 (當 MarkItDown 未啟用或失敗時) ─────────────
        elif not text:
            # Word (.docx)
            if ext in (".docx",):
                try:
                    import docx, io
                    doc = docx.Document(io.BytesIO(file_bytes))
                    parts = [p.text for p in doc.paragraphs if p.text.strip()]
                    text = "\n\n".join(parts)
                except Exception: pass

            # Excel (.xlsx, .xls)
            elif ext in (".xlsx", ".xls"):
                try:
                    import openpyxl, io
                    wb = openpyxl.load_workbook(io.BytesIO(file_bytes), read_only=True, data_only=True)
                    parts = []
                    for sheet_name in wb.sheetnames:
                        ws = wb[sheet_name]
                        parts.append(f"### 工作表: {sheet_name}")
                        for row in ws.iter_rows(values_only=True):
                            cells = [str(c).replace("\n", " ").strip() if c is not None else "" for c in row]
                            if any(cells):
                                parts.append("| " + " | ".join(cells) + " |")
                    text = "\n\n".join(parts)
                except Exception: pass

            # PowerPoint (.pptx, .ppt)
            elif ext in (".pptx", ".ppt"):
                try:
                    from pptx import Presentation
                    import io
                    prs = Presentation(io.BytesIO(file_bytes))
                    parts = []
                    for i, slide in enumerate(prs.slides, 1):
                        parts.append(f"### 投影片 {i}")
                        for shape in slide.shapes:
                            if hasattr(shape, "text") and shape.text.strip():
                                parts.append(shape.text)
                    text = "\n\n".join(parts)
                except Exception: pass

            # 純文字 / 程式碼 / HTML / CSV 通用 UTF-8 解碼
            else:
                try:
                    text = file_bytes.decode("utf-8")
                except Exception:
                    text = file_bytes.decode("latin1", errors="replace")

        text = (text or "").strip()
        if not text and not extracted_images:
            return {"status": "error", "error": f"文件 ({req.filename}) 解析成功，但未能提取到文字或圖片內容"}

        char_count = len(text)
        save_info = save_converted_markdown(req.filename, text)
        return {
            "status": "success",
            "filename": req.filename,
            "ext": ext,
            "engine": engine_used,
            "format": "markdown",
            "char_count": char_count,
            "tables_count": tables_count,
            "images_count": len(extracted_images),
            "images": extracted_images,
            "text": text,
            "markdown": text,
            **save_info
        }

    except Exception as e:
        logging.exception(f"Document parse error ({req.filename}): {e}")
        return {"status": "error", "error": f"文件解析異常: {str(e)}"}


@app.post("/api/convert")
def api_convert_document(req: DocumentParseRequest):
    """
    相容 MarkItDown Website 的原生極速轉檔介面。
    呼叫 Microsoft MarkItDown 原生核心進行轉檔，回傳標準 Markdown。
    """
    res = parse_document(req)
    if res.get("status") == "success":
        md = res.get("markdown") or res.get("text") or ""
        title = os.path.splitext(req.filename)[0]
        return {
            "status": "success",
            "filename": req.filename,
            "title": title,
            "markdown": md,
            "charCount": len(md),
            "lineCount": len(md.splitlines())
        }
    else:
        err = res.get("error") or "文件轉換失敗"
        raise HTTPException(status_code=500, detail=err)


class RevealPathRequest(BaseModel):
    path: str

@app.post("/api/reveal_file")
def reveal_file_in_os(req: RevealPathRequest):
    """在 Windows 檔案總管或系統檔案瀏覽器中選取並顯示該檔案"""
    p = os.path.abspath(req.path)
    if not os.path.exists(p):
        cand1 = os.path.join(webcom_dir, "rag_docs", os.path.basename(req.path))
        cand2 = os.path.join(webcom_dir, "assets", "RAG", "Converted", os.path.basename(req.path))
        if os.path.exists(cand1):
            p = cand1
        elif os.path.exists(cand2):
            p = cand2
        else:
            return {"status": "error", "error": f"檔案或目錄不存在: {p}"}
    try:
        if sys.platform == "win32" or os.name == "nt":
            if os.path.isfile(p):
                subprocess.Popen(f'explorer.exe /select,"{p}"', shell=True)
            else:
                subprocess.Popen(f'explorer.exe "{p}"', shell=True)
        else:
            subprocess.Popen(["xdg-open", os.path.dirname(p) if os.path.isfile(p) else p])
        return {"status": "success", "path": p}
    except Exception as e:
        return {"status": "error", "error": str(e)}

class RagSaveDocRequest(BaseModel):
    filename: str
    content: str

@app.post("/api/rag/save")
def api_save_rag_document(req: RagSaveDocRequest):
    """手動將 RAG 知識庫文件或筆記儲存至 rag_docs/ 實體目錄"""
    try:
        save_info = save_converted_markdown(req.filename, req.content)
        return {"status": "success", **save_info}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/rag/list")
def list_rag_assets():
    """自動掃描 assets/RAG/ 及 rag_docs/ 目錄下的所有知識庫文件與範本 (支援 SVG、純文字、Markdown 等)"""
    rag_root = os.path.join(webcom_dir, "assets", "RAG")
    rag_docs_dir = os.path.join(webcom_dir, "rag_docs")
    if not os.path.exists(rag_root):
        os.makedirs(rag_root, exist_ok=True)
    if not os.path.exists(rag_docs_dir):
        os.makedirs(rag_docs_dir, exist_ok=True)
    
    docs = []
    seen_ids = set()

    # 1. 優先掃描使用者一級目錄 rag_docs/
    if os.path.exists(rag_docs_dir):
        for f in os.listdir(rag_docs_dir):
            full_path = os.path.join(rag_docs_dir, f)
            if os.path.isfile(full_path):
                ext = os.path.splitext(f)[1].lower()
                if ext in (".md", ".txt", ".json", ".csv", ".xml", ".svg"):
                    doc_id = f"rag_doc_{f}"
                    seen_ids.add(doc_id)
                    try:
                        with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                            content = fh.read()
                        docs.append({
                            "id": doc_id,
                            "title": f,
                            "filename": f,
                            "rel_path": f"rag_docs/{f}",
                            "saved_path": os.path.abspath(full_path).replace("\\", "/"),
                            "category": "rag_docs",
                            "content": content,
                            "ext": ext,
                            "download_url": f"/rag_docs/{f}"
                        })
                    except Exception as ex:
                        logging.warning(f"Failed to read rag_doc {full_path}: {ex}")

    # 2. 掃描 assets/RAG/ 子目錄與範本
    for root, dirs, files in os.walk(rag_root):
        for f in files:
            full_path = os.path.join(root, f)
            rel_path = os.path.relpath(full_path, rag_root)
            category = os.path.basename(root) if root != rag_root else "General"
            ext = os.path.splitext(f)[1].lower()
            doc_id = f"rag_{rel_path.replace(os.sep, '_')}"
            if doc_id in seen_ids or f"rag_doc_{f}" in seen_ids:
                continue
            seen_ids.add(doc_id)
            try:
                if ext in (".svg", ".txt", ".md", ".json", ".csv", ".xml", ".py", ".yaml", ".yml"):
                    with open(full_path, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    docs.append({
                        "id": doc_id,
                        "title": f"{category}: {f}",
                        "filename": f,
                        "rel_path": rel_path.replace("\\", "/"),
                        "saved_path": os.path.abspath(full_path).replace("\\", "/"),
                        "category": category,
                        "content": content,
                        "ext": ext,
                        "download_url": f"/assets/RAG/{rel_path.replace(os.sep, '/')}"
                    })
            except Exception as ex:
                logging.warning(f"Failed to read RAG file {full_path}: {ex}")
    return {"status": "success", "count": len(docs), "docs": docs}




@app.post("/tools/read_file")
def read_file(req: FileReadRequest):
    try:
        if not os.path.exists(req.filepath):
            return {"status": "error", "error": f"檔案不存在: {req.filepath}"}
        with open(req.filepath, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        return {"status": "success", "content": content}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/tools/write_file")
def write_file(req: FileWriteRequest):
    try:
        os.makedirs(os.path.dirname(os.path.abspath(req.filepath)), exist_ok=True)
        with open(req.filepath, "w", encoding="utf-8") as f:
            f.write(req.content)
        return {"status": "success", "message": f"成功寫入檔案: {req.filepath}"}
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.post("/tools/execute_ssh")
def execute_ssh(req: SSHRequest):
    try:
        import paramiko
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname=req.host, port=req.port, username=req.username, password=req.password, timeout=10)
        stdin, stdout, stderr = client.exec_command(req.command, timeout=20)
        out = stdout.read().decode('utf-8', errors='replace')
        err = stderr.read().decode('utf-8', errors='replace')
        client.close()
        return {"status": "success", "stdout": out, "stderr": err}
    except ImportError:
        return {"status": "error", "error": "後端尚未安裝 paramiko 套件 (pip install paramiko)"}
    except Exception as e:
        return {"status": "error", "error": f"SSH 連線失敗: {str(e)}"}

@app.post("/tools/execute_telnet")
def execute_telnet(req: TelnetRequest):
    try:
        import telnetlib
        tn = telnetlib.Telnet(req.host, req.port, timeout=10)
        if req.username:
            tn.read_until(b"login: ", timeout=5)
            tn.write(req.username.encode('ascii') + b"\n")
        if req.password:
            tn.read_until(b"Password: ", timeout=5)
            tn.write(req.password.encode('ascii') + b"\n")
        
        prompt = req.cmd_prompt.encode('ascii')
        tn.read_until(prompt, timeout=5)
        tn.write(req.command.encode('utf-8') + b"\n")
        out = tn.read_until(prompt, timeout=10).decode('utf-8', errors='replace')
        tn.close()
        return {"status": "success", "stdout": out}
    except Exception as e:
        return {"status": "error", "error": f"Telnet 連線失敗: {str(e)}"}

@app.post("/tools/execute_serial")
def execute_serial(req: SerialRequest):
    try:
        import serial
        import time
        cmd = req.command if req.command is not None else ""
        ser = serial.Serial(req.port, req.baudrate, timeout=2)
        if cmd:
            ser.write((cmd + "\r\n").encode('utf-8'))
        time.sleep(0.3)
        out = ser.read_all().decode('utf-8', errors='replace')
        ser.close()
        return {"status": "success", "stdout": out}
    except ImportError:
        return {"status": "error", "error": "後端尚未安裝 pyserial 套件 (pip install pyserial)"}
    except Exception as e:
        return {"status": "error", "error": f"Serial 操作失敗: {str(e)}"}

@app.get("/tools/list_serial_ports")
def list_serial_ports():
    try:
        import serial.tools.list_ports
        ports = list(serial.tools.list_ports.comports())
        return {
            "status": "success",
            "ports": [{"port": p.device, "description": p.description or p.device} for p in ports]
        }
    except Exception as e:
        return {"status": "error", "error": str(e), "ports": []}

class MCPCallRequest(BaseModel):
    name: str
    arguments: Optional[dict] = {}

@app.get("/mcp/tools/list")
def list_mcp_tools():
    return {
        "tools": [
            {
                "name": "mcp_get_system_info",
                "description": "獲取本機系統資源資訊 (CPU, Memory, Disk, Platform)",
                "inputSchema": {
                    "type": "object",
                    "properties": {}
                }
            },
            {
                "name": "mcp_list_processes",
                "description": "列出本機正在運行的重要系統行程",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filter_name": {"type": "string", "description": "行程名稱過濾條件 (選填)"}
                    }
                }
            },
            {
                "name": "mcp_list_directory",
                "description": "列出指定目錄下的所有檔案與資料夾",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "path": {"type": "string", "description": "目錄絕對路徑或相對路徑"}
                    },
                    "required": ["path"]
                }
            },
            {
                "name": "mcp_analyze_pcb_dxf",
                "description": "分析 PCB 電路板 DXF 檔案，精確計算外框長寬 (mm)、面積 (mm² / cm²)、圖層統計 (Edge.Cuts, F.Cu, Drill, F.SilkS 等) 與零件/鑽孔數量",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dxf_path": {"type": "string", "description": "DXF 檔案路徑 (例如 board.dxf)"},
                        "dxf_content": {"type": "string", "description": "DXF 原始文字內容 (選填)"}
                    }
                }
            },
            {
                "name": "mcp_convert_pcb_dxf_to_geojson",
                "description": "將 PCB 電路板 DXF 轉換為高精度 GeoJSON FeatureCollection，保全奈米/微米級幾何特徵 (BGA 焊盤、0.1mm 走線、圓角弧度)",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "dxf_path": {"type": "string", "description": "DXF 檔案路徑"},
                        "output_geojson_path": {"type": "string", "description": "輸出 GeoJSON 檔案路徑 (選填)"},
                        "unit": {"type": "string", "description": "目標單位: 'mm', 'mil', 'inch', 'um' (預設 'mm')"},
                        "tolerance": {"type": "number", "description": "圓弧弦差容許值 (mm，預設 0.01)"}
                    }
                }
            }
        ]
    }

@app.post("/mcp/tools/call")
def call_mcp_tool(req: MCPCallRequest):
    tool_name = req.name
    args = req.arguments or {}
    
    if tool_name == "mcp_get_system_info":
        import platform
        import psutil
        try:
            mem = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            return {
                "content": [{
                    "type": "text",
                    "text": f"系統: {platform.system()} {platform.release()} ({platform.machine()})\n"
                            f"CPU 核心: {psutil.cpu_count(logical=True)} (使用率: {psutil.cpu_percent()}%)\n"
                            f"記憶體: 已用 {mem.used // (1024**2)}MB / 總共 {mem.total // (1024**2)}MB ({mem.percent}%)\n"
                            f"硬碟: 已用 {disk.used // (1024**3)}GB / 總共 {disk.total // (1024**3)}GB ({disk.percent}%)"
                }]
            }
        except ImportError:
            import platform
            return {
                "content": [{
                    "type": "text",
                    "text": f"系統: {platform.system()} {platform.release()} ({platform.machine()})\n(未安裝 psutil 套件以提供詳細資源資訊)"
                }]
            }
    
    if tool_name == "mcp_list_directory":
        dir_path = args.get("path", ".")
        try:
            if not os.path.exists(dir_path):
                return {"isError": True, "content": [{"type": "text", "text": f"目錄不存在: {dir_path}"}]}
            entries = os.listdir(dir_path)
            details = []
            for item in entries[:100]:
                full = os.path.join(dir_path, item)
                is_dir = os.path.isdir(full)
                sz = os.path.getsize(full) if not is_dir else 0
                details.append(f"[{ 'DIR' if is_dir else 'FILE' }] {item} ({sz} bytes)")
            return {
                "content": [{
                    "type": "text",
                    "text": f"目錄 {dir_path} 清單 ({len(entries)} 項目):\n" + "\n".join(details)
                }]
            }
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": str(e)}]}

    if tool_name == "mcp_analyze_pcb_dxf":
        try:
            from scripts.pcb_dxf_geojson import analyze_pcb_dxf
            dxf_target = args.get("dxf_path") or args.get("path")
            dxf_content = args.get("dxf_content")
            if not dxf_target and not dxf_content:
                return {"isError": True, "content": [{"type": "text", "text": "請提供 dxf_path 或 dxf_content 參數"}]}
            input_data = dxf_content if dxf_content else dxf_target
            res = analyze_pcb_dxf(input_data)
            summary = (
                f"=== PCB 電路板 DXF 幾何與尺寸分析報告 ===\n"
                f"• 電路板長寬: {res['width_mm']} mm × {res['height_mm']} mm\n"
                f"• 電路板面積: {res['area_mm2']} mm² ({res['area_cm2']} cm²)\n"
                f"• 外框 BBox: [Xmin: {res['bbox'][0]}, Ymin: {res['bbox'][1]}, Xmax: {res['bbox'][2]}, Ymax: {res['bbox'][3]}]\n"
                f"• 實體總數: {res['total_features']} 個\n"
                f"• 圖層分佈:\n"
            )
            for l, c in res['layer_breakdown'].items():
                summary += f"  - [{l}]: {c} 個圖元\n"
            return {"content": [{"type": "text", "text": summary}]}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"PCB 分析失敗: {e}"}]}

    if tool_name == "mcp_convert_pcb_dxf_to_geojson":
        try:
            from scripts.pcb_dxf_geojson import PcbDxfGeoJsonConverter
            dxf_target = args.get("dxf_path") or args.get("path")
            dxf_content = args.get("dxf_content")
            out_path = args.get("output_geojson_path")
            target_unit = args.get("unit", "mm")
            tolerance = float(args.get("tolerance", 0.01))
            if not dxf_target and not dxf_content:
                return {"isError": True, "content": [{"type": "text", "text": "請提供 dxf_path 或 dxf_content 參數"}]}
            converter = PcbDxfGeoJsonConverter(target_unit=target_unit, default_tolerance=tolerance)
            input_data = dxf_content if dxf_content else dxf_target
            geojson_data = converter.dxf_to_geojson(input_data)
            dims = geojson_data['metadata']['board_dimensions']
            summary = (
                f"✅ PCB DXF 成功轉為高精度 GeoJSON！\n"
                f"• 單位: {target_unit}\n"
                f"• 尺寸: {dims['width']} mm × {dims['height']} mm (面積: {dims['area_cm2']} cm²)\n"
                f"• 幾何圖元數: {geojson_data['metadata']['total_features']} 個 Feature\n"
            )
            if out_path:
                import json
                with open(out_path, "w", encoding="utf-8") as f:
                    json.dump(geojson_data, f, indent=2, ensure_ascii=False)
                summary += f"• 檔案已儲存至: {out_path}\n"
            else:
                import json
                j_str = json.dumps(geojson_data, ensure_ascii=False)
                if len(j_str) > 1500:
                    summary += f"• GeoJSON 特徵預覽 (前 1500 字元):\n{j_str[:1500]}...\n"
                else:
                    summary += f"• GeoJSON 完整內容:\n{j_str}\n"
            return {"content": [{"type": "text", "text": summary}]}
        except Exception as e:
            return {"isError": True, "content": [{"type": "text", "text": f"PCB 轉檔失敗: {e}"}]}

    if tool_name == "mcp_list_processes":
        import psutil
        try:
            filter_str = (args.get("filter_name") or "").lower()
            procs = []
            for p in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = p.info
                    name = pinfo['name'] or ''
                    if filter_str and filter_str not in name.lower():
                        continue
                    procs.append(f"PID {pinfo['pid']:6d} | {name:25s} | CPU {pinfo.get('cpu_percent', 0.0):4.1f}% | MEM {pinfo.get('memory_percent', 0.0):4.1f}%")
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            return {
                "content": [{
                    "type": "text",
                    "text": "行程清單 (前 30 項):\n" + "\n".join(procs[:30])
                }]
            }
        except ImportError:
            return {"isError": True, "content": [{"type": "text", "text": "未安裝 psutil 套件"}]}

    return {"isError": True, "content": [{"type": "text", "text": f"未知的 MCP 工具: {tool_name}"}]}

if __name__ == "__main__":
    import time
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        res = s.connect_ex(('127.0.0.1', 8001))
        s.close()
        if res == 0:
            current_pid = os.getpid()
            # Try psutil first
            try:
                import psutil
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['pid'] != current_pid:
                        try:
                            for conn in proc.connections(kind='inet'):
                                if conn.laddr.port == 8001 and conn.status == 'LISTEN':
                                    print(f"[info] 釋放被佔用之 8001 埠 (終止舊行程 PID: {proc.info['pid']})...")
                                    proc.kill()
                                    time.sleep(0.8)
                        except Exception:
                            pass
            except Exception:
                pass

            # Windows netstat fallback if port is still bound
            if sys.platform == 'win32':
                try:
                    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    res2 = s2.connect_ex(('127.0.0.1', 8001))
                    s2.close()
                    if res2 == 0:
                        lines = subprocess.check_output('netstat -ano | findstr :8001', shell=True, text=True, stderr=subprocess.DEVNULL).splitlines()
                        for line in lines:
                            parts = line.strip().split()
                            if len(parts) >= 5 and 'LISTENING' in parts:
                                pid = int(parts[-1])
                                if pid != current_pid and pid > 0:
                                    print(f"[info] 透過 netstat 釋放佔用 8001 埠之行程 (PID: {pid})...")
                                    subprocess.run(f"taskkill /F /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                                    time.sleep(0.5)
                except Exception:
                    pass
    except Exception:
        pass
    print("Webcom Daemon 正在啟動於 http://127.0.0.1:8001 ...")
    uvicorn.run(app, host="127.0.0.1", port=8001)


