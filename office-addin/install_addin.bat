@echo off
chcp 65001 >nul
title Webcom Office Add-in Auto Installer

echo ========================================================
echo        Webcom Office Add-in Auto Register Tool
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo [1/3] Current Directory: "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%\manifest.xml" (
    echo [ERROR] Cannot find manifest.xml in: "%SCRIPT_DIR%"
    echo Please make sure this script is in the same folder as manifest.xml.
    pause
    exit /b 1
)

:: 1. Copy manifest to Office WEF folder directly
echo [2/3] Registering manifest into Office local WEF cache...
set "WEF_DIR=%APPDATA%\Microsoft\Office\16.0\Wef"
if not exist "%WEF_DIR%" mkdir "%WEF_DIR%" >nul 2>&1

copy /y "%SCRIPT_DIR%\manifest.xml" "%WEF_DIR%\webcom_manifest.xml" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [OK] Copied manifest to WEF folder: "%WEF_DIR%"
) else (
    echo   [!] Note: Direct WEF copy skipped, relying on TrustedCatalogs registry.
)

:: 2. Register TrustedCatalogs to HKCU
echo [3/3] Registering TrustedCatalogs to Windows Registry...
set "CATALOG_ID={b781df03-e83c-42b7-a365-d917849182a4}"

reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\%CATALOG_ID%" /v "Id" /t REG_SZ /d "%CATALOG_ID%" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\%CATALOG_ID%" /v "Url" /t REG_SZ /d "%SCRIPT_DIR%" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\%CATALOG_ID%" /v "Flags" /t REG_DWORD /d 1 /f >nul 2>&1

echo.
echo ========================================================
echo Registration Completed Successfully!
echo.
echo Quick Steps:
echo 1. Ensure Webcom Daemon is running at 127.0.0.1:8001
echo 2. Open Microsoft Word, Excel or PowerPoint
echo 3. Go to top Ribbon: Insert - My Add-ins (or Get Add-ins)
echo 4. Switch to the SHARED FOLDER tab (click Refresh on top right if needed)
echo 5. Click on 'Webcom AI Assistant' and click Add to start!
echo ========================================================
echo.
pause