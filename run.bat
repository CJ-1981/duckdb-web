@echo off
setlocal enabledelayedexpansion

:: CD to the repo directory (in case script is called from elsewhere)
cd /d "%~dp0"

echo Starting DuckDB Data Processor Services...

:: 0. Check for OneDrive/Cloud-Synced Paths
echo Checking environment...
set "CURRENT_DIR=%CD%"

set "ONEDRIVE_CHECK=!CURRENT_DIR:OneDrive=!"
set "SKYDRIVE_CHECK=!CURRENT_DIR:SkyDrive=!"
if not "!ONEDRIVE_CHECK!"=="!CURRENT_DIR!" (
    echo WARNING: Running from OneDrive path!
    echo This may cause issues with virtual environments and file locking.
    echo/
    echo If you encounter problems, consider moving to:
    echo   - C:\dev\duckdb-web
    echo   - %USERPROFILE%\projects\duckdb-web
    echo/
)

set "DROPBOX_CHECK=!CURRENT_DIR:Dropbox=!"
set "GOOGLE_CHECK=!CURRENT_DIR:Google Drive=!"
set "ICLOUD_CHECK=!CURRENT_DIR:iCloudDrive=!"
if not "!DROPBOX_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"
if not "!GOOGLE_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"
if not "!ICLOUD_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"

if defined CLOUD_FOUND (
    echo WARNING: Running from cloud-synced path!
    echo File synchronization may interfere with development.
    echo/
)

:: 1. Start Backend (FastAPI)
echo Starting Backend (FastAPI)...

if defined VENV_DIR (
    set "VENV_PATH=!VENV_DIR!"
    echo Using custom virtual environment: !VENV_PATH!
) else (
    set "VENV_PATH=.venv"
)

set "ACTIVATE_SCRIPT=!VENV_PATH!\Scripts\activate.bat"

if exist "!ACTIVATE_SCRIPT!" (
    echo Starting backend with virtual environment...
    start /b cmd /c "cd /d ""%cd%"" && call ""!ACTIVATE_SCRIPT!"" && python -m uvicorn src.api.main:create_app --factory --reload --port 8000"
) else (
    echo Virtual environment not found at !ACTIVATE_SCRIPT!
    echo Falling back to system Python...
    start /b cmd /c "cd /d ""%cd%"" && python -m uvicorn src.api.main:create_app --factory --reload --port 8000"
)

:: 2. Wait a moment for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

:: 3. Start Frontend (Next.js)
echo Starting Frontend (Next.js)...

if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

if defined PORT (
    set "valid_port=1"
    for /f "delims=0123456789" %%a in ("!PORT!") do set "valid_port=0"
    if "!valid_port!"=="1" (
        if !PORT! lss 1 set "valid_port=0"
        if !PORT! gtr 65535 set "valid_port=0"
    )
    
    if "!valid_port!"=="1" (
        call npm run dev -- -p !PORT!
    ) else (
        echo Warning: PORT !PORT! is invalid. Using default port 3000.
        call npm run dev -- -p 3000
    )
) else (
    call npm run dev -- -p 3000
)

if not defined CI (
    pause
)
