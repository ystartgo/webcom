@echo off
setlocal
chcp 65001 >nul
title Webcom Dependencies Installer (依賴安裝工具)
cd /d "%~dp0"
echo ===================================================
echo   Webcom AI 控制台 — Python 核心相依套件一鍵安裝
echo ===================================================
echo.

set "PY="
if exist "%~dp0python\python.exe" (
    "%~dp0python\python.exe" -m pip --version >nul 2>&1
    if not errorlevel 1 (
        set "PY=%~dp0python\python.exe"
        goto :run_install
    )
)

where uv >nul 2>&1
if not errorlevel 1 (
    echo [INFO] 偵測到 uv 套件管理器，正在透過 uv 快速安裝...
    if exist "%~dp0python\python.exe" (
        uv pip install --target="%~dp0python\Lib\site-packages" -r "%~dp0requirements.txt"
    ) else (
        uv pip install --system -r "%~dp0requirements.txt"
    )
    if not errorlevel 1 goto :done
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto :run_install
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY=py -3"
    goto :run_install
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
if defined PY goto :run_install

echo [ERROR] 找不到可用於安裝依賴的 Python 執行環境，請先安裝 Python 3.10+！
pause
exit /b 1

:run_install
echo [INFO] 使用解譯器: %PY%
if exist "%~dp0python\python.exe" (
    "%PY%" -m pip install --target="%~dp0python\Lib\site-packages" -r "%~dp0requirements.txt"
) else (
    "%PY%" -m pip install -r "%~dp0requirements.txt"
)

:done
echo.
echo ===================================================
echo   所有核心依賴安裝完成！請重新執行自我檢測。
echo ===================================================
pause
