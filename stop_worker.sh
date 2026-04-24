#!/bin/bash

# RQ Worker Stop Script for SPEC-WORKFLOW-001
# This script stops the background worker

set -e

WORKER_PID_FILE="worker.pid"
WORKER_LOG_FILE="worker.log"

# Check if PID file exists
if [ ! -f "$WORKER_PID_FILE" ]; then
    echo "Worker PID file not found. Worker may not be running."
    exit 0
fi

# Read PID
PID=$(cat "$WORKER_PID_FILE")

# Check if process is running
if ! ps -p $PID > /dev/null 2>&1; then
    echo "Process with PID $PID is not running."
    rm -f "$WORKER_PID_FILE"
    exit 0
fi

# Gracefully stop worker
echo "Stopping worker with PID: $PID"
kill -TERM $PID

# Wait for graceful shutdown
timeout=10
count=0
while ps -p $PID > /dev/null 2>&1 && [ $count -lt $timeout ]; do
    echo "Waiting for worker to shutdown gracefully... ($count/$timeout)"
    sleep 1
    count=$((count + 1))
done

# Force kill if still running
if ps -p $PID > /dev/null 2>&1; then
    echo "Force killing worker..."
    kill -KILL $PID
    sleep 2
fi

# Clean up
if ! ps -p $PID > /dev/null 2>&1; then
    echo "Worker stopped successfully"
    rm -f "$WORKER_PID_FILE"
else
    echo "Error: Failed to stop worker with PID: $PID"
    exit 1
fi

echo "Worker cleanup completed"