@echo off
REM ============================================================
REM  scripts\start_daemon_wsl.bat  —  Launch Webcom Daemon on WSL from Windows
REM
REM  1. Ensures default WSL distro is running.
REM  2. Mounts or copies project (if ~/workspace/webcom exists uses that)
REM  3. Calls  scripts/start_daemon_wsl.sh  inside WSL.
REM
REM  Usage (Windows PowerShell / CMD):
REM      scripts\start_daemon_wsl.bat
REM      scripts\start_daemon_wsl.bat  Ubuntu-22.04    (override distro name)
REM ============================================================
setlocal
cd /d "%~dp0\.."

set "DISTRO=%~1"
if "%DISTRO%"=="" (
    REM use default distro
    for /f "tokens=2 delims==" %%D in ('wsl --status 2^>nul ^| findstr /i /c:"Default Distribution"') do set "DISTRO=%%D"
    if "!DISTRO!"=="" set "DISTRO=Ubuntu"
)
call :trim DISTRO

echo [WSL launcher] distro = %DISTRO%
echo [WSL launcher] making sure distro is running...
wsl -d "%DISTRO%" -- echo "  -> WSL ok.  user=$(id -un), pwd=$(pwd)" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Failed to contact WSL distro "%DISTRO%".
    echo         Install it via:  wsl --install -d Ubuntu-22.04
    echo         or list existing:  wsl -l -v
    pause
    exit /b 1
)

echo [WSL launcher] ensuring ~/workspace/webcom exists + scripts are executable...
wsl -d "%DISTRO%" -- bash -lc "set -e ; \
  SRC='/mnt/c/Apps/Webcom/github'; \
  if [ -d '/mnt/c/Apps/Webcom' ] && [ -f '/mnt/c/Apps/Webcom/daemon.py' ]; then SRC='/mnt/c/Apps/Webcom'; fi; \
  mkdir -p ~/workspace; \
  if [ ! -d ~/workspace/webcom/daemon.py ]; then cp -r \${SRC}/* ~/workspace/webcom/ 2>/dev/null || true; fi; \
  chmod +x ~/workspace/webcom/scripts/start_daemon_wsl.sh 2>/dev/null || true; \
  mkdir -p ~/workspace/webcom/logs; \
  echo '  -> project location: ' ~/workspace/webcom"

echo.
echo [WSL launcher] launching daemon (foreground). Ctrl+C to stop.
echo.
REM foreground run inside the user's default WSL login shell
wsl -d "%DISTRO%" -- bash -lc "cd ~/workspace/webcom && exec ./scripts/start_daemon_wsl.sh"

exit /b %ERRORLEVEL%

:trim
for /f "tokens=* delims= " %%a in ("%~1") do set "%~1=%%a"
goto :eof
