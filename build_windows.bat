@echo off
REM Build script for Windows executable
REM This script creates a standalone .exe file that doesn't require Python

echo ========================================
echo Building pyTranscriber Windows Executable
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

echo [1/5] Checking Python version...
python --version

echo.
echo [2/5] Installing/updating build dependencies...
pip install --upgrade pip
pip install pyinstaller
pip install -r requirements.txt

echo.
echo [3/5] Checking for ffmpeg...
if exist ffmpeg.exe (
    echo Found ffmpeg.exe
) else (
    echo WARNING: ffmpeg.exe not found in project root
    echo The executable will be built but may not work without ffmpeg
    echo You can download ffmpeg from: https://ffmpeg.org/download.html
    echo Place ffmpeg.exe in the project root directory
    pause
)

echo.
echo [4/5] Building executable with PyInstaller...
pyinstaller build_windows_exe.spec --clean --noconfirm

if errorlevel 1 (
    echo.
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo [5/5] Build complete!
echo.
echo The executable is located at: dist\pyTranscriber.exe
echo.
echo You can now distribute this .exe file - it includes all dependencies
echo and does not require Python to be installed on the target machine.
echo.
pause


