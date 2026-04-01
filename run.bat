@echo off
setlocal

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
cd frontend

:: Check if node_modules exists, if not install dependencies
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)

call npm run dev

:: Cleanup is tricky in batch, but usually closing terminal kills children
pause
