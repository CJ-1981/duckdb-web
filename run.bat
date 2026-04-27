@echo off
setlocal enabledelayedexpansion

:: CD to the repo directory (in case script is called from elsewhere)
cd /d "%~dp0"

echo Starting DuckDB Data Processor Suite...

:: 0. Check for existing processes
:: echo Checking for existing processes...
:: taskkill /F /FI "IMAGENAME eq python.exe" /FI "WINDOWTITLE eq uvicorn*" /T >nul 2>&1
:: taskkill /F /FI "IMAGENAME eq node.exe" /FI "WINDOWTITLE eq next*" /T >nul 2>&1

:: Initialize cleanup variables
set "CLEANUP_DONE=0"

:: 1. Check for OneDrive/Cloud-Synced Paths
echo Checking environment...
set "CURRENT_DIR=%CD%"

set "ONEDRIVE_CHECK=!CURRENT_DIR:OneDrive=!"
set "SKYDRIVE_CHECK=!CURRENT_DIR:SkyDrive=!"
if not "!ONEDRIVE_CHECK!"=="!CURRENT_DIR!" (
    echo WARNING: Running from OneDrive path!
    echo This may cause issues with virtual environments and file locking.
    echo/
)

set "DROPBOX_CHECK=!CURRENT_DIR:Dropbox=!"
set "GOOGLE_CHECK=!CURRENT_DIR:Google Drive=!"
set "ICLOUD_CHECK=!CURRENT_DIR:iCloudDrive=!"
set "CLOUD_FOUND=0"
if not "!DROPBOX_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"
if not "!GOOGLE_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"
if not "!ICLOUD_CHECK!"=="!CURRENT_DIR!" set "CLOUD_FOUND=1"

if "!CLOUD_FOUND!"=="1" (
    echo WARNING: Running from cloud-synced path!
    echo File synchronization may interfere with development.
    echo/
)

:: 2. Ensure node_modules exists
echo Checking frontend dependencies...
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install --no-bin-links
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        pause
        exit /b 1
    )
)

:: 3. Start Backend (FastAPI)
echo Starting Backend (FastAPI)...

if defined VENV_DIR (
    set "VENV_PATH=!VENV_DIR!"
) else (
    set "VENV_PATH=.venv"
)

set "ACTIVATE_SCRIPT=!VENV_PATH!\Scripts\activate.bat"

:: Set environment variables for development mode
set "APP_NO_BROWSER=true"
set "PYTHONUNBUFFERED=1"

if exist "!ACTIVATE_SCRIPT!" (
    echo Starting backend with virtual environment...
    start "uvicorn-backend" /b cmd /c "call ""!ACTIVATE_SCRIPT!"" && python -m uvicorn src.api.main:create_app --factory --port 8000"
) else (
    echo Virtual environment not found at !ACTIVATE_SCRIPT!
    echo Falling back to system Python...
    start "uvicorn-backend" /b cmd /c "python -m uvicorn src.api.main:create_app --factory --port 8000"
)

:: 4. Wait for backend to initialize
echo Waiting for backend to start (8000)...
timeout /t 2 /nobreak > nul

:: 5. Start Frontend (Next.js)
echo Starting Frontend (Next.js)...

:: Smart port detection
if not defined PORT (
    echo Detecting available port...
    set "PORT=3000"
    
    for %%p in (3000 3001 3002 3003) do (
        :: Use netstat -an to avoid slow DNS lookups
        netstat -an | findstr /C:":%%p " >nul 2>&1
        if errorlevel 1 (
            echo   ✅ Port %%p is available
            set "PORT=%%p"
            goto :port_found
        ) else (
            echo   ❌ Port %%p is in use
        )
    )
    
    echo   ❌ All ports 3000-3003 are in use!
    goto :cleanup
)

:port_found
echo 🎯 Using port !PORT!

:: Launch browser for the frontend in the background
echo 🚀 Opening http://localhost:!PORT! in your browser...
start http://localhost:!PORT!

:: Start frontend (this will block until exit)
echo Starting Next.js...
set "PORT=!PORT!"
call npm run dev

:: 6. Cleanup on exit
:cleanup
if "!CLEANUP_DONE!"=="1" exit /b
set "CLEANUP_DONE=1"

echo.
echo Cleaning up background processes...
:: Kill the backend specifically using the window title
taskkill /F /FI "WINDOWTITLE eq uvicorn-backend" /T >nul 2>&1
:: Also kill any orphaned python processes from this session
taskkill /F /IM python.exe /FI "WINDOWTITLE eq uvicorn-backend" /T >nul 2>&1

if not defined CI (
    echo Application stopped.
    pause
)
exit /b

