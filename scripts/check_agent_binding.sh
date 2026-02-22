#!/bin/bash
set -e

echo "🔍 Checking Agent Server Binding"
echo "================================"

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Checking port 48431 binding..."
if sudo ss -tlnp 2>/dev/null | grep -q ":48431 "; then
    echo "✅ Port 48431 is listening"
    SOCKET_INFO=$(sudo ss -tlnp 2>/dev/null | grep ":48431 ")
    echo "   Socket info: $SOCKET_INFO"
    
    # Check binding address
    if echo "$SOCKET_INFO" | grep -q "0.0.0.0:"; then
        echo "   ✅ Binding to 0.0.0.0 (all interfaces)"
    elif echo "$SOCKET_INFO" | grep -q "127.0.0.1:"; then
        echo "   ⚠️  Binding to 127.0.0.1 (localhost only)"
        echo "   This means Tailscale/remote connections will fail!"
    else
        echo "   Binding to: $(echo "$SOCKET_INFO" | grep -o '[0-9]\+.[0-9]\+.[0-9]\+.[0-9]\+:[0-9]\+')"
    fi
else
    echo "❌ Port 48431 is NOT listening"
    echo "   Agent server may not be running or using different port"
fi

echo ""
echo "2. Checking Docker containers mapping to port 48431..."
DOCKER_MAPPING=$(docker ps --format "{{.Names}}\t{{.Ports}}" 2>/dev/null | grep 48431 || echo "No Docker mapping found")
echo "   $DOCKER_MAPPING"

if [ "$DOCKER_MAPPING" != "No Docker mapping found" ]; then
    CONTAINER_NAME=$(echo "$DOCKER_MAPPING" | awk '{print $1}')
    echo "   Container: $CONTAINER_NAME"
    
    # Get container IP inside Docker network
    CONTAINER_IP=$(docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' "$CONTAINER_NAME" 2>/dev/null || echo "unknown")
    echo "   Container IP: $CONTAINER_IP"
    
    # Check what the container is listening on
    echo "   Checking what container is listening on..."
    docker exec "$CONTAINER_NAME" sh -c 'ss -tlnp 2>/dev/null | grep -E ":80000|:8000" || echo "No listening sockets found"' 2>/dev/null || echo "Cannot exec into container"
fi

echo ""
echo "3. Testing local connectivity..."
echo "   From localhost:"
if curl -s "http://localhost:48431/" 2>&1 | head -1 >/dev/null; then
    echo "   ✅ Can connect via localhost"
else
    echo "   ❌ Cannot connect via localhost"
fi

echo "   From Tailscale IP ($TS_IP):"
if [ "$TS_IP" != "NOT_FOUND" ]; then
    if curl -s "http://$TS_IP:48431/" 2>&1 | head -1 >/dev/null; then
        echo "   ✅ Can connect via Tailscale IP"
    else
        echo "   ❌ Cannot connect via Tailscale IP"
        echo "   Check firewall: sudo ufw status"
    fi
fi

echo ""
echo "4. Testing SOCKS5 proxy connectivity (simulating Cloud Run)..."
echo "   Note: This assumes SOCKS5 proxy is running on localhost:1055"
if ss -tlnp 2>/dev/null | grep -q ":1055 "; then
    echo "   ✅ SOCKS5 proxy is running"
    echo "   Testing connection through SOCKS5 to localhost:48431..."
    if curl --socks5 localhost:1055 --max-time 3 -s "http://localhost:48431/" 2>&1 | head -1 >/dev/null; then
        echo "   ✅ SOCKS5 proxy can reach agent server"
    else
        echo "   ❌ SOCKS5 proxy cannot reach agent server"
        echo "   This matches Cloud Run's issue!"
    fi
else
    echo "   ⚠️  SOCKS5 proxy not running on port 1055"
    echo "   (This is normal unless you're testing Cloud Run connectivity)"
fi

echo ""
echo "📋 Summary:"
echo "=========="
echo "For WebSocket to work from Cloud Run:"
echo "1. Agent server must bind to 0.0.0.0 (not 127.0.0.1)"
echo "2. Port must be accessible via Tailscale IP"
echo "3. SOCKS5 proxy must be able to route to it"
echo ""
echo "If agent server binds to 127.0.0.1:"
echo "  Restart OpenHands with: AGENT_SERVER_BIND_ADDRESS=0.0.0.0"
echo "  Or restart agent containers with proper binding"
