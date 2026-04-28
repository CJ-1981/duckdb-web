#!/bin/bash

# Exit script on any error
set -e

echo "Starting DuckDB Web Suite Installation..."

# 1. Check for Node.js
if ! command -v node &> /dev/null; then
    echo "Node.js is not installed. Please download it from https://nodejs.org/"
    exit 1
fi
echo "Node.js found."

# 2. Check for Python
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
elif command -v python &> /dev/null; then
    PYTHON_CMD="python"
else
    echo "Python is not installed. Please download it from https://python.org/"
    exit 1
fi
echo "Python found ($PYTHON_CMD)."

# 3. Setup Virtual Environment
echo "Creating Python Virtual Environment (.venv)..."
$PYTHON_CMD -m venv .venv
echo "Virtual environment created successfully."

# 4. Install Python Dependencies
echo "Installing Backend dependencies..."
source .venv/bin/activate

echo "Upgrading pip..."
pip install --upgrade pip --quiet

if [ -f "requirements.txt" ]; then
    echo "Installing from requirements.txt..."
    pip install -r requirements.txt
else
    echo "requirements.txt not found. Skipping..."
fi

if [ -f "requirements-dev.txt" ]; then
    echo "Installing dev dependencies..."
    pip install -r requirements-dev.txt
fi

echo "Note: For SQL Server support, ensure you have the Microsoft ODBC Driver installed."
echo "Backend dependencies installed successfully."

# 5. Install Frontend Dependencies
echo "Installing Frontend dependencies (npm)..."
if [ -f "package.json" ]; then
    npm install
else
    echo "package.json not found. Skipping..."
fi
echo "Frontend dependencies installed."

echo ""
echo "Installation Complete!"
echo "You can now run the application using: ./run.sh"
echo ""
