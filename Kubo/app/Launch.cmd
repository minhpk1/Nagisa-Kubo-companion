@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo First launch: preparing the Python environment...
  py -3 -m venv .venv
  if errorlevel 1 goto fail
)
if not exist ".venv\installed.ok" (
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 goto fail
  echo ready>".venv\installed.ok"
)
start "" ".venv\Scripts\pythonw.exe" "%~dp0start_kubo.pyw" %*
exit /b 0
:fail
echo.
echo Setup or launch failed. Install Python 3.11 or newer from python.org,
echo then try again. See README.md for manual setup and troubleshooting.
pause
exit /b 1
