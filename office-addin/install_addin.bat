@echo off
chcp 65001 >nul
echo ========================================================
echo        Webcom Office 增益集 (Add-in) 快速旁載入設定工具
echo ========================================================
echo.
echo 正在為微軟 Office (Word / Excel / PowerPoint) 註冊增益集清單目錄...
echo.

set "ADDIN_DIR=C:\Apps\Webcom\office-addin"

if not exist "%ADDIN_DIR%\manifest.xml" (
    echo [錯誤] 找不到增益集清單檔案: %ADDIN_DIR%\manifest.xml
    pause
    exit /b 1
)

:: 1. 建立 Windows 共用資料夾 (Shared Folder Sideloading)
echo [1/2] 正在檢查網路共用設定...
net share WebcomAddin="%ADDIN_DIR%" /grant:everyone,READ >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [?] 已建立網路共用 \\localhost\WebcomAddin
) else (
    echo   [!] 共用已存在或需要系統管理員權限，略過共用建立。
)

:: 2. 寫入 Office 受信任增益集目錄註冊表
echo [2/2] 正在註冊 Office 受信任的增益集目錄...
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /v "Id" /t REG_SZ /d "{b781df03-e83c-42b7-a365-d917849182a4}" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /v "Url" /t REG_SZ /d "\\localhost\WebcomAddin" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\{b781df03-e83c-42b7-a365-d917849182a4}" /v "Flags" /t REG_DWORD /d 1 /f >nul 2>&1

echo.
echo ========================================================
echo ?? 設定完成！
echo.
echo 使用說明：
echo 1. 請確保 Webcom Daemon 常駐程式正在運作 (Port 8001)。
echo 2. 開啟微軟 Word、Excel 或 PowerPoint。
echo 3. 點選上方 [插入] ? [增益集 / 我的增益集] ? [共用資料夾]。
echo 4. 即可看到 [Webcom AI 智慧助理]，點擊 [新增/啟用] 即可在側邊展開對話框！
echo ========================================================
echo.
pause