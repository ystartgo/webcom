@echo off
setlocal
chcp 65001 >nul
title Webcom System Self-Diagnostics (自我檢測工具)
cd /d "%~dp0"
echo ===================================================
echo   Webcom AI 控制台 — 系統與功能自我健康檢測
echo ===================================================
echo.

set "PY="
if exist "%~dp0python\python.exe" (
    set "PY=%~dp0python\python.exe"
    goto :py_found
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto :py_found
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py -3"
    goto :py_found
)

for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
) do (
    if exist %%P (
        if not defined PY set "PY=%%~fP"
    )
)
if defined PY goto :py_found

echo [ERROR] 找不到 Python 執行環境，無法執行自我檢測！
echo 請安裝 Python 3.10+ (勾選 Add python.exe to PATH)
pause
exit /b 1

:py_found
"%PY%" "%~dp0diagnose_system.py"
if %errorlevel% neq 0 (
    echo.
    echo ---------------------------------------------------
    echo [提示] 若檢測到依賴套件缺失，可執行 install_dependencies.bat 一鍵安裝。
    echo ---------------------------------------------------
)
echo.
echo 請按任意鍵退出...
pause >nul
