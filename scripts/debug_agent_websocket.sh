#!/bin/bash
set -e

echo "🔍 Debugging Agent Server WebSocket 403 Error"
echo "============================================"

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"
AGENT_PORT="48431"
AGENT_IP="100.79.140.119"

echo ""
echo "1. Checking agent container logs..."
AGENT_CONTAINER=$(docker ps --format "{{.Names}}" | grep agent | head -1)
if [ -n "$AGENT_CONTAINER" ]; then
    echo "   Agent container: $AGENT_CONTAINER"
    echo "   Recent logs (last 20 lines):"
    docker logs --tail 20 "$AGENT_CONTAINER" 2>&1 | while read line; do
        echo "   $line"
    done
else
    echo "   ❌ No agent containers found"
fi

echo ""
echo "2. Testing HTTP endpoints on agent server..."
echo "   Testing root path:"
curl -s "http://$AGENT_IP:$AGENT_PORT/" 2>&1 | head -5

echo "   Testing /health endpoint:"
curl -s "http://$AGENT_IP:$AGENT_PORT/health" 2>&1 | head -5

echo "   Testing /sockets/events/test:"
curl -s "http://$AGENT_IP:$AGENT_PORT/sockets/events/test" 2>&1 | head -5

echo ""
echo "3. Testing WebSocket with different configurations..."

# Check if websockets module is installed
if ! python3 -c "import websockets" 2>/dev/null; then
    echo "❌ Python websockets module not installed"
    echo "   Installing with: pip3 install websockets --user"
    echo "   Or run: bash scripts/install_python_deps.sh"
    echo "   Skipping WebSocket tests..."
    exit 0
fi

cat > /tmp/debug_agent_ws.py << 'PYEOF'
import asyncio
import websockets
import json
import sys

async def test_config(config_name, url, headers=None, extra_params=""):
    print(f"\\n🔧 Testing: {config_name}")
    print(f"   URL: {url}")
    
    try:
        ws_kwargs = {"open_timeout": 5}
        if headers:
            ws_kwargs["extra_headers"] = headers
            
        async with websockets.connect(url, **ws_kwargs) as ws:
            print(f"   ✅ Connected!")
            # Try to send a ping
            await ws.ping()
            pong = await asyncio.wait_for(ws.recv(), timeout=2)
            print(f"   ✅ Ping-pong successful")
            return True
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False

async def run_tests():
    base_url = f"ws://{AGENT_IP}:{AGENT_PORT}"
    conversation_id = "test-conv-123"
    session_key = "test-key-123"
    
    tests = []
    
    # Test 1: Standard OpenHands path with query params
    tests.append((
        "Standard OpenHands path",
        f"{base_url}/sockets/events/{conversation_id}?resend_all=true&session_api_key={session_key}",
        None
    ))
    
    # Test 2: Same but with Origin header
    tests.append((
        "With Origin: localhost",
        f"{base_url}/sockets/events/{conversation_id}?resend_all=true&session_api_key={session_key}",
        [("Origin", f"http://localhost:{AGENT_PORT}")]
    ))
    
    # Test 3: With Origin: agent IP
    tests.append((
        "With Origin: agent IP",
        f"{base_url}/sockets/events/{conversation_id}?resend_all=true&session_api_key={session_key}",
        [("Origin", f"http://{AGENT_IP}:{AGENT_PORT}")]
    ))
    
    # Test 4: Different path - root WebSocket
    tests.append((
        "Root WebSocket",
        f"{base_url}/?session_api_key={session_key}",
        None
    ))
    
    # Test 5: /ws path
    tests.append((
        "/ws path",
        f"{base_url}/ws?session_api_key={session_key}",
        None
    ))
    
    # Test 6: /api/ws path
    tests.append((
        "/api/ws path",
        f"{base_url}/api/ws?session_api_key={session_key}",
        None
    ))
    
    # Test 7: Session key in header instead of query
    tests.append((
        "Session key in Authorization header",
        f"{base_url}/sockets/events/{conversation_id}",
        [("Authorization", f"Bearer {session_key}")]
    ))
    
    results = []
    for name, url, headers in tests:
        success = await test_config(name, url, headers)
        results.append((name, success))
    
    print(f"\\n📊 Summary:")
    for name, success in results:
        status = "✅" if success else "❌"
        print(f"   {status} {name}")

if __name__ == "__main__":
    import os
    AGENT_IP = os.getenv("AGENT_IP", "100.79.140.119")
    AGENT_PORT = os.getenv("AGENT_PORT", "48431")
    
    asyncio.run(run_tests())
PYEOF

AGENT_IP="100.79.140.119" AGENT_PORT="48431" python3 /tmp/debug_agent_ws.py 2>&1

echo ""
echo "📋 Next steps:"
echo "============="
echo "1. Check which WebSocket configuration works"
echo "2. If none work, check agent server authentication requirements"
echo "3. Look for agent server documentation on WebSocket API"
echo "4. Check if session_api_key needs to be validated differently"
echo ""
echo "If standard path works: Cloud Run proxy needs fixing"
echo "If different path works: Update proxy to use correct path"
echo "If Authorization header works: Update proxy to move session_api_key to header"
