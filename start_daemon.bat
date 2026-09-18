@echo off
REM ============================================================
REM Webcom Daemon (Port 8001) - Windows Launcher
REM ============================================================
setlocal
cd /d "%~dp0"

chcp 65001 >nul 2>&1
set "PYTHONIOENCODING=utf-8"
set "PYTHONUTF8=1"

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
    set "PY_CMD=uv run --with fastapi --with uvicorn --with pydantic --with markitdown --with pyserial python"
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
echo [%date% %time%] [INFO] Python not found in %~dp0python or system PATH. Checking auto-install... >> "%~dp0daemon.log"
if "%1"=="__bg__" (
    powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%~dp0python.zip'; Expand-Archive -Path '%~dp0python.zip' -DestinationPath '%~dp0python' -Force; Remove-Item '%~dp0python.zip' -Force }" >nul 2>&1
    if exist "%~dp0python\python.exe" (
        set "PY=%~dp0python\python.exe"
        goto :python_found
    )
    exit /b 1
)

echo ============================================================
echo  [提示] 系統未在 PATH 或本地找到 Python 3
echo ============================================================
echo  Webcom 擴充功能預設可透過瀏覽器內建 Pyodide 執行 Python (免安裝)。
echo  若您欲啟用 Port 8001 主機常駐服務 (WSL/硬體/本機檔案存取)，
echo  系統正在透過 PowerShell 自動下載官方可攜版 Python 3 (~15MB)...
echo ============================================================
echo.
powershell -NoProfile -Command "& { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; Write-Host '正在下載官方 Python 3.11 輕量嵌入版...'; Invoke-WebRequest -Uri 'https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip' -OutFile '%~dp0python.zip'; Write-Host '正在解壓縮至 %~dp0python ...'; Expand-Archive -Path '%~dp0python.zip' -DestinationPath '%~dp0python' -Force; Remove-Item '%~dp0python.zip' -Force; Write-Host 'Python 可攜環境配置完成！' }"
if exist "%~dp0python\python.exe" (
    echo.
    echo  [OK] Python 3 可攜版已自動就緒！
    set "PY=%~dp0python\python.exe"
    goto :python_found
)

echo.
echo  自動下載失敗，請手動確認網路連線或至 https://www.python.org 下載安裝 Python。
pause
exit /b 1

:python_found
REM 3. Ensure ports 8001 and 8002 are clean
powershell -NoProfile -Command "Get-NetTCPConnection -LocalPort 8001,8002 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }" >nul 2>&1

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
echo [%date% %time%] [INFO] Launching Webcom Daemon on http://127.0.0.1:8001 ... >> "%~dp0daemon.log"
if defined PY_CMD (
    %PY_CMD% "%~dp0daemon.py" >> "%~dp0daemon.log" 2>&1
) else (
    "%PY%" "%~dp0daemon.py" >> "%~dp0daemon.log" 2>&1
)
if errorlevel 1 (
    echo [%date% %time%] [ERROR] Webcom Daemon process exited with code %ERRORLEVEL%. >> "%~dp0daemon.log"
)
exit /b %ERRORLEVEL%
