import os
import sys
import json
import urllib.request

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODELS_DIR = os.path.join(BASE_DIR, "models")
os.makedirs(MODELS_DIR, exist_ok=True)

DEFAULT_MODEL = "Qwen2.5-0.5B-Instruct-q4f16_1-MLC"

def download_file(url, dest_path):
    print(f"  Downloading: {url} -> {os.path.basename(dest_path)}")
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Webcom-Offline-Model-Downloader/1.0'})
        with urllib.request.urlopen(req) as resp, open(dest_path, 'wb') as f:
            total_size = resp.info().get('Content-Length')
            if total_size:
                total_size = int(total_size)
            dl = 0
            block_size = 1024 * 1024  # 1MB
            while True:
                buf = resp.read(block_size)
                if not buf:
                    break
                dl += len(buf)
                f.write(buf)
                if total_size:
                    pct = (dl / total_size) * 100
                    mb = dl / (1024 * 1024)
                    tot_mb = total_size / (1024 * 1024)
                    print(f"\r    [{pct:5.1f}%] {mb:6.1f}MB / {tot_mb:6.1f}MB", end="", flush=True)
            print()
        return True
    except Exception as e:
        print(f"\n    [ERROR] Download failed: {e}")
        if os.path.exists(dest_path):
            os.remove(dest_path)
        return False

def download_model(model_name=DEFAULT_MODEL):
    target_dir = os.path.join(MODELS_DIR, model_name)
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"\n=======================================================")
    print(f" Downloading Offline WebLLM Model: {model_name}")
    print(f" Destination: {target_dir}")
    print(f"=======================================================")

    hf_base = f"https://huggingface.co/mlc-ai/{model_name}/resolve/main"

    # Step 1: Download ndarray-cache.json to inspect shards
    cache_json_url = f"{hf_base}/ndarray-cache.json"
    cache_json_path = os.path.join(target_dir, "ndarray-cache.json")
    if not download_file(cache_json_url, cache_json_path):
        print(f"Failed to download ndarray-cache.json from {cache_json_url}")
        return False

    # Essential config and tokenizer files
    essential_files = [
        "mlc-chat-config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "vocab.json",
        "merges.txt"
    ]
    for fn in essential_files:
        url = f"{hf_base}/{fn}"
        dest = os.path.join(target_dir, fn)
        download_file(url, dest)

    # Parse shards from ndarray-cache.json
    try:
        with open(cache_json_path, "r", encoding="utf-8") as f:
            cache_data = json.load(f)
        records = cache_data.get("records", [])
        shard_files = set()
        for r in records:
            if "dataPath" in r:
                shard_files.add(r["dataPath"])
        
        print(f"\n  Found {len(shard_files)} parameter shard file(s)...")
        for sf in sorted(shard_files):
            shard_url = f"{hf_base}/{sf}"
            shard_dest = os.path.join(target_dir, sf)
            download_file(shard_url, shard_dest)
    except Exception as e:
        print(f"Error parsing parameter shards: {e}")

    # Download wasm model lib
    wasm_map = {
        "Qwen2.5-0.5B-Instruct-q4f16_1-MLC": "Qwen2-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm",
        "Qwen2.5-1.5B-Instruct-q4f16_1-MLC": "Qwen2-1.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm",
        "Qwen2.5-3B-Instruct-q4f16_1-MLC": "Qwen2.5-3B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm",
        "Llama-3.2-1B-Instruct-q4f16_1-MLC": "Llama-3.2-1B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm",
        "SmolLM2-360M-Instruct-q0f16-MLC": "SmolLM2-360M-Instruct-q0f16-ctx4k_cs1k-webgpu.wasm"
    }
    wasm_filename = wasm_map.get(model_name, "Qwen2.5-3B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm" if "3B" in model_name else "Qwen2-0.5B-Instruct-q4f16_1-ctx4k_cs1k-webgpu.wasm")
    wasm_url = f"https://raw.githubusercontent.com/mlc-ai/binary-mlc-llm-libs/main/web-llm-models/v0_2_48/{wasm_filename}"
    wasm_dest = os.path.join(MODELS_DIR, wasm_filename)
    download_file(wasm_url, wasm_dest)

def download_onnx_model(model_name="onnx-community/Qwen2.5-0.5B-Instruct"):
    target_dir = os.path.join(MODELS_DIR, model_name.replace("/", os.sep))
    os.makedirs(target_dir, exist_ok=True)
    
    print(f"\n=======================================================")
    print(f" Downloading Offline ONNX Model: {model_name}")
    print(f" Destination: {target_dir}")
    print(f"=======================================================")

    hf_base = f"https://huggingface.co/{model_name}/resolve/main"

    essential_files = [
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt"
    ]
    for fn in essential_files:
        url = f"{hf_base}/{fn}"
        dest = os.path.join(target_dir, fn)
        download_file(url, dest)

    # ONNX model files inside onnx/ subfolder
    onnx_dir = os.path.join(target_dir, "onnx")
    os.makedirs(onnx_dir, exist_ok=True)
    
    onnx_files = [
        "model_q4.onnx",
        "model_q4.onnx_data",
        "model_quantized.onnx",
        "model_quantized.onnx_data",
        "model.onnx",
        "model.onnx_data"
    ]
    for of in onnx_files:
        url = f"{hf_base}/onnx/{of}"
        dest = os.path.join(onnx_dir, of)
        download_file(url, dest)

    print(f"\n✅ ONNX Model {model_name} offline download complete!")
    print(f"Files stored in: {target_dir}")
    return True

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_MODEL
    if "onnx" in target.lower() or "xenova" in target.lower() or "/" in target:
        download_onnx_model(target)
    else:
        download_model(target)

