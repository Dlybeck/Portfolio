#!/bin/bash

# Dev Server Startup Script (Background Mode)
# Used by LaunchAgent for auto-start

# Change to project directory
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

# Log startup
echo "[$(date)] Starting Dev Server..."
echo "Project Directory: $PROJECT_DIR"

# Kill any existing servers first
echo "[$(date)] Killing any existing servers..."
lsof -ti :8888 | xargs kill -9 2>/dev/null || true
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
lsof -ti :8443 | xargs kill -9 2>/dev/null || true
sleep 1

# Start code-server
echo "[$(date)] Starting code-server on 0.0.0.0:8888..."
code-server --bind-addr 0.0.0.0:8888 --auth none > /tmp/code-server.log 2>&1 &
CODE_SERVER_PID=$!
echo "[$(date)] code-server started with PID: $CODE_SERVER_PID"
sleep 2

# Start FastAPI
echo "[$(date)] Starting FastAPI server..."
# Activate virtual environment and run
source "$PROJECT_DIR/.venv/bin/activate"
python "$PROJECT_DIR/main.py" > /tmp/portfolio-app.log 2>&1 &
FASTAPI_PID=$!
echo "[$(date)] FastAPI started with PID: $FASTAPI_PID"

echo "[$(date)] Dev Server startup complete!"
echo "Access: http://localhost:8080/dev or http://100.84.184.84:8080/dev"
