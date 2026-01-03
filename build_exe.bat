@echo off
echo ==================================================
echo   SHRINKIFY - STANDALONE BUILD SCRIPT
echo ==================================================

REM 1. Activate Virtual Environment
if not exist "venv\Scripts\activate" (
    echo [ERR] Virtual environment not found. Please create it first.
    pause
    exit /b
)
call venv\Scripts\activate

REM 2. Ensure application is closed (prevent PermissionError)
echo [PRE-BUILD] Closing any running instances of Shrinkify...
taskkill /F /IM "Shrinkify.exe" /T >nul 2>&1

REM 3. Install PyInstaller
echo [INIT] Ensuring PyInstaller is installed...
pip install pyinstaller pillow

REM 3. Run PyInstaller
echo [BUILD] Starting PyInstaller build...
echo [INFO] Building with --onedir to keep all files visible.
pyinstaller --noconfirm --onedir --windowed ^
    --name "Shrinkify" ^
    --icon "logo.ico" ^
    --add-data "logo.ico;." ^
    --add-data "optimizer_config.json;." ^
    "Production-Ready-ts-darkMode.py"

echo [POST-BUILD] Copying engine folder to dist...
xcopy /S /I /Y "engine" "dist\Shrinkify\engine"

echo ==================================================
echo   BUILD COMPLETE
echo   Output location: dist\Shrinkify
echo ==================================================
echo NOTE: Standalone EXE is now ready for testing in dist\Shrinkify.
echo DLLs and the 'engine' folder are visible as requested.
echo ==================================================
pause
