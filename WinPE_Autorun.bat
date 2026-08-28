@echo off
setlocal
title Webcom WinPE Launcher

cd /d "%~dp0"

echo ===================================================
echo   Webcom - WinPE Portable AI Console Launcher
echo ===================================================
echo Starting background daemon service on Port 8001...

start "Webcom Daemon Service" /min "%~dp0start_daemon.bat"

echo Opening Web Console in default browser...
start "" "%~dp0index.html"

echo.
echo [OK] Webcom is up and running in WinPE!
timeout /t 2 >nul
exit /b 0
