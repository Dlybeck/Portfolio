#!/bin/bash

# Dev Server Auto-Start Management Script
# Double-click to manage auto-start on login

PLIST_PATH="$HOME/Library/LaunchAgents/com.dlybeck.portfolio-dev.plist"
SERVICE_NAME="com.dlybeck.portfolio-dev"

echo "======================================"
echo "  Dev Server Auto-Start Manager"
echo "======================================"
echo ""

# Check current status
if launchctl list | grep -q "$SERVICE_NAME"; then
    STATUS="✅ ENABLED (Running)"
else
    if [ -f "$PLIST_PATH" ]; then
        STATUS="⚠️  DISABLED (File exists but not loaded)"
    else
        STATUS="❌ NOT INSTALLED"
    fi
fi

echo "Current Status: $STATUS"
echo ""
echo "What would you like to do?"
echo ""
echo "  1) Enable auto-start (start on login)"
echo "  2) Disable auto-start (stop service)"
echo "  3) Check service status"
echo "  4) View service logs"
echo "  5) Restart service now"
echo "  6) Exit"
echo ""
read -p "Enter choice [1-6]: " choice

case $choice in
    1)
        echo ""
        echo "Enabling auto-start..."
        launchctl load "$PLIST_PATH"
        echo "✅ Auto-start enabled! Server will start on next login."
        echo "   Starting now..."
        launchctl start "$SERVICE_NAME"
        sleep 2
        echo ""
        echo "📍 Access Points:"
        echo "   • https://localhost:8443/dev"
        echo "   • https://100.84.184.84:8443/dev"
        ;;
    2)
        echo ""
        echo "Disabling auto-start..."
        launchctl unload "$PLIST_PATH"
        echo "✅ Auto-start disabled. Server stopped."
        ;;
    3)
        echo ""
        echo "Service Status:"
        echo "==============="
        if launchctl list | grep -q "$SERVICE_NAME"; then
            echo "✅ Service is RUNNING"
            launchctl list | grep "$SERVICE_NAME"
        else
            echo "❌ Service is NOT running"
        fi
        echo ""
        echo "Port Status:"
        echo "============"
        echo "code-server (8888):"
        lsof -ti :8888 > /dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not running"
        echo "FastAPI (8443):"
        lsof -ti :8443 > /dev/null 2>&1 && echo "  ✅ Running" || echo "  ❌ Not running"
        ;;
    4)
        echo ""
        echo "Recent Logs:"
        echo "============"
        echo ""
        echo "--- LaunchAgent Output ---"
        tail -20 /tmp/portfolio-dev-stdout.log 2>/dev/null || echo "No logs yet"
        echo ""
        echo "--- LaunchAgent Errors ---"
        tail -20 /tmp/portfolio-dev-stderr.log 2>/dev/null || echo "No errors"
        ;;
    5)
        echo ""
        echo "Restarting service..."
        launchctl stop "$SERVICE_NAME" 2>/dev/null
        sleep 1
        launchctl start "$SERVICE_NAME"
        echo "✅ Service restarted"
        ;;
    6)
        echo "Exiting..."
        exit 0
        ;;
    *)
        echo "Invalid choice"
        ;;
esac

echo ""
echo "Press any key to close..."
read -n 1
