import os
import sys
import urllib.request

VERSION = "v0.26.4"
BASE_URL = f"https://cdn.jsdelivr.net/pyodide/{VERSION}/full/"
TARGET_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dist")

CORE_FILES = [
    "pyodide.js",
    "pyodide.asm.js",
    "pyodide.asm.wasm",
    "python_stdlib.zip",
    "pyodide-lock.json"
]

def download_pyodide_core():
    os.makedirs(TARGET_DIR, exist_ok=True)
    print(f"=== Downloading Pyodide {VERSION} Core to {TARGET_DIR} ===")
    for fname in CORE_FILES:
        target_path = os.path.join(TARGET_DIR, fname)
        if os.path.exists(target_path) and os.path.getsize(target_path) > 0:
            print(f"  [Skip] {fname} already exists ({os.path.getsize(target_path)} bytes)")
            continue
        url = BASE_URL + fname
        print(f"  [Downloading] {url} -> {fname} ...")
        try:
            urllib.request.urlretrieve(url, target_path)
            print(f"  [✔ Done] {fname} ({os.path.getsize(target_path)} bytes)")
        except Exception as e:
            print(f"  [✖ Failed] {fname}: {e}")

if __name__ == "__main__":
    download_pyodide_core()
