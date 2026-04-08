#!/bin/bash

# Exit script on any error
set -e

# CD to the repo directory (in case script is called from elsewhere)
cd "$(dirname "$0")"

# Function to cleanup background processes on exit
cleanup() {
    echo "Stopping all services..."
    kill $(jobs -p)
}

trap cleanup EXIT

echo "🚀 Starting DuckDB Data Processor Services..."

# 1. Start Backend (FastAPI)
echo "📦 Starting Backend (FastAPI)..."

if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Run backend in background - use python -m uvicorn to ensure PYTHONPATH handling
python -m uvicorn src.api.main:create_app --factory --reload --port 8000 &

# 2. Wait a moment for backend to initialize
sleep 2

# 3. Start Frontend (Next.js)
echo "💻 Starting Frontend (Next.js)..."

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Use PORT environment variable if provided, else default to 3000
npm run dev -- -p "${PORT:-3000}"
