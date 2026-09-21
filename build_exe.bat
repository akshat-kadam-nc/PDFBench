@echo off
REM Build the standalone PDFBench.exe (Windows). Output: dist\PDFBench.exe
setlocal
cd /d "%~dp0"

set PY=.venv\Scripts\python.exe
if not exist "%PY%" (
  echo Run run.bat once first to create the .venv, then re-run this.
  pause & exit /b 1
)

"%PY%" -m pip install --quiet --disable-pip-version-check pyinstaller

"%PY%" -m PyInstaller --onefile --windowed --name PDFBench ^
  --icon "assets\PDFBench.ico" ^
  --add-data "web;web" ^
  --collect-all skimage ^
  --collect-all scipy ^
  --collect-all pymupdf ^
  --collect-all deskew ^
  --collect-all webview ^
  --collect-submodules uvicorn ^
  --collect-submodules fastapi ^
  --hidden-import clr ^
  --noconfirm --clean desktop.py

echo.
echo Done. Share dist\PDFBench.exe
pause
