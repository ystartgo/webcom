@echo off
setlocal
title Register Webcom URL Protocol
cd /d "%~dp0"
echo ===================================================
echo   正在為 Windows 註冊 webcom:// 一鍵網頁靜默啟動協定
echo ===================================================
set "APP_DIR=%~dp0"
set "VBS_PATH=%APP_DIR%silent_daemon.vbs"

reg add "HKCU\Software\Classes\webcom" /ve /d "URL:Webcom Daemon Launcher" /f >nul
reg add "HKCU\Software\Classes\webcom" /v "URL Protocol" /d "" /f >nul
reg add "HKCU\Software\Classes\webcom\shell\open\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul

echo.
echo [成功] 已完成註冊！前台網頁點擊按鈕將於背景完全靜默啟動，無視窗干擾！
echo.
pause
