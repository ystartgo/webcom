#!/usr/bin/env bash
# ============================================================
# scripts/start_daemon_wsl.sh — Webcom Daemon launcher for WSL
#
#  1. Auto-selects a python interpreter:  .venv/bin/python3  >
#     ./python/bin/python3  >  system python3
#  2. Auto-installs requirements with pip if FastAPI is missing
#  3. Launches daemon.py bound to 0.0.0.0:8001 (so Windows/LAN
#     hosts can reach it as well as localhost).
#
# Usage:
#   chmod +x scripts/start_daemon_wsl.sh
#   ./scripts/start_daemon_wsl.sh                        # foreground
#   nohup ./scripts/start_daemon_wsl.sh > logs/daemon_wsl.log 2>&1 &
# ============================================================
set -euo pipefail

# Resolve project root = parent dir of the scripts/ folder this file lives in
SCRIPT_DIR="$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_ROOT="$( cd "${SCRIPT_DIR}/.." && pwd )"
cd "${PROJECT_ROOT}"

mkdir -p logs

# -------- 1) Resolve python interpreter ----------------------------
PY=""
if [[ -x "${PROJECT_ROOT}/.venv/bin/python3" ]]; then
    PY="${PROJECT_ROOT}/.venv/bin/python3"
elif [[ -x "${PROJECT_ROOT}/python/bin/python3" ]]; then
    PY="${PROJECT_ROOT}/python/bin/python3"
elif command -v python3 >/dev/null 2>&1; then
    PY="python3"
elif command -v python >/dev/null 2>&1; then
    PY="python"
else
    echo "[ERROR] No python3/python interpreter found (looked in .venv/, ./python/, PATH)."
    echo "        Install python3.10+ or create a venv:  python3 -m venv .venv"
    exit 1
fi
echo "[1/3] Using interpreter: ${PY}  ($(${PY} --version 2>&1))"

# -------- 2) Auto-install requirements if FastAPI is missing ------
echo "[2/3] Checking dependencies..."
if ! "${PY}" -c "import fastapi, uvicorn, paramiko, serial" >/dev/null 2>&1; then
    echo "      Missing packages. Running  pip install -r requirements.txt  ..."
    "${PY}" -m pip install --disable-pip-version-check --upgrade pip >/dev/null
    "${PY}" -m pip install --disable-pip-version-check -r requirements.txt || {
        echo "[ERROR] pip install -r requirements.txt FAILED. Aborting."
        exit 2
    }
else
    echo "      All required packages already present."
fi

# -------- 3) Launch daemon (listen on all IFs, port 8001) --------
echo "[3/3] Starting Webcom Daemon on 0.0.0.0:8001  (project=${PROJECT_ROOT})"
echo "      Press Ctrl+C to stop. Logs append to logs/daemon_wsl.log."
export PYTHONUNBUFFERED=1
exec "${PY}" -u daemon.py
