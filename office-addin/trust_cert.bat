@echo off
chcp 65001 >nul
title Webcom Office 增益集 憑證信任與連線修復工具

echo ========================================================
echo   Webcom Office 增益集 (Add-in) 憑證信任與連線修復工具
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "ROOT_DIR=%SCRIPT_DIR%\.."

echo [1/3] 檢查 Webcom Daemon 常駐服務 (Port 8001 / 8002)...
powershell -NoProfile -Command "try { $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8001/health' -TimeoutSec 2 -UseBasicParsing; Write-Host '  [OK] HTTP 8001 常駐服務在線！' -ForegroundColor Green } catch { Write-Host '  [!] 警告: 8001 尚未啟動，請確認已執行 python daemon.py' -ForegroundColor Yellow }"

echo.
echo [2/3] 安裝本機開發者 SSL 信任憑證 (解決桌面版 Word/Excel「連不上」)...
set "CERT_FILE="
if exist "%USERPROFILE%\.office-addin-dev-certs\ca.crt" (
    set "CERT_FILE=%USERPROFILE%\.office-addin-dev-certs\ca.crt"
) else if exist "%ROOT_DIR%\assets\ssl\cert.pem" (
    set "CERT_FILE=%ROOT_DIR%\assets\ssl\cert.pem"
)

if defined CERT_FILE (
    echo   找到本機憑證: "%CERT_FILE%"
    echo   正在註冊至 Windows 受信任的根憑證授權單位...
    echo   (若彈出 Windows 安全性警告對話框，請點選【是】以允許信任)
    certutil -user -addstore Root "%CERT_FILE%"
    echo   [OK] 憑證安裝步驟完成。
) else (
    echo   [!] 尚未產生憑證，請先啟動一次 python daemon.py。
)

echo.
echo [3/3] 為 Weboffice (網頁版 Word/Excel) 建立瀏覽器信任授權...
echo   正在為您在瀏覽器開啟增益集端點:
echo   https://127.0.0.1:8002/office-addin/taskpane.html
echo.
echo   ★ 關鍵步驟 (Weboffice 必做一次):
echo   1. 瀏覽器若顯示「您的連線不是私人連線」
echo   2. 請點擊【進階】 -^> 【繼續前往 127.0.0.1 (不安全)】
echo   3. 看到 Webcom AI 畫面後，切回 Weboffice (Word Online)，增益集就能立刻連線！
echo ========================================================
echo.
start https://127.0.0.1:8002/office-addin/taskpane.html
pause
