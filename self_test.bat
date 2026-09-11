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
if exist "%~dp0python\python.exe" set "PY=%~dp0python\python.exe"
if not defined PY where python >nul 2>&1 && set "PY=python"
if not defined PY where py >nul 2>&1 && set "PY=py -3"

if not defined PY (
    echo [ERROR] 找不到 Python 執行環境，無法執行自我檢測！
    pause
    exit /b 1
)

"%PY%" "%~dp0diagnose_system.py"
if %errorlevel% neq 0 (
    echo.
    echo ---------------------------------------------------
    echo [提示] 若檢測到依賴套件缺失，可執行 install_dependencies.bat 一鍵安裝。
    echo ---------------------------------------------------
)
goto :done
:done
echo.
echo 請按任意鍵退出...
pause >nul