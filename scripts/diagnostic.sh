#!/bin/bash
set -e

echo "🔍 OpenHands Diagnostic Script"
echo "=============================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

# Test OpenHands conversation API
echo ""
echo "1. Testing OpenHands API..."
API_RESPONSE=$(curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/api/conversations?limit=1" 2>&1 || echo "FAILED")
if echo "$API_RESPONSE" | grep -q '"url"'; then
    echo "✅ API responded with agent URL"
    AGENT_URL=$(echo "$API_RESPONSE" | grep -o '"url":"[^"]*"' | head -1 | cut -d'"' -f4)
    echo "   Agent URL: $AGENT_URL"
    # Extract port
    if [[ "$AGENT_URL" =~ localhost:([0-9]+) ]]; then
        AGENT_PORT=${BASH_REMATCH[1]}
        echo "   Agent port: $AGENT_PORT"
    fi
else
    echo "❌ API response missing agent URL"
    echo "   Response preview: ${API_RESPONSE:0:200}"
fi

# Check if agent port is listening
echo ""
echo "2. Checking agent server port..."
if [ -n "$AGENT_PORT" ]; then
    if sudo ss -tlnp 2>/dev/null | grep -q ":${AGENT_PORT} "; then
        LISTENING=$(sudo ss -tlnp 2>/dev/null | grep ":${AGENT_PORT} ")
        echo "✅ Port $AGENT_PORT is listening"
        echo "   Details: $LISTENING"
    else
        echo "❌ Port $AGENT_PORT NOT listening"
    fi
else
    echo "⚠️  Could not determine agent port"
fi

# Test connectivity from Cloud Run perspective (simulate SOCKS5)
echo ""
echo "3. Testing SOCKS5 proxy to agent port..."
if [ -n "$AGENT_PORT" ]; then
    # Try to connect via SOCKS5 (if tailscale is running locally)
    if curl --socks5 localhost:1055 --max-time 3 -s "http://${TS_IP}:${AGENT_PORT}/health" 2>&1 | grep -q "healthy"; then
        echo "✅ SOCKS5 can reach agent server"
    else
        echo "❌ SOCKS5 cannot reach agent server"
    fi
fi

echo ""
echo "📋 Summary:"
echo "=========="
echo "If all checks pass, WebSocket should work."
echo "If API fails: OpenHands configuration issue"
echo "If port not listening: Agent server binding issue"
echo "If SOCKS5 fails: Tailscale/network issue"
