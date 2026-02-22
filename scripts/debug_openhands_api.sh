#!/bin/bash
set -e

echo "🐛 OpenHands API Debug Script"
echo "============================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Testing all OpenHands endpoints..."
ENDPOINTS=(
    "/health"
    "/api/health" 
    "/api/status"
    "/api/conversations?limit=1"
    "/api/conversations"
    "/api/agent/servers"
    "/api/agents"
    "/api/servers"
    "/api/ws"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo ""
    echo "--- Testing: $endpoint ---"
    RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000${endpoint}" 2>&1 || echo "FAILED")
    STATUS=$?
    if [ $STATUS -eq 0 ]; then
        LENGTH=${#RESPONSE}
        echo "Status: OK, Length: $LENGTH chars"
        
        # Check if it looks like JSON
        if [[ "$RESPONSE" =~ ^[\[\{] ]]; then
            echo "Format: JSON-like"
            # Try to parse and show structure
            echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f'  List with {len(data)} items')
        if data:
            first = data[0]
            if isinstance(first, dict):
                print(f'  First item keys: {list(first.keys())[:10]}')
    elif isinstance(data, dict):
        print(f'  Dict keys: {list(data.keys())[:10]}')
except:
    pass
" 2>/dev/null || echo "  Could not parse as JSON"
        elif [[ "$RESPONSE" =~ \<html ]] || [[ "$RESPONSE" =~ \<!DOCTYPE ]]; then
            echo "Format: HTML"
        elif [[ -z "$RESPONSE" ]]; then
            echo "Format: Empty"
        else
            echo "Format: Unknown"
            echo "  Preview: ${RESPONSE:0:100}"
        fi
    else
        echo "Status: FAILED"
    fi
done

echo ""
echo "2. Looking for agent server ports..."
echo "   Active ports 36000-39999:"
sudo ss -tlnp 2>/dev/null | grep -E ":(36[0-9]{3}|37[0-9]{3}|38[0-9]{3}|39[0-9]{3})" | while read line; do
    echo "   $line"
done

echo ""
echo "3. Testing one agent server directly..."
# Find first agent port
AGENT_PORT=$(sudo ss -tlnp 2>/dev/null | grep -E ":(36[0-9]{3}|37[0-9]{3}|38[0-9]{3}|39[0-9]{3})" | head -1 | grep -o ":[0-9]*" | cut -d: -f2)
if [ -n "$AGENT_PORT" ]; then
    echo "   Testing agent port $AGENT_PORT..."
    curl -s "http://localhost:${AGENT_PORT}/health" 2>&1 | head -2
    curl -s "http://localhost:${AGENT_PORT}/" 2>&1 | head -2
else
    echo "   No agent ports found"
fi

echo ""
echo "📋 Analysis:"
echo "==========="
echo "If /api/conversations returns data but no URLs:"
echo "1. Check response format with: curl -H 'Host: opencode.davidlybeck.com' 'http://${TS_IP}:3000/api/conversations?limit=1' | python3 -m json.tool"
echo "2. Look for 'url', 'agent_url', or similar fields"
echo "3. Check if agent URLs are in a different endpoint"
