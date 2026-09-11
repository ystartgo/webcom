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
    set "PY_CMD=uv run --with fastapi --with uvicorn --with pydantic --with markitdown[all] python"
    goto :python_found
)

where python >nul 2>&1
if not errorlevel 1 (
    set "PY=python"
    goto :python_found
)

where py >nul 2>&1
if not errorlevel 1 (
    set "PY_CMD=py -3"
    goto :python_found
)

REM Check common Python installation paths if not in system PATH
for %%P in (
    "%LocalAppData%\Programs\Python\Python313\python.exe"
    "%LocalAppData%\Programs\Python\Python312\python.exe"
    "%LocalAppData%\Programs\Python\Python311\python.exe"
    "%LocalAppData%\Programs\Python\Python310\python.exe"
    "%ProgramFiles%\Python313\python.exe"
    "%ProgramFiles%\Python312\python.exe"
    "%ProgramFiles%\Python311\python.exe"
    "%ProgramFiles%\Python310\python.exe"
    "%SystemDrive%\Python312\python.exe"
    "%SystemDrive%\Python311\python.exe"
    "%SystemDrive%\Python310\python.exe"
    "%UserProfile%\miniconda3\python.exe"
    "%UserProfile%\anaconda3\python.exe"
) do (
    if exist %%P (
        if not defined PY set "PY=%%~fP"
    )
)
if defined PY goto :python_found

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
if defined PY (
    "%PY%" -c "import fastapi, markitdown" >nul 2>&1
    if errorlevel 1 (
        echo [INFO] 偵測到尚未安裝完整依賴，正在自動從 requirements.txt 安裝...
        "%PY%" -m pip install -r "%~dp0requirements.txt"
    )
)

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
