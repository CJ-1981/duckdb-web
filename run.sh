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
    # Use venv Python explicitly to avoid system Python conflicts
    VENV_PYTHON=".venv/bin/python"
else
    VENV_PYTHON="python"
fi

# Run backend in background - use venv python explicitly to ensure correct environment
# Note: --reload disabled for E2E tests to prevent port binding issues
if [ "$PORT" = "3001" ]; then
    # E2E test mode - no reload
    $VENV_PYTHON -m uvicorn src.api.main:create_app --factory --port 8000 &
else
    # Development mode - with reload
    $VENV_PYTHON -m uvicorn src.api.main:create_app --factory --reload --port 8000 &
fi

# 2. Wait a moment for backend to initialize
sleep 2

# 3. Start Frontend (Next.js)
echo "💻 Starting Frontend (Next.js)..."

# Check if node_modules exists, if not install dependencies
if [ ! -d "node_modules" ]; then
    echo "Installing frontend dependencies..."
    npm install
fi

# Function to check if port is in use
is_port_in_use() {
    local port=$1
    if lsof -Pi :$port -sTCP:LISTEN -t >/dev/null 2>&1 ; then
        return 0  # Port is in use
    else
        return 1  # Port is available
    fi
}

# Smart port detection if PORT not already set
if [ -z "$PORT" ]; then
    echo "🔍 Detecting available port..."
    PORTS=(3000 3001 3002 3003)

    for port in "${PORTS[@]}"; do
        if is_port_in_use $port; then
            echo "  ❌ Port $port is in use"
        else
            echo "  ✅ Port $port is available!"
            PORT=$port
            break
        fi
    done

    if [ -z "$PORT" ]; then
        echo "❌ All ports (3000-3003) are in use!"
        echo "Please free up a port and try again."
        exit 1
    fi

    echo "🎯 Using port $PORT"
fi

# Start Next.js with detected or specified port
npm run dev -- -p "$PORT"
