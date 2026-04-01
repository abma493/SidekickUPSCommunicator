@echo off
echo Building SidekickCommunicator...
echo.

REM Build outside OneDrive to avoid file-locking issues during sync
set DIST_PATH=C:\SidekickBuild\dist
set WORK_PATH=C:\SidekickBuild\work

REM Install PyInstaller if not present
pip install pyinstaller >nul 2>&1

REM Clean previous work/dist outside OneDrive
if exist "%WORK_PATH%" rmdir /s /q "%WORK_PATH%"
if exist "%DIST_PATH%" rmdir /s /q "%DIST_PATH%"

REM Run build
pyinstaller SidekickCommunicator.spec --noconfirm --distpath "%DIST_PATH%" --workpath "%WORK_PATH%"

if errorlevel 1 (
    echo ERROR: Build failed.
    pause
    exit /b 1
)

echo.
echo Build complete. Output is in %DIST_PATH%\SidekickCommunicator\
echo Run %DIST_PATH%\SidekickCommunicator\SidekickCommunicator.exe
echo.
pause
