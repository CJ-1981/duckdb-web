@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting DuckDB Web Suite Installation (Windows)...

:: 0. Check for OneDrive/Cloud-Synced Paths
echo 🔎 Checking environment...
set "SAFE_ENV=1"
set "CURRENT_DIR=%CD%"

:: Check for OneDrive paths
echo %CURRENT_DIR% | findstr /C:"OneDrive" /C:"SkyDrive" >nul
if %ERRORLEVEL% equ 0 (
    echo ⚠️  WARNING: Detected OneDrive/SkyDrive path!
    echo OneDrive synchronization can cause issues with virtual environments and node_modules.
    echo.
    echo Recommended: Clone repository to a non-synced location like:
    echo   - C:\dev\duckdb-web
    echo   - %USERPROFILE%\projects\duckdb-web
    echo.
    set "SAFE_ENV=0"
)

:: Check for other cloud storage paths (Dropbox, Google Drive, etc.)
echo %CURRENT_DIR% | findstr /C:"Dropbox" /C:"Google Drive" /C:"iCloudDrive" >nul
if %ERRORLEVEL% equ 0 (
    echo ⚠️  WARNING: Detected cloud-synced path!
    echo Cloud synchronization can cause issues with virtual environments and node_modules.
    echo.
    echo Recommended: Clone repository to a local directory.
    echo.
    set "SAFE_ENV=0"
)

if "!SAFE_ENV!"=="0" (
    echo Press Ctrl+C to cancel and move to a safe location,
    echo or press any key to continue anyway (not recommended).
    pause >nul
)

:: 1. Check for Node.js
echo 🔎 Checking for Node.js...
where node >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ❌ Node.js is not installed. Please download it from https://nodejs.org/
    pause
    exit /b 1
)
echo ✅ Node.js found.

:: 2. Check for Python
echo 🔎 Checking for Python...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo 🔎 Checking for python3...
    where python3 >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo ❌ Python is not installed. Please download it from https://python.org/
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python3
    )
) else (
    set PYTHON_CMD=python
)
echo ✅ Python found (!PYTHON_CMD!).

:: 3. Setup Virtual Environment
echo 📦 Creating Python Virtual Environment (.venv)...

:: Allow custom VENV location via environment variable
if defined VENV_DIR (
    set "VENV_PATH=!VENV_DIR!"
    echo Using custom virtual environment location: !VENV_PATH!
) else (
    set "VENV_PATH=.venv"
)

if exist "!VENV_PATH!" (
    echo ℹ️  Existing virtual environment found at !VENV_PATH!. Checking for updates...
) else (
    echo Creating virtual environment at: !VENV_PATH!

    :: For OneDrive paths, suggest using USERPROFILE location
    if "!SAFE_ENV!"=="0" (
        if not defined VENV_DIR (
            echo.
            echo 💡 Suggestion: Create virtual environment in your user profile:
            echo   !PYTHON_CMD! -m venv %USERPROFILE%\.venvs\duckdb-web
            echo   set VENV_DIR=%USERPROFILE%\.venvs\duckdb-web
            echo.
        )
    )

    !PYTHON_CMD! -m venv "!VENV_PATH!"
    if %ERRORLEVEL% neq 0 (
        echo ❌ Failed to create virtual environment at !VENV_PATH!.
        echo.
        echo Try creating it manually:
        echo   !PYTHON_CMD! -m venv %USERPROFILE%\.venvs\duckdb-web
        echo   set VENV_DIR=%USERPROFILE%\.venvs\duckdb-web
        echo   !VENV_PATH!\Scripts\activate
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created successfully.
)

:: 4. Install Python Dependencies
echo 📦 Installing Backend dependencies...

:: Construct activation script path based on VENV_PATH
if "!VENV_PATH!"==".venv" (
    set "ACTIVATE_SCRIPT=!VENV_PATH!\Scripts\activate.bat"
) else (
    set "ACTIVATE_SCRIPT=!VENV_PATH!\Scripts\activate.bat"
)

if exist "!ACTIVATE_SCRIPT!" (
    call "!ACTIVATE_SCRIPT!" || (
        echo ❌ Failed to activate virtual environment at !ACTIVATE_SCRIPT!
        pause
        exit /b 1
    )

    echo Upgrading pip...
    python -m pip install --upgrade pip --quiet || exit /b 1

    if exist requirements.txt (
        echo Installing from requirements.txt...
        pip install -r requirements.txt || exit /b 1
    ) else (
        echo ⚠️  requirements.txt not found. Skipping...
    )

    if exist requirements-dev.txt (
        echo 📦 Installing dev dependencies...
        pip install -r requirements-dev.txt || exit /b 1
    )

    echo ✅ Backend dependencies installed successfully.
) else (
    echo ❌ Virtual environment activation script not found: !ACTIVATE_SCRIPT!
    echo Expected location: !ACTIVATE_SCRIPT!
    echo.
    echo Virtual environment path: !VENV_PATH!
    pause
    exit /b 1
)

:: 5. Install Frontend Dependencies
echo 📦 Installing Frontend dependencies (npm)...
if exist package.json (
    call npm install || exit /b 1
) else (
    echo ⚠️  package.json not found. Skipping...
)
echo ✅ Frontend dependencies installed.

echo.
echo ✨ Installation Complete! ✨
echo You can now run the application using: run.bat
echo.
pause
