#!/bin/bash

# Dev Server Startup Script
# Double-click this file to start code-server and FastAPI app

echo "🚀 Starting Dev Server..."
echo ""

# Change to project directory
cd "$(dirname "$0")"
PROJECT_DIR="$(pwd)"

echo "📁 Project Directory: $PROJECT_DIR"
echo ""

# Kill any existing servers first
echo "🔄 Killing any existing servers..."
lsof -ti :8888 | xargs kill -9 2>/dev/null || true
lsof -ti :8080 | xargs kill -9 2>/dev/null || true
lsof -ti :8443 | xargs kill -9 2>/dev/null || true
sleep 1
echo ""

# Start code-server
echo "🔵 Starting code-server on 0.0.0.0:8888..."
code-server --bind-addr 0.0.0.0:8888 --auth none > /tmp/code-server.log 2>&1 &
CODE_SERVER_PID=$!
echo "   PID: $CODE_SERVER_PID"

# Wait a moment for code-server to start
sleep 2

# Start FastAPI
echo "🟢 Starting FastAPI server..."
# Activate virtual environment and run
source "$PROJECT_DIR/.venv/bin/activate"
python "$PROJECT_DIR/main.py" > /tmp/portfolio-app.log 2>&1 &
FASTAPI_PID=$!
echo "   PID: $FASTAPI_PID"

echo ""
echo "✅ Dev Server Started!"
echo ""
echo "📍 Access Points:"
echo "   • Local HTTP:   http://localhost:8080/dev"
echo "   • Tailscale:    http://100.84.184.84:8080/dev"
echo "   • code-server:  http://localhost:8888"
echo ""
echo "💡 Note: Using HTTP (port 8080). For HTTPS, create certs in ~/certs/"
echo ""
echo "📋 Logs:"
echo "   • code-server:  tail -f /tmp/code-server.log"
echo "   • FastAPI:      tail -f /tmp/portfolio-app.log"
echo ""
echo "🛑 To stop servers:"
echo "   kill $(lsof -ti :8888) $(lsof -ti :8443)"
echo ""
echo "Press any key to close this window..."
read -n 1
