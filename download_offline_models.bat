@echo off
setlocal
title Webcom - Download Offline WebLLM Models
cd /d "%~dp0"

echo ========================================================
echo   Webcom WebLLM Offline Model Downloader
echo ========================================================
echo Target model: Qwen2.5-0.5B-Instruct-q4f16_1-MLC (~350MB)
echo Files will be saved into: %~dp0models\
echo.

if exist "%~dp0python\python.exe" (
    "%~dp0python\python.exe" "%~dp0download_offline_models.py"
    goto :done
)

where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv run "%~dp0download_offline_models.py"
    goto :done
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0download_offline_models.py"
    goto :done
)

echo [ERROR] Python not found.
pause
exit /b 1

:done
echo.
echo ========================================================
echo   Download Finished! You can now use WebGPU offline.
echo ========================================================
pause
