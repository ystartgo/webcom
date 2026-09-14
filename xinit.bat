@echo off
if "%~1"=="" (
    wsl.exe -e bash -c "xinit"
) else (
    wsl.exe -e bash -c "xinit %*"
)
