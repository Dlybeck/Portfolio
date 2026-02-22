#!/bin/bash
set -e

echo "🔍 OpenHands API Discovery Script"
echo "================================"

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"
BASE_URL="http://${TS_IP}:3000"

echo ""
echo "📊 1. Testing all possible API endpoints..."
ENDPOINTS=(
    "/api/conversations"
    "/api/v1/conversations" 
    "/api/agent/servers"
    "/api/v1/agent/servers"
    "/api/servers"
    "/api/v1/servers"
    "/api/agents"
    "/api/v1/agents"
    "/api/ws"
    "/api/v1/ws"
    "/health"
    "/api/health"
    "/api/v1/health"
)

for endpoint in "${ENDPOINTS[@]}"; do
    echo ""
    echo "--- $endpoint ---"
    RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "${BASE_URL}${endpoint}" 2>&1 || echo "CURL_FAILED")
    
    if [ "$RESPONSE" = "CURL_FAILED" ]; then
        echo "   ❌ Failed to connect"
        continue
    fi
    
    LEN=${#RESPONSE}
    echo "   Length: $LEN chars"
    
    if [ $LEN -eq 0 ]; then
        echo "   ⚠️  Empty response"
        continue
    fi
    
    # Check content type
    echo -n "   Content: "
    if [[ "$RESPONSE" =~ ^[\[\{] ]]; then
        echo -n "JSON-like"
        # Try to parse
        echo "$RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list):
        print(f' (List of {len(data)} items)')
        if data and isinstance(data[0], dict):
            print(f'   First item keys: {list(data[0].keys())[:8]}')
    elif isinstance(data, dict):
        print(f' (Dict)')
        print(f'   Keys: {list(data.keys())[:8]}')
except:
    print(' (Invalid JSON)')
" 2>/dev/null || echo " (Could not parse)"
    elif [[ "$RESPONSE" =~ \<html ]] || [[ "$RESPONSE" =~ \<!DOCTYPE ]]; then
        echo "HTML"
    elif [[ "$RESPONSE" =~ ^[0-9a-fA-F]{8} ]]; then
        echo "Possible hex/ID"
    else
        echo "Unknown"
        echo "   Preview: ${RESPONSE:0:80}"
    fi
done

echo ""
echo "🐳 2. Extracting conversation IDs from agent containers..."
docker ps --filter "name=agent" --format "{{.Names}}" 2>/dev/null | while read name; do
    # Try to extract conversation ID from container name
    # Common patterns: openhands-agent-XXXXX, agent-XXXXX, XXXXX where XXXXX might be conversation ID
    CONV_ID=""
    
    # Try to find UUID pattern
    if [[ "$name" =~ [a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12} ]]; then
        CONV_ID="${BASH_REMATCH[0]}"
    # Try to find hex string (32 chars)
    elif [[ "$name" =~ [a-f0-9]{32} ]]; then
        CONV_ID="${BASH_REMATCH[0]}"
    # Try common patterns
    elif [[ "$name" =~ agent-([a-f0-9-]+) ]]; then
        CONV_ID="${BASH_REMATCH[1]}"
    elif [[ "$name" =~ openhands-agent-([a-f0-9-]+) ]]; then
        CONV_ID="${BASH_REMATCH[1]}"
    fi
    
    if [ -n "$CONV_ID" ]; then
        echo "   Container: $name"
        echo "   Possible conversation ID: $CONV_ID"
        
        # Get port mapping
        PORTS=$(docker ps --filter "name=^${name}$" --format "{{.Ports}}" 2>/dev/null || echo "")
        echo "   Ports: $PORTS"
        
        # Extract host port (first mapped port)
        HOST_PORT=$(echo "$PORTS" | grep -o '0.0.0.0:[0-9]*' | head -1 | cut -d: -f2)
        if [ -n "$HOST_PORT" ]; then
            echo "   Host port: $HOST_PORT"
            # Test the agent server directly
            echo -n "   Agent test: "
            curl -s "http://localhost:${HOST_PORT}/" 2>&1 | head -1 | cut -c1-40
        fi
        echo ""
    fi
done

echo ""
echo "🔧 3. Testing POST to create conversation..."
# Try to create a conversation via POST
echo "   Testing POST /api/conversations"
curl -X POST -H "Host: opencode.davidlybeck.com" -H "Content-Type: application/json" \
    -d '{"title":"Test Conversation"}' "${BASE_URL}/api/conversations" 2>&1 | head -100

echo ""
echo "   Testing POST /api/v1/conversations"  
curl -X POST -H "Host: opencode.davidlybeck.com" -H "Content-Type: application/json" \
    -d '{"title":"Test Conversation"}' "${BASE_URL}/api/v1/conversations" 2>&1 | head -100

echo ""
echo "📋 Summary:"
echo "=========="
echo "If endpoints return empty lists but agent containers exist:"
echo "1. API might be at different path (check /api/v1/*)"
echo "2. Conversations might be in different data store"
echo "3. Agent containers might have conversation IDs in labels/metadata"
echo ""
echo "Next: Check container labels for conversation IDs:"
echo "  docker inspect <agent-container> --format='{{json .Config.Labels}}'"
