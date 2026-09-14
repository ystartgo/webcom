@echo off
if "%~1"=="" (
    wsl.exe -e bash -c "startx"
) else (
    wsl.exe -e bash -c "startx %*"
)
