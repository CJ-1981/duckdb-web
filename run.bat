@echo off
setlocal enabledelayedexpansion

:: CD to the repo directory (in case script is called from elsewhere)
cd /d "%~dp0"

:: Kill any existing processes from previous runs
echo Checking for existing processes...
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe" ^| findstr "uvicorn"') do (
    echo Killing existing Python process: %%a
    taskkill /F /PID %%a 2>nul
)

for /f "tokens=2" %%a in ('tasklist /fi "imagename eq node.exe" /fo csv ^| find "node.exe" ^| findstr "next"') do (
    echo Killing existing Node process: %%a
    taskkill /F /PID %%a 2>nul
)

:: Cleanup function to kill background processes on exit
set "BACKEND_PID="
set "CLEANUP_DONE=0"

:cleanup
if "!CLEANUP_DONE!"=="1" goto :EOF
set "CLEANUP_DONE=1"

echo.
echo Cleaning up background processes...

:: Kill uvicorn processes
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    taskkill /F /PID %%a 2>nul
)

:: Kill any node processes started by this script
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq node.exe" /fo csv ^| find "node.exe"') do (
    taskkill /F /PID %%a 2>nul
)

goto :EOF

:: Set up cleanup on script exit (Ctrl+C, errors, etc.)
if not defined CLEANUP_SETUP (
    set "CLEANUP_SETUP=1"
    set "ERRORHANDLING="
    :: Trap Ctrl+C
    for /f "delims=" %%a in ('echo prompt $E ^| cmd') do set "ESC=%%a"
    echo !ESC![?25l
    call :setup_ctrlc_handler
)

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

:: 0.5. Ensure node_modules exists BEFORE starting services
echo Checking frontend dependencies...
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install frontend dependencies
        goto :cleanup
    )
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
    start /b "" cmd /c "cd /d ""%cd%"" && call ""!ACTIVATE_SCRIPT!"" && python -m uvicorn src.api.main:create_app --factory --port 8000 2>&1"
) else (
    echo Virtual environment not found at !ACTIVATE_SCRIPT!
    echo Falling back to system Python...
    start /b "" cmd /c "cd /d ""%cd%"" && python -m uvicorn src.api.main:create_app --factory --port 8000 2>&1"
)

:: Store backend process ID for cleanup
for /f "tokens=2" %%a in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe" ^| find /v "0"') do (
    set "BACKEND_PID=%%a"
    goto :backend_found
)
:backend_found

:: 2. Wait a moment for backend to initialize
echo Waiting for backend to initialize...
timeout /t 5 /nobreak > nul

:: 3. Start Frontend (Next.js)
echo Starting Frontend (Next.js)...

:: Smart port detection if PORT not already set
if not defined PORT (
    echo Detecting available port...

    :: Try ports in sequence: 3000, 3001, 3002, 3003
    for %%p in (3000 3001 3002 3003) do (
        echo   Checking port %%p...
        netstat >nul 2>&1
        if errorlevel 1 (
            :: netstat not available, assume port is free
            echo   ✅ Port %%p is available^(netstat not available^)
            set "PORT=%%p"
            goto :port_found
        ) else (
            netstat -an ^| findstr ":%%p " >nul 2>&1
            if errorlevel 1 (
                :: Port not in use
                echo   ✅ Port %%p is available!
                set "PORT=%%p"
                goto :port_found
            ) else (
                :: Port is in use
                echo   ❌ Port %%p is in use
            )
        )
    )

    :: No port found
    echo   ❌ All ports 3000-3003 are in use!
    echo Please free up a port and try again.
    goto :cleanup

    :port_found
    echo 🎯 Using port !PORT!
)

:: Validate and use PORT
if defined PORT (
    set "valid_port=1"
    for /f "delims=0123456789" %%a in ("!PORT!") do set "valid_port=0"
    if "!valid_port!"=="1" (
        if !PORT! lss 1 set "valid_port=0"
        if !PORT! gtr 65535 set "valid_port=0"
    )

    if "!valid_port!"=="1" (
        echo Starting on port !PORT!...
        call npm run dev -- -p !PORT!
    ) else (
        echo Warning: PORT !PORT! is invalid. Using default port 3000.
        call npm run dev -- -p 3000
    )
) else (
    echo Starting on default port 3000...
    call npm run dev -- -p 3000
)

:: Clean up when npm run dev exits
call :cleanup

if not defined CI (
    pause
)

goto :EOF

:: Ctrl+C handler setup
:setup_ctrlc_handler
:: Windows doesn't have a simple trap command like Unix
:: We rely on the :cleanup function being called on exit
goto :EOF
