#!/bin/bash
set -e

echo "🔧 Fixing Everything - OpenHands & Dependencies"
echo "=============================================="

echo ""
echo "1. Setting up Python environment using existing setup..."
if [ -f "./scripts/setup_ubuntu_python.sh" ]; then
    bash ./scripts/setup_ubuntu_python.sh
else
    echo "❌ setup_ubuntu_python.sh not found, trying basic install..."
    # Try apt-get install first (more reliable on Ubuntu)
    if command -v apt-get >/dev/null 2>&1; then
        echo "   Installing via apt-get..."
        sudo apt-get update
        sudo apt-get install -y python3-websockets python3-pip 2>&1 | tail -5
    fi
    
    # Then try pip
    pip3 install websockets --user 2>&1 | tail -3 || echo "⚠️  pip install failed"
    
    # Verify
    python3 -c "import websockets" 2>/dev/null && echo "✅ websockets installed" || echo "❌ websockets not installed"
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
echo "📋 Next Steps:"
echo "============="
echo "1. Wait 2-3 minutes for Cloud Run to redeploy our fixes"
echo "2. Refresh https://opencode.davidlybeck.com/"
echo "3. If WebSocket still fails, run debug script:"
echo "   bash scripts/debug_agent_websocket.sh"
echo ""
echo "✅ Fix script completed!"
