import os
import urllib.request
import ssl

ssl_context = ssl._create_unverified_context()

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
os.makedirs(ASSETS_DIR, exist_ok=True)

RESOURCES = [
    {
        "filename": "tailwindcss.js",
        "url": "https://cdn.tailwindcss.com"
    },
    {
        "filename": "lucide.min.js",
        "url": "https://unpkg.com/lucide@latest"
    },
    {
        "filename": "marked.min.js",
        "url": "https://cdn.jsdelivr.net/npm/marked/marked.min.js"
    },
    {
        "filename": "wterm.bundle.js",
        "url": "https://cdn.jsdelivr.net/npm/@wterm/dom@0.3.4/dist/index.js",
        "optional_if_exists": True
    },
    {
        "filename": "wterm.css",
        "url": "https://cdn.jsdelivr.net/npm/@wterm/dom@0.3.4/src/terminal.css",
        "optional_if_exists": True
    },
    {
        "filename": "webllm.bundle.js",
        "url": "https://esm.run/@mlc-ai/web-llm",
        "optional_if_exists": True
    },
    {
        "filename": "transformers.min.js",
        "url": "https://cdn.jsdelivr.net/npm/@huggingface/transformers@3.3.3/dist/transformers.min.js",
        "optional_if_exists": True
    }
]

print("===================================================")
print("  Downloading Webcom Offline Assets (斷網離線資源包)")
print("===================================================")

for res in RESOURCES:
    dest_path = os.path.join(ASSETS_DIR, res["filename"])
    if res.get("optional_if_exists") and os.path.exists(dest_path) and os.path.getsize(dest_path) > 0:
        print(f"[*] {res['filename']} already exists ({os.path.getsize(dest_path)/1024:.1f} KB), keeping local bundle.")
        continue
    print(f"[*] Downloading {res['filename']} from {res['url']} ...")
    try:
        req = urllib.request.Request(
            res["url"],
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        )
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as response:
            content = response.read()
            with open(dest_path, "wb") as f:
                f.write(content)
        size_kb = len(content) / 1024
        print(f"    [SUCCESS] Saved to {dest_path} ({size_kb:.1f} KB)")
    except Exception as e:
        print(f"    [ERROR] Failed to download {res['filename']}: {e}")

print("===================================================")
print("  Offline assets download completed!")
print("===================================================")
