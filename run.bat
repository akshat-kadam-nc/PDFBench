@echo off
REM ── PDF Bench launcher. Double-click this file. ────────────────────────────
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

set PORT=8765

REM Free the port from any stale server left running from a previous launch,
REM so the browser can never end up talking to an old process.
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT%" ^| findstr LISTENING') do (
  echo Stopping stale server on port %PORT% ^(PID %%p^)...
  taskkill /F /PID %%p >nul 2>&1
)

echo Starting PDF Bench at http://127.0.0.1:%PORT%
start "" http://127.0.0.1:%PORT%
"%PY%" -m uvicorn server.main:app --host 127.0.0.1 --port %PORT%

pause
