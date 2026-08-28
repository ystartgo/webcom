@echo off
setlocal
title Webcom Offline Assets Downloader

cd /d "%~dp0"

echo ===================================================
echo   Webcom Offline Assets Downloader (離線資源下載器)
echo ===================================================

if exist "%~dp0python\python.exe" (
    "%~dp0python\python.exe" "%~dp0download_offline_assets.py"
    goto :done
)

where uv >nul 2>&1
if %errorlevel% equ 0 (
    uv run "%~dp0download_offline_assets.py"
    goto :done
)

where python >nul 2>&1
if %errorlevel% equ 0 (
    python "%~dp0download_offline_assets.py"
    goto :done
)

powershell -NoProfile -Command "& { New-Item -ItemType Directory -Force -Path '%~dp0assets' | Out-Null; Write-Host 'Downloading tailwindcss.js...'; Invoke-WebRequest -Uri 'https://cdn.tailwindcss.com' -OutFile '%~dp0assets\tailwindcss.js'; Write-Host 'Downloading lucide.min.js...'; Invoke-WebRequest -Uri 'https://unpkg.com/lucide@latest' -OutFile '%~dp0assets\lucide.min.js'; Write-Host 'Downloading marked.min.js...'; Invoke-WebRequest -Uri 'https://cdn.jsdelivr.net/npm/marked/marked.min.js' -OutFile '%~dp0assets\marked.min.js'; Write-Host 'All assets verified and ready!' }"

:done
echo.
echo [DONE] All offline assets are ready in '%~dp0assets\'!
pause
