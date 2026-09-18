@echo off
chcp 65001 >nul
title Webcom Office Add-in 一鍵註冊安裝工具

echo ========================================================
echo        Webcom Office 增益集 (Add-in) 自動免共用註冊工具
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "ROOT_DIR=%SCRIPT_DIR%\.."
set "MANIFEST_PATH=%SCRIPT_DIR%\manifest.xml"

echo [1/5] 檢查增益集清單檔案:
if not exist "%MANIFEST_PATH%" (
    echo   [錯誤] 找不到 manifest.xml！
    echo   請確認本工具位於 office-addin 資料夾內。
    echo.
    pause
    exit /b 1
)
echo   [OK] 清單檔案就緒: "%MANIFEST_PATH%"

echo.
echo [2/5] 寫入 Office 開發者直接旁載 (Sideload) 註冊表...
:: 微軟官方推薦之免開網路共用開發者旁載註冊
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\Developer" /v "%MANIFEST_PATH%" /t REG_SZ /d "%MANIFEST_PATH%" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [OK] 已成功註冊至 Office WEF Developer 登錄檔！
) else (
    echo   [!] 注意: 寫入 Developer 註冊表可能受限。
)

echo.
echo [3/5] 檢查並設定網路共用目錄 (雙重保障)...
net share WebcomAddin="%SCRIPT_DIR%" /grant:Everyone,READ >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [OK] 已成功建立 Windows 共用: \\localhost\WebcomAddin
    reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /v "Id" /t REG_SZ /d "{b781df03-e83c-42b7-a365-d917849182a4}" /f >nul 2>&1
    reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /v "Url" /t REG_SZ /d "\\localhost\WebcomAddin" /f >nul 2>&1
    reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /v "Flags" /t REG_DWORD /d 1 /f >nul 2>&1
) else (
    echo   [提示] 免開共用模式已啟動 (直接透過開發者登錄檔載入，無須網路共用權限)。
    reg delete "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /f >nul 2>&1
)

echo.
echo [4/5] 清除 Office 快取以確保立即載入最新清單...
if exist "%LOCALAPPDATA%\Microsoft\Office\16.0\Wef" (
    del /s /q "%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\*.*" >nul 2>&1
    echo   [OK] 已清除 Office WEF 快取。
) else (
    echo   [OK] Office WEF 快取乾淨。
)

echo.
echo [5/5] 設定本機開發者 SSL 憑證信任 (解決「連不上」問題)...
set "CERT_FILE="
if exist "%USERPROFILE%\.office-addin-dev-certs\ca.crt" (
    set "CERT_FILE=%USERPROFILE%\.office-addin-dev-certs\ca.crt"
) else if exist "%ROOT_DIR%\assets\ssl\cert.pem" (
    set "CERT_FILE=%ROOT_DIR%\assets\ssl\cert.pem"
)

if defined CERT_FILE (
    echo   找到本機 SSL 憑證，註冊至 Windows 受信任根授權單位...
    echo   (若彈出 Windows 警告對話框，請點選【是】以信任本機通訊)
    certutil -user -addstore Root "%CERT_FILE%" >nul 2>&1
    echo   [OK] SSL 憑證信任已就緒。
) else (
    echo   [提示] 憑證將於首次啟動 python daemon.py 時自動建立。
)

echo.
echo ========================================================
echo  🎉 增益集註冊設定已完成！
echo ========================================================
echo.
echo 【常見「連不上」解決方法】:
echo  1. 請確認已啟動常駐後端:
echo     在終端機執行 python daemon.py，看到 8001 與 8002 啟動訊息。
echo.
echo  2. 若在 Weboffice (網頁版 Word/Excel) 看到連不上:
echo     請在同一個瀏覽器開啟新分頁前往:
echo     https://127.0.0.1:8002/office-addin/taskpane.html
echo     點擊【進階】 -^> 【繼續前往 127.0.0.1 (不安全)】允許信任一次即可！
echo.
echo  3. 若在桌面版 Word/Excel 看到連不上:
echo     請直接執行本目錄下的 trust_cert.bat 進行憑證授權。
echo ========================================================
echo.
pause
