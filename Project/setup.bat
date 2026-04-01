@echo off
echo Installing Sidekick Communicator Dependencies...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found. Installing dependencies...

REM Install required packages
pip install textual playwright aiohttp pysnmp pythonping

if errorlevel 1 (
    echo ERROR: Failed to install Python packages
    pause
    exit /b 1
)

echo Installing Firefox browser for Playwright...
set PLAYWRIGHT_BROWSERS_PATH=0
python -m playwright install firefox

if errorlevel 1 (
    echo ERROR: Failed to install Firefox browser
    pause
    exit /b 1
)

echo.
echo All dependencies installed successfully.
echo You can now run Sidekick Communicator.
echo.
pause
