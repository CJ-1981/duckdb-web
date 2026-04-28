@echo off
setlocal enabledelayedexpansion

echo Starting DuckDB Web Suite Installation (Windows)...

:: 0. Check for OneDrive/Cloud-Synced Paths
echo Checking environment...
set "SAFE_ENV=1"
set "CURRENT_DIR=%CD%"

:: Check for OneDrive paths
set "ONEDRIVE_CHECK=!CURRENT_DIR:OneDrive=!"
set "SKYDRIVE_CHECK=!CURRENT_DIR:SkyDrive=!"
if not "!ONEDRIVE_CHECK!"=="!CURRENT_DIR!" set "SAFE_ENV=0"
if not "!SKYDRIVE_CHECK!"=="!CURRENT_DIR!" set "SAFE_ENV=0"

if not "!SAFE_ENV!"=="0" goto :SKIP_ONEDRIVE_WARNING
    echo WARNING: Detected OneDrive/SkyDrive path!
    echo OneDrive synchronization can cause issues with virtual environments and node_modules.
    echo/
    echo Recommended: Clone repository to a non-synced location like:
    echo   - C:\dev\duckdb-web
    echo   - %USERPROFILE%\projects\duckdb-web
    echo/
:SKIP_ONEDRIVE_WARNING

:: Check for other cloud storage paths (Dropbox, Google Drive, etc.)
set "DROPBOX_CHECK=!CURRENT_DIR:Dropbox=!"
set "GOOGLE_CHECK=!CURRENT_DIR:Google Drive=!"
set "ICLOUD_CHECK=!CURRENT_DIR:iCloudDrive=!"
set "CLOUD_FOUND=0"
if not "!DROPBOX_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"
if not "!GOOGLE_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"
if not "!ICLOUD_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"

if not "!CLOUD_FOUND!"=="1" goto :SKIP_CLOUD_WARNING
    echo WARNING: Detected cloud-synced path!
    echo Cloud synchronization can cause issues with virtual environments and node_modules.
    echo/
    echo Recommended: Clone repository to a local directory.
    echo/
    set "SAFE_ENV=0"
:SKIP_CLOUD_WARNING

if not "!SAFE_ENV!"=="0" goto :SKIP_PAUSE
    echo Press Ctrl+C to cancel and move to a safe location,
    echo or press any key to continue anyway (not recommended).
    pause >nul
:SKIP_PAUSE

:: 1. Check for Node.js
echo Checking for Node.js...
where node >nul 2>&1
if !ERRORLEVEL! neq 0 (
    echo Node.js is not installed. Please download it from https://nodejs.org/
    pause
    exit /b 1
)
echo Node.js found.

:: 2. Check for Python
echo Checking for Python...
where python >nul 2>&1
if !ERRORLEVEL! equ 0 (
    set "PYTHON_CMD=python"
) else (
    where python3 >nul 2>&1
    if !ERRORLEVEL! equ 0 (
        set "PYTHON_CMD=python3"
    ) else (
        echo Python is not installed. Please download it from https://python.org/
        pause
        exit /b 1
    )
)
echo Python found (!PYTHON_CMD!).

:: 3. Setup Virtual Environment
echo Creating Python Virtual Environment (.venv)...

if defined VENV_DIR (
    set "VENV_PATH=!VENV_DIR!"
    echo Using custom virtual environment location: !VENV_PATH!
) else (
    set "VENV_PATH=.venv"
)

if exist "!VENV_PATH!" (
    echo Existing virtual environment found at !VENV_PATH!. Checking for updates...
) else (
    echo Creating virtual environment at: !VENV_PATH!

    if "!SAFE_ENV!"=="0" (
        if not defined VENV_DIR (
            echo/
            echo Suggestion: Create virtual environment in your user profile:
            echo   !PYTHON_CMD! -m venv %USERPROFILE%\.venvs\duckdb-web
            echo   set VENV_DIR=%USERPROFILE%\.venvs\duckdb-web
            echo/
        )
    )

    !PYTHON_CMD! -m venv "!VENV_PATH!"
    if !ERRORLEVEL! neq 0 (
        echo Failed to create virtual environment at !VENV_PATH!.
        echo/
        echo Try creating it manually:
        echo   !PYTHON_CMD! -m venv %USERPROFILE%\.venvs\duckdb-web
        echo   set VENV_DIR=%USERPROFILE%\.venvs\duckdb-web
        echo   !VENV_PATH!\Scripts\activate
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
)

:: 4. Install Python Dependencies
echo Installing Backend dependencies...

set "ACTIVATE_SCRIPT=!VENV_PATH!\Scripts\activate.bat"

if not exist "!ACTIVATE_SCRIPT!" (
    echo Virtual environment activation script not found: !ACTIVATE_SCRIPT!
    echo Expected location: !ACTIVATE_SCRIPT!
    echo/
    echo Virtual environment path: !VENV_PATH!
    pause
    exit /b 1
)

call "!ACTIVATE_SCRIPT!"
if !ERRORLEVEL! neq 0 (
    echo Error: Failed to activate virtual environment at !ACTIVATE_SCRIPT!
    pause
    exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip --quiet

if exist requirements.txt (
    echo Installing from requirements.txt...
    pip install -r requirements.txt
) else (
    echo requirements.txt not found. Skipping...
)

echo Note: For SQL Server support, ensure you have the Microsoft ODBC Driver installed.

if exist requirements-dev.txt (
    echo Installing dev dependencies...
    pip install -r requirements-dev.txt
)

echo Backend dependencies installed successfully.

:: 5. Install Frontend Dependencies
echo Installing Frontend dependencies (npm)...
if exist package.json (
    call npm install
) else (
    echo package.json not found. Skipping...
)
echo Frontend dependencies installed.

echo/
echo Installation Complete!
echo You can now run the application using: run.bat
echo/
pause
