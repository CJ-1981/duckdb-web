#!/bin/bash

# RQ Worker Startup Script for SPEC-WORKFLOW-001
# This script starts the background worker for workflow automation

set -e

# Environment variables
PYTHON_EXEC="python3"
VENV_PATH=".venv"
WORKER_SCRIPT="src/workflow/worker.py"
WORKER_PID_FILE="worker.pid"
WORKER_LOG_FILE="worker.log"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "Error: Virtual environment not found at $VENV_PATH"
    echo "Please create virtual environment and install dependencies first"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Check if worker is already running
if [ -f "$WORKER_PID_FILE" ]; then
    PID=$(cat "$WORKER_PID_FILE")
    if ps -p $PID > /dev/null 2>&1; then
        echo "Worker is already running with PID: $PID"
        echo "To stop the worker, use: ./stop_worker.sh"
        exit 0
    else
        echo "Stale PID file found. Removing..."
        rm -f "$WORKER_PID_FILE"
    fi
fi

# Create log directory if it doesn't exist
mkdir -p "$(dirname "$WORKER_LOG_FILE")"

# Start worker in background
echo "Starting RQ worker for SPEC-WORKFLOW-001..."
echo "Log file: $WORKER_LOG_FILE"
echo "PID file: $WORKER_PID_FILE"

nohup "$PYTHON_EXEC" "$WORKER_SCRIPT" > "$WORKER_LOG_FILE" 2>&1 &
PID=$!

# Store PID
echo $PID > "$WORKER_PID_FILE"

# Check if worker started successfully
sleep 2
if ps -p $PID > /dev/null 2>&1; then
    echo "Worker started successfully with PID: $PID"
    echo "To view logs: tail -f $WORKER_LOG_FILE"
    echo "To stop the worker: ./stop_worker.sh"
else
    echo "Error: Failed to start worker"
    echo "Check log file for details: $WORKER_LOG_FILE"
    rm -f "$WORKER_PID_FILE"
    exit 1
fi