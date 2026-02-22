#!/bin/bash
set -e

echo "🔍 OpenHands One-Shot Debug"
echo "==========================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "📦 1. API /conversations fields:"
API_RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/api/conversations?limit=1" 2>/dev/null || echo "FAILED")
if [ "$API_RESPONSE" != "FAILED" ] && [ -n "$API_RESPONSE" ]; then
    echo "$API_RESPONSE" | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if isinstance(data, list) and data:
        first = data[0]
        print('   First item keys:')
        for k in first.keys():
            print(f'   - {k}')
        # Look for URL-like fields
        print('\\n   URL-like values:')
        for k, v in first.items():
            if isinstance(v, str) and ('url' in k.lower() or 'localhost' in v.lower() or '://' in v):
                print(f'   - {k}: {v[:60]}...')
    else:
        print('   Empty list or not list')
except Exception as e:
    print(f'   JSON error: {e}')
" 2>/dev/null || echo "   Could not parse response"
else
    echo "   API failed or empty"
fi

echo ""
echo "🐳 2. Agent containers (max 3):"
AGENT_CONTAINERS=$(docker ps --filter "name=agent" --format "{{.Names}}\t{{.Ports}}" 2>/dev/null || echo "docker error")
if [ "$AGENT_CONTAINERS" != "docker error" ] && [ -n "$AGENT_CONTAINERS" ]; then
    echo "$AGENT_CONTAINERS" | head -3 | while read line; do
        echo "   $line"
    done
    COUNT=$(echo "$AGENT_CONTAINERS" | wc -l)
    if [ $COUNT -gt 3 ]; then
        echo "   ... and $((COUNT - 3)) more"
    fi
else
    echo "   No agent containers or docker error"
fi

echo ""
echo "🔧 3. First agent environment (key variables):"
AGENT_ID=$(docker ps --filter "name=agent" --format "{{.ID}}" 2>/dev/null | head -1)
if [ -n "$AGENT_ID" ]; then
    docker inspect "$AGENT_ID" --format='{{range .Config.Env}}{{println .}}{{end}}' 2>/dev/null | \
    grep -E -i "port|url|host|conv|agent|server|ws" | head -8 | while read var; do
        echo "   $var"
    done
else
    echo "   No agent containers"
fi

echo ""
echo "🌐 4. Alternative endpoints (quick check):"
for ep in "/api/agent/servers" "/api/servers" "/api/agents" "/health"; do
    echo -n "   $ep: "
    RESP=$(curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000${ep}" 2>&1 | head -1 | tr -d '\n' | cut -c1-40)
    if [ -n "$RESP" ]; then
        echo "$RESP"
    else
        echo "empty"
    fi
done

echo ""
echo "📋 Summary:"
echo "=========="
echo "If conversations has keys but no URLs:"
echo "1. Agent URLs might be elsewhere"
echo "2. Check container env for PORT/URL"
echo "3. Try /api/agent/servers endpoint"
echo ""
echo "Next: Share output of this script."
