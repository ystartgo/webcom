@echo off
setlocal
chcp 65001 >nul
title Webcom System Self-Diagnostics (自我檢測工具)
cd /d "%~dp0"
echo ===================================================
echo   Webcom AI 控制台 — 系統與功能自我健康檢測
echo ===================================================
echo.
if exist "%~dp0python\python.exe" (
    "%~dp0python\python.exe" "%~dp0diagnose_system.py"
    goto :done
)
where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0diagnose_system.py"
    goto :done
)
where py >nul 2>&1
if %errorlevel% equ 0 (
    py -3 "%~dp0diagnose_system.py"
    goto :done
)
echo [ERROR] 找不到 Python 執行環境，無法執行自我檢測！
pause
exit /b 1
:done
echo.
echo 請按任意鍵退出...
pause >nul