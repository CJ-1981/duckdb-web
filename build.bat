@echo off
setlocal

echo ====================================================
echo 🛠️  Data Analyst Web - Windows Build Script
echo ====================================================

:: 1. Check for Node.js
where npm >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: npm is not installed. Please install Node.js.
    exit /b 1
)

:: 2. Check for Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Error: python is not installed.
    exit /b 1
)

:: 3. Build Frontend
echo [1/4] 💻 Building Frontend (Next.js Static Export)...
if not exist node_modules (
    echo Installing frontend dependencies...
    call npm install
)
call npm run build
if %errorlevel% neq 0 (
    echo ❌ Error: Frontend build failed.
    exit /b 1
)

:: 4. Install Python Dependencies
echo [2/4] 📦 Installing Python dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

:: 5. Prepare PyInstaller
echo [3/4] 🚀 Packaging application with PyInstaller...

:: We use --onedir for faster startup. 
:: We add the 'out' directory which contains the static frontend.
:: We include uvicorn hidden imports which are often missed by PyInstaller.

pyinstaller --name "data-analyst-web" ^
            --onedir ^
            --clean ^
            --add-data "out;out" ^
            --add-data "fonts;fonts" ^
            --hidden-import uvicorn.logging ^
            --hidden-import uvicorn.loops ^
            --hidden-import uvicorn.loops.auto ^
            --hidden-import uvicorn.protocols ^
            --hidden-import uvicorn.protocols.http ^
            --hidden-import uvicorn.protocols.http.auto ^
            --hidden-import uvicorn.protocols.websockets ^
            --hidden-import uvicorn.protocols.websockets.auto ^
            --hidden-import uvicorn.lifespan ^
            --hidden-import uvicorn.lifespan.on ^
            --paths . ^
            src/api/main.py

if %errorlevel% neq 0 (
    echo ❌ Error: PyInstaller packaging failed.
    exit /b 1
)

:: 6. Success
echo ====================================================
echo ✅ Build complete! 
echo 📂 Executable location: dist\data-analyst-web\data-analyst-web.exe
echo 💡 Note: Make sure to copy config.yaml to the same folder if needed.
echo ====================================================
pause
