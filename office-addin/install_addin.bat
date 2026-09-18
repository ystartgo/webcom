@echo off
chcp 65001 >nul
title Webcom Office Add-in Auto Installer

echo ========================================================
echo        Webcom Office 增益集 (Add-in) 自動免共用註冊工具
echo ========================================================
echo.

set "SCRIPT_DIR=%~dp0"
set "SCRIPT_DIR=%SCRIPT_DIR:~0,-1%"

echo [1/3] 偵測目前所在目錄: "%SCRIPT_DIR%"

if not exist "%SCRIPT_DIR%\manifest.xml" (
    echo [錯誤] 找不到增益集清單檔案: "%SCRIPT_DIR%\manifest.xml"
    echo 請確保本腳本與 manifest.xml 放在同一目錄下。
    pause
    exit /b 1
)

:: 1. 本地 Office WEF 直接旁載入 (支援 Office 2016/2019/2021/365 不需要建網路共用)
echo [2/3] 正在建立 Office 本地受信任增益集目錄...
set "WEF_DIR=%APPDATA%\Microsoft\Office\16.0\Wef"
if not exist "%WEF_DIR%" mkdir "%WEF_DIR%" >nul 2>&1

copy /y "%SCRIPT_DIR%\manifest.xml" "%WEF_DIR%\webcom_manifest.xml" >nul 2>&1
if %ERRORLEVEL% equ 0 (
    echo   [✔] 已成功將清單複製至 Office WEF 目錄: "%WEF_DIR%"
) else (
    echo   [!] 複製清單至 WEF 失敗，將使用受信任資料夾註冊。
)

:: 2. 寫入本機路徑至受信任增益集目錄註冊表 (支援磁碟代號如 R:\ 或 C:\)
echo [3/3] 正在註冊受信任增益集目錄到 Windows 註冊表...
set "CATALOG_ID={b781df03-e83c-42b7-a365-d917849182a4}"

reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\%CATALOG_ID%" /v "Id" /t REG_SZ /d "%CATALOG_ID%" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\%CATALOG_ID%" /v "Url" /t REG_SZ /d "%SCRIPT_DIR%" /f >nul 2>&1
reg add "HKCU\Software\Microsoft\Office\16.0\WEF\TrustedCatalogs\%CATALOG_ID%" /v "Flags" /t REG_DWORD /d 1 /f >nul 2>&1

echo.
echo ========================================================
echo 🎉 自動註冊完成！完全免開 Windows 網路共用！
echo.
echo 使用步驟：
echo 1. 請確保 Webcom Daemon 正在運作 (127.0.0.1:8001)。
echo 2. 開啟微軟 Word、Excel 或 PowerPoint。
echo 3. 點選上方功能區 [插入] ➔ [我的增益集]（或 [取得增益集]）。
echo 4. 切換到 [共用資料夾] 分頁，若未顯示請點擊右上角「重新整理」。
echo 5. 點選 [Webcom AI 智慧助理] ➔ [新增] 即可直接開啟側邊欄對話框！
echo ========================================================
echo.
pause