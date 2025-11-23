#!/bin/bash

# Code-Server Startup Script
# Used by LaunchAgent for auto-start
# Note: FastAPI server runs on Google Cloud Run, not locally

# Change to project directory
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Log startup
echo "[$(date)] Starting code-server..."
echo "Project Directory: $PROJECT_DIR"

# Kill any existing code-server processes first
echo "[$(date)] Killing any existing code-server..."
lsof -ti :8888 | xargs kill -9 2>/dev/null || true
sleep 1

# Start code-server (runs in foreground - LaunchAgent manages it)
echo "[$(date)] Starting code-server on 0.0.0.0:8888..."
exec code-server --bind-addr 0.0.0.0:8888 --auth none
