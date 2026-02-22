#!/bin/bash
set -e

echo "🔍 Deep OpenHands Diagnostic"
echo "==========================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Checking OpenHands container status..."
if docker ps --format '{{.Names}}' | grep -q "^openhands-app$"; then
    echo "✅ OpenHands container is running"
    
    # Check container details
    echo "   Container details:"
    docker ps --filter "name=openhands-app" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    
    # Check environment variables
    echo "   Environment variables in container:"
    docker inspect openhands-app --format='{{range .Config.Env}}{{println .}}{{end}}' | grep -i "bind\|host\|agent" | head -10
else
    echo "❌ OpenHands container NOT running"
    echo "   Trying to start with current script..."
    if [ -f scripts/openhands_start.sh ]; then
        bash scripts/openhands_start.sh
        sleep 10
    fi
fi

echo ""
echo "2. Checking OpenHands logs (last 20 lines)..."
if docker ps --format '{{.Names}}' | grep -q "^openhands-app$"; then
    docker logs openhands-app --tail 20 2>&1 | while read line; do echo "   $line"; done
    
    # Look for agent server related logs
    echo ""
    echo "   Agent server logs:"
    docker logs openhands-app 2>&1 | grep -i "agent\|spawn\|container\|port" | tail -10 | while read line; do echo "   $line"; done
else
    echo "   No container to check logs"
fi

echo ""
echo "3. Testing OpenHands API endpoints..."
echo "   Health endpoint:"
curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/health" 2>&1 | head -2
echo "   Status endpoint:"
curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/api/status" 2>&1 | head -2
echo "   Conversations endpoint (full response, truncated):"
API_RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/api/conversations?limit=1" 2>&1)
echo "   Response length: ${#API_RESPONSE} characters"
if [ ${#API_RESPONSE} -gt 0 ]; then
    echo "   First 500 chars:"
    echo "${API_RESPONSE:0:500}"
    
    # Check for JSON structure
    if echo "$API_RESPONSE" | grep -q '{'; then
        echo "   Looks like JSON"
        # Try to parse with python
        echo "$API_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print('   JSON parsed successfully')
    print(f'   Type: {type(data)}')
    if isinstance(data, list):
        print(f'   List length: {len(data)}')
        if len(data) > 0:
            item = data[0]
            print(f'   First item keys: {list(item.keys())}')
            if 'url' in item:
                print(f'   URL found: {item[\"url\"]}')
            else:
                print('   No URL key found')
                # Look for any URL-like keys
                url_keys = [k for k in item.keys() if 'url' in k.lower()]
                if url_keys:
                    print(f'   URL-like keys: {url_keys}')
    elif isinstance(data, dict):
        print(f'   Dict keys: {list(data.keys())}')
except Exception as e:
    print(f'   JSON parse error: {e}')
" 2>/dev/null || echo "   JSON parsing failed"
    else
        echo "   Not JSON"
    fi
else
    echo "   Empty response"
fi

echo ""
echo "4. Checking Docker socket permissions..."
if [ -e /var/run/docker.sock ]; then
    echo "✅ Docker socket exists"
    LS_OUTPUT=$(ls -la /var/run/docker.sock)
    echo "   Permissions: $LS_OUTPUT"
    
    # Test if current user can access Docker
    if docker ps >/dev/null 2>&1; then
        echo "✅ User has Docker access"
    else
        echo "❌ User cannot access Docker"
        echo "   Try: sudo usermod -aG docker $USER"
    fi
else
    echo "❌ Docker socket not found"
fi

echo ""
echo "5. Checking for running agent containers..."
AGENT_CONTAINERS=$(docker ps --filter "name=agent" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}" 2>/dev/null || echo "   Docker error")
if [ -n "$AGENT_CONTAINERS" ] && [ "$AGENT_CONTAINERS" != "   Docker error" ]; then
    echo "Agent containers:"
    echo "$AGENT_CONTAINERS"
else
    echo "No agent containers running"
fi

echo ""
echo "📋 Summary:"
echo "=========="
echo "If no agent URL in API:"
echo "1. OpenHands not spawning agent servers"
echo "2. API response format changed"
echo "3. Docker permissions issue"
echo "4. OpenHands configuration missing"
echo ""
echo "Check OpenHands logs for 'agent', 'spawn', 'container', 'port' messages"
