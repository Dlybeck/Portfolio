#!/bin/bash
set -e

echo "🔧 Fixing Everything - OpenHands & Dependencies"
echo "=============================================="

echo ""
echo "1. Installing Python dependencies (websockets)..."
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "   Installing websockets module..."
    pip3 install websockets --user 2>&1 | tail -3
    if ! python3 -c "import websockets" 2>/dev/null; then
        echo "   ❌ Failed to install websockets, trying with sudo..."
        sudo pip3 install websockets 2>&1 | tail -3 || echo "   ⚠️  Installation may have failed"
    fi
else
    echo "   ✅ websockets already installed"
fi

echo ""
echo "2. Restarting OpenHands and agent servers..."
if [ -f "./scripts/restart_openhands.sh" ]; then
    bash ./scripts/restart_openhands.sh
else
    echo "❌ restart_openhands.sh not found"
    echo "   Please run: bash scripts/fix_agent_binding.sh"
fi

echo ""
echo "3. Testing basic connectivity..."
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
if [ "$TS_IP" != "NOT_FOUND" ]; then
    echo "   Testing OpenHands API on $TS_IP:3000..."
    curl -s -H "Host: opencode.davidlybeck.com" "http://${TS_IP}:3000/api/conversations" 2>&1 | head -1 | grep -E "^{|^\[" && echo "   ✅ API responded" || echo "   ⚠️  API may not be ready"
    
    echo "   Testing agent port 48431..."
    curl -s "http://${TS_IP}:48431/" 2>&1 | head -1 | grep -v "curl:" && echo "   ✅ Agent server responding" || echo "   ⚠️  Agent server may not be ready"
else
    echo "   ⚠️  Tailscale not connected"
fi

echo ""
echo "📋 Next Steps:"
echo "============="
echo "1. Wait 2-3 minutes for Cloud Run to redeploy our fixes"
echo "2. Refresh https://opencode.davidlybeck.com/"
echo "3. If WebSocket still fails, run debug script:"
echo "   bash scripts/debug_agent_websocket.sh"
echo ""
echo "✅ Fix script completed!"
