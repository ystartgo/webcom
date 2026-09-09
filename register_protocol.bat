@echo off
title Register Webcom URL Protocol
cd /d "%~dp0"

echo ===================================================
echo   Registering webcom:// Silent URL Protocol
echo ===================================================

set "APP_DIR=%~dp0"
set "VBS_PATH=%APP_DIR%silent_daemon.vbs"

reg add "HKCU\Software\Classes\webcom" /ve /d "URL:Webcom Daemon Launcher" /f >nul
reg add "HKCU\Software\Classes\webcom" /v "URL Protocol" /d "" /f >nul
reg add "HKCU\Software\Classes\webcom\shell\open\command" /ve /d "wscript.exe \"%VBS_PATH%\" \"%%1\"" /f >nul

if %errorlevel% equ 0 (
    echo.
    echo [OK] Successfully registered webcom:// silent protocol!
    echo      Webpage can now launch the daemon in background without any window.
) else (
    echo.
    echo [ERROR] Registration failed. Please check registry permissions.
)

echo.
pause
