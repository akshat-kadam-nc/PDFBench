@echo off
REM ── DeskewPDF launcher. Double-click this file. ────────────────────────────
setlocal
cd /d "%~dp0"

set VENV=.venv
set PY=%VENV%\Scripts\python.exe

if not exist "%PY%" (
  echo Creating virtual environment...
  python -m venv "%VENV%"
)

if not exist "%VENV%\.deps_installed" (
  echo Installing dependencies ^(first run only, please wait^)...
  "%PY%" -m pip install --quiet --disable-pip-version-check -r server\requirements.txt
  if errorlevel 1 (
    echo.
    echo Dependency installation failed. See messages above.
    pause
    exit /b 1
  )
  echo done > "%VENV%\.deps_installed"
)

echo Starting DeskewPDF at http://127.0.0.1:8765
start "" http://127.0.0.1:8765
"%PY%" -m uvicorn server.main:app --host 127.0.0.1 --port 8765

pause
