@echo off
setlocal enabledelayedexpansion

echo 🚀 Starting DuckDB Data Processor Services...

:: 1. Start Backend (FastAPI)
echo 📦 Starting Backend (FastAPI)...

if exist .venv\Scripts\activate.bat (
    start /b cmd /c ".venv\Scripts\activate.bat && uvicorn src.api.main:create_app --factory --reload --port 8000"
) else (
    start /b uvicorn src.api.main:create_app --factory --reload --port 8000
)

:: 2. Wait a moment for backend to initialize
timeout /t 5 /nobreak > nul

:: 3. Start Frontend (Next.js)
echo 💻 Starting Frontend (Next.js)...

:: Check if node_modules exists, if not install dependencies
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

:: Use PORT environment variable if provided, else default to 3000
if defined PORT (
    call npm run dev -- -p !PORT!
) else (
    call npm run dev -- -p 3000
)

:: Cleanup is tricky in batch, but usually closing terminal kills children
if not defined CI (
    pause
)
