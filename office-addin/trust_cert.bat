@echo off
chcp 65001 >nul
title Webcom SSL 憑證受信任清單自動安裝工具

:: 1. 自動檢測並請求系統管理員權限 (確保 100% 寫入本機受信任根憑證清單)
net session >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo [提示] 正在請求系統管理員權限以自動寫入 Windows 受信任根憑證清單...
    powershell -NoProfile -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

echo ========================================================
echo   Webcom SSL 憑證受信任清單自動安裝工具 (view.yia.app)
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "CERT_FILE=%SCRIPT_DIR%view.yia.app.crt"
if not exist "%CERT_FILE%" set "CERT_FILE=%SCRIPT_DIR%..\assets\ssl\cert.crt"
if not exist "%CERT_FILE%" set "CERT_FILE=%SCRIPT_DIR%..\assets\ssl\cert.pem"

if not exist "%CERT_FILE%" (
    echo [錯誤] 找不到憑證檔案: "%CERT_FILE%"
    echo 請先啟動一次 python daemon.py 以自動產生憑證。
    echo.
    pause
    exit /b 1
)

echo 找到憑證檔案: "%CERT_FILE%"
echo.

echo [1/3] 正在寫入【本機電腦 (Local Machine)】受信任的根憑證授權單位 (Root)...
certutil -addstore -f Root "%CERT_FILE%"
if %ERRORLEVEL% equ 0 (
    echo   [OK] 本機電腦受信任清單安裝成功！
) else (
    echo   [!] 本機電腦安裝略過或受限。
)

echo.
echo [2/3] 正在寫入【目前使用者 (Current User)】受信任的根憑證授權單位 (Root)...
certutil -user -f -addstore Root "%CERT_FILE%"
if %ERRORLEVEL% equ 0 (
    echo   [OK] 目前使用者受信任清單安裝成功！
) else (
    echo   [!] 目前使用者安裝略過或受限。
)

echo.
echo [3/3] 檢查受信任清單驗證狀態...
certutil -store Root view.yia.app >nul 2>&1
set "IN_MACHINE_ROOT=%ERRORLEVEL%"
certutil -store -user Root view.yia.app >nul 2>&1
set "IN_USER_ROOT=%ERRORLEVEL%"

echo.
if %IN_MACHINE_ROOT% equ 0 (
    echo  🎉【成功】view.yia.app 憑證已成功加入本機電腦受信任清單！
    echo      Word、Excel、Edge、Chrome 均可直接安全存取，絕不跳出警告！
) else if %IN_USER_ROOT% equ 0 (
    echo  🎉【成功】view.yia.app 憑證已成功加入使用者受信任清單！
    echo      Word、Excel、Edge、Chrome 均可直接安全存取，絕不跳出警告！
) else (
    echo  ⚠️ 憑證未自動加入。您也可以直接在此目錄雙擊【view.yia.app.crt】:
    echo     1. 點擊「安裝憑證」
    echo     2. 選擇「本機電腦」或「目前使用者」
    echo     3. 勾選「將所有憑證放入下列存放區」-^> 瀏覽選擇【受信任的根憑證授權單位】
    echo     4. 點擊「下一步」完成安裝即可！
)

echo.
echo ========================================================
pause
