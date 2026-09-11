@echo off
REM ============================================================
REM Webcom Daemon (Port 8001) - Windows Launcher
REM ============================================================
setlocal
cd /d "%~dp0"

REM 1. Auto-register webcom:// protocol in HKCU
reg query "HKCU\Software\Classes\webcom\shell\open\command" >nul 2>&1
if errorlevel 1 (
    reg add "HKCU\Software\Classes\webcom" /ve /d "URL:Webcom Daemon Launcher" /f >nul 2>&1
    reg add "HKCU\Software\Classes\webcom" /v "URL Protocol" /d "" /f >nul 2>&1
    reg add "HKCU\Software\Classes\webcom\shell\open\command" /ve /d "wscript.exe \"%~dp0silent_daemon.vbs\" \"%%1\"" /f >nul 2>&1
)

REM 2. Resolve Python interpreter (prioritize local embedded python)
set "PY="
set "PY_CMD="

if exist "%~dp0python\python.exe" (
    set "PY=%~dp0python\python.exe"
    goto :python_found
)

where uv >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=uv run --with fastapi --with uvicorn --with pydantic python"
    goto :python_found
)

for /f "delims=" %%i in ('where python 2^>nul') do (
    if not defined PY set "PY=%%i"
)
if defined PY goto :python_found

where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto :python_found
)

goto :python_missing

:python_missing
echo [%date% %time%] [ERROR] Python not found in %~dp0python or system PATH. >> "%~dp0daemon.log"
if "%1"=="__bg__" exit /b 1

echo ============================================================
echo  [ERROR] Python 3 is not installed or not in PATH!
echo ============================================================
echo  Webcom requires Python 3.10+ to run the background service.
echo.
echo  Options to resolve:
echo   1. Portable package: Ensure the 'python' folder exists:
echo      %~dp0python\
echo   2. Standard installation: Install Python from https://www.python.org
echo      (Make sure to check 'Add python.exe to PATH')
echo.
pause
exit /b 1

:python_found
REM 3. Ensure port 8001 is clean
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

REM 4. Run Daemon
if "%1"=="__bg__" goto :run_bg
if "%1"=="-s" goto :run_silent
if "%1"=="--silent" goto :run_silent

set "DISPLAY_PY=%PY%"
if not defined DISPLAY_PY set "DISPLAY_PY=%PY_CMD%"

echo ============================================================
echo  Webcom Daemon Launcher (Port 8001)
echo ============================================================
echo  [OK] Interpreter : %DISPLAY_PY%
echo  [OK] Protocol    : webcom:// registered
echo  [OK] Status      : Starting on http://127.0.0.1:8001 ...
echo  Press Ctrl+C to stop.
echo ============================================================
echo.

if defined PY_CMD (
    %PY_CMD% "%~dp0daemon.py"
) else (
    "%PY%" "%~dp0daemon.py"
)

if errorlevel 1 (
    echo.
    echo [ERROR] Daemon exited with code %ERRORLEVEL%.
    pause
)
exit /b %ERRORLEVEL%

:run_silent
start "" wscript.exe "%~dp0silent_daemon.vbs"
exit /b 0

:run_bg
if defined PY_CMD (
    %PY_CMD% "%~dp0daemon.py"
) else (
    "%PY%" "%~dp0daemon.py"
)
exit /b %ERRORLEVEL%
