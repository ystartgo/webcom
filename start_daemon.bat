@echo off
REM ============================================================
REM Webcom Daemon (Port 8001) — One-click Windows launcher
REM   Auto-detects python / py launcher; installs requirements
REM   if missing; auto-restarts after a crash (daemon style).
REM ============================================================
setlocal
cd /d "%~dp0"

REM --- 1) Resolve python interpreter ---------------------------
set PY=
where py      >nul 2>nul && set PY=py -3
if not defined PY where python >nul 2>nul && set PY=python
if not defined PY (
    echo [ERROR] Python 3 is not installed or not in PATH.
    echo         Please install Python 3.10+ from https://www.python.org
    echo         (tick "Add python.exe to PATH" during installation)
    pause
    exit /b 1
)
echo [1/3] Using interpreter: %PY%

REM --- 2) Auto-install missing dependencies --------------------
echo [2/3] Checking requirements...
%PY% -c "import fastapi, uvicorn, paramiko, serial" >nul 2>nul
if errorlevel 1 (
    echo       Missing packages detected — running pip install -r requirements.txt
    %PY% -m pip install --disable-pip-version-check -r requirements.txt
    if errorlevel 1 (
        echo [ERROR] pip install failed. Check network/pip.
        pause
        exit /b 2
    )
) else (
    echo       All required packages OK.
)

REM --- 3) Launch daemon (auto-restart on crash) ----------------
echo [3/3] Starting Webcom Daemon on http://127.0.0.1:8001 ...
echo       Press Ctrl+C twice to stop.
:loop
%PY% daemon.py
echo.
echo [warn] Daemon exited with code %ERRORLEVEL%. Restarting in 3s ...
timeout /t 3 /nobreak >nul
goto loop
