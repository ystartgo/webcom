@echo off
chcp 65001 >nul
title Webcom Office Add-in 一鍵註冊安裝工具

echo ========================================================
echo        Webcom Office 增益集 (Add-in) 自動免共用註冊工具
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"
set "MANIFEST_PATH=%SCRIPT_DIR%\manifest.xml"

echo [1/4] 檢查增益集清單檔案:
if not exist "%MANIFEST_PATH%" (
    echo   [錯誤] 找不到 manifest.xml！
    echo   請確認本工具位於 office-addin 資料夾內。
    echo.
    pause
    exit /b 1
)
echo   [OK] 清單檔案就緒: "%MANIFEST_PATH%"

echo.
echo [2/4] 寫入 Office 開發者直接旁載 (Sideload) 註冊表...
:: 微軟官方推薦之免開網路共用開發者旁載註冊
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\Developer" /v "%MANIFEST_PATH%" /t REG_SZ /d "%MANIFEST_PATH%" /f >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [OK] 已成功註冊至 Office WEF Developer 登錄檔！
) else (
    echo   [!] 注意: 寫入 Developer 註冊表可能受限。
)

echo.
echo [3/4] 檢查並設定網路共用目錄 (雙重保障)...
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
echo [4/4] 清除 Office 快取以確保立即載入最新清單...
if exist "%LOCALAPPDATA%\Microsoft\Office\16.0\Wef" (
    del /s /q "%LOCALAPPDATA%\Microsoft\Office\16.0\Wef\*.*" >nul 2>&1
    echo   [OK] 已清除 Office WEF 快取。
) else (
    echo   [OK] Office WEF 快取乾淨。
)

echo.
echo ========================================================
echo  🎉 增益集註冊設定已完成！
echo ========================================================
echo.
echo 【如何立即在 Office 中使用 Webcom】:
echo.
echo  方法一 (最推薦・自動載入):
echo    1. 若 Word、Excel 或 PowerPoint 正在執行，請「完全關閉後重新開啟」。
echo    2. 開啟後，上方功能區 (Ribbon) 會自動出現【Webcom AI】標籤頁！
echo    3. 點擊【開啟 Webcom 對話】即可展開側邊對話面板。
echo.
echo  方法二 (手動上傳・1秒完成，免看快取):
echo    1. 在 Word 或 Excel 中，點擊上方功能區【插入】 -^> 【我的增益集】。
echo    2. 點擊右上角的「管理我的增益集」下拉箭頭，選擇【上傳我的增益集】。
echo    3. 瀏覽並選取此檔案:
echo       "%MANIFEST_PATH%"
echo    4. 點擊【上傳】，增益集立即載入！
echo.
echo  方法三 (共用資料夾分頁):
echo    若您在【插入】 -^> 【我的增益集】 -^> 【共用資料夾】分頁中查看，
echo    請務必點擊右上角的【🔄 重新整理】圖示，Office 即會顯示可用增益集！
echo.
echo ========================================================
echo.
pause
