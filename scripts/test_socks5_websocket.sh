#!/bin/bash
set -e

echo "🔍 Testing SOCKS5 WebSocket Connectivity"
echo "======================================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Testing HTTP over SOCKS5 to agent port (simulate curl test)..."
echo "   Testing: curl --socks5 localhost:1055 http://${TS_IP}:48431/"
if curl --socks5 localhost:1055 --max-time 5 -s "http://${TS_IP}:48431/" 2>&1 | head -2; then
    echo "✅ HTTP over SOCKS5 to port 48431 works"
else
    echo "❌ HTTP over SOCKS5 to port 48431 fails"
    echo "   This suggests agent server isn't accessible via SOCKS5 at all"
fi

echo ""
echo "2. Checking if SOCKS5 proxy is running..."
if ss -tlnp 2>/dev/null | grep -q ":1055 "; then
    echo "✅ SOCKS5 proxy listening on port 1055"
    SOCKS5_INFO=$(ss -tlnp 2>/dev/null | grep ":1055 ")
    echo "   Socket info: $SOCKS5_INFO"
else
    echo "❌ SOCKS5 proxy NOT listening on port 1055"
    echo "   Tailscale SOCKS5 proxy may not have started"
fi

echo ""
echo "3. Testing WebSocket connectivity with Python..."
cat > /tmp/test_ws_socks5.py << 'PYEOF'
import asyncio
import websockets
import sys
import os

async def test_websocket():
    target = "ws://100.79.140.119:48431/sockets/events/test"
    proxy = "socks5://localhost:1055"
    
    print(f"Testing WebSocket to: {target}")
    print(f"Using proxy: {proxy}")
    
    try:
        async with websockets.connect(
            target,
            proxy=proxy,
            open_timeout=5
        ) as websocket:
            print("✅ WebSocket connection successful!")
            return True
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

if __name__ == "__main__":
    # Check if we can import required modules
    try:
        import websockets
        import python_socks
        print("✅ Required modules installed")
    except ImportError as e:
        print(f"❌ Missing module: {e}")
        sys.exit(1)
    
    # Run test
    result = asyncio.run(test_websocket())
    sys.exit(0 if result else 1)
PYEOF

python3 /tmp/test_ws_socks5.py 2>&1

echo ""
echo "4. Alternative: Test with wscat if available..."
if command -v wscat >/dev/null 2>&1; then
    echo "   wscat found, testing WebSocket..."
    # Note: wscat may not support SOCKS5 proxy
    echo "   (wscat may not support SOCKS5 proxy)"
else
    echo "   wscat not installed"
fi

echo ""
echo "📋 Summary:"
echo "=========="
echo "If HTTP over SOCKS5 works but WebSocket fails:"
echo "1. Python websockets library SOCKS5 support issue"
echo "2. Agent server WebSocket endpoint issue"
echo ""
echo "If both fail:"
echo "1. Agent server not accessible on port 48431"
echo "2. SOCKS5 proxy not working for that port"
echo "3. Firewall/ACL blocking port 48431"
