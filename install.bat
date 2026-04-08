@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting DuckDB Web Suite Installation (Windows)...

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
if exist .venv (
    echo ℹ️  Existing .venv found. Checking for updates...
) else (
    !PYTHON_CMD! -m venv .venv
    if %ERRORLEVEL% neq 0 (
        echo ❌ Failed to create virtual environment.
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created.
)

:: 4. Install Python Dependencies
echo 📦 Installing Backend dependencies...
if exist .venv\Scripts\activate.bat (
    call .venv\Scripts\activate.bat || exit /b 1
    python -m pip install --upgrade pip || exit /b 1
    if exist requirements.txt (
        pip install -r requirements.txt || exit /b 1
    ) else (
        echo ⚠️  requirements.txt not found. Skipping...
    )
    if exist requirements-dev.txt (
        echo 📦 Installing dev dependencies...
        pip install -r requirements-dev.txt || exit /b 1
    )
) else (
    echo ❌ .venv activation script not found.
    pause
    exit /b 1
)
echo ✅ Backend dependencies installed.

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
