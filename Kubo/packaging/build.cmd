@echo off
setlocal
cd /d "%~dp0"
echo ===================================================
echo     Nagisa Kubo Packaging - Build Automation
echo ===================================================
call "..\app\.venv\Scripts\python.exe" build.py
if errorlevel 1 (
    echo [ERROR] Build failed with error level %errorlevel%!
    pause
    exit /b %errorlevel%
)
echo [SUCCESS] Build completed! Output in Kubo\release\Kubo\
pause
