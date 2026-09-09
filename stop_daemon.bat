@echo off
REM ============================================================
REM Webcom Daemon - Stop Service (Port 8001)
REM ============================================================
setlocal
cd /d "%~dp0"

echo Stopping Webcom Daemon (Port 8001)...

REM 1. Terminate any background start_daemon.bat loop
powershell -NoProfile -Command "Get-CimInstance Win32_Process -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*start_daemon.bat*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }" >nul 2>&1

REM 2. Try graceful shutdown via HTTP
powershell -NoProfile -Command "try { Invoke-RestMethod -Uri 'http://127.0.0.1:8001/shutdown' -Method Post -TimeoutSec 1 | Out-Null } catch {}" >nul 2>&1

REM 3. Ensure any process occupying port 8001 is terminated
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

echo.
echo ============================================================
echo  [OK] Webcom Daemon (Port 8001) has been stopped.
echo ============================================================
ping 127.0.0.1 -n 3 >nul
exit /b 0
