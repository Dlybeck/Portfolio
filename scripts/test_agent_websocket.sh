#!/bin/bash
set -e

echo "🔍 Testing Agent Server WebSocket Endpoint"
echo "========================================="

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Testing HTTP endpoint on agent server (port 48431)..."
echo "   GET http://$TS_IP:48431/"
curl -s "http://$TS_IP:48431/" 2>&1 | head -5

echo ""
echo "2. Testing WebSocket endpoint directly..."
cat > /tmp/test_agent_ws.py << 'PYEOF'
import asyncio
import websockets
import sys

async def test():
    # Test different WebSocket paths that OpenHands might use
    base_url = "ws://100.79.140.119:48431"
    paths_to_test = [
        "/sockets/events/test",
        "/ws",
        "/api/ws",
        "/api/v1/ws",
        "/events",
        "/socket.io",
    ]
    
    for path in paths_to_test:
        url = f"{base_url}{path}"
        print(f"Testing: {url}")
        try:
            async with websockets.connect(url, open_timeout=3) as ws:
                print(f"  ✅ Connected to {path}")
                return True
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue
    
    return False

if __name__ == "__main__":
    result = asyncio.run(test())
    sys.exit(0 if result else 1)
PYEOF

python3 /tmp/test_agent_ws.py 2>&1

echo ""
echo "3. Checking what's actually running on port 48431..."
echo "   Using nmap to scan service (if available):"
if command -v nmap >/dev/null 2>&1; then
    nmap -sV -p 48431 100.79.140.119 2>&1 | grep -A5 "PORT\|Service"
else
    echo "   nmap not installed, trying netcat..."
    timeout 2 bash -c "echo 'GET / HTTP/1.1\\r\\nHost: localhost\\r\\n\\r\\n' | nc 100.79.140.119 48431" 2>&1 | head -10
fi

echo ""
echo "📋 Summary:"
echo "=========="
echo "If agent server rejects WebSocket with 403:"
echo "1. Wrong WebSocket path (not /sockets/events/{id})"
echo "2. Missing required headers (Origin, etc.)"
echo "3. Agent server requires different authentication"
echo ""
echo "Check OpenHands agent server documentation for correct WebSocket path"
