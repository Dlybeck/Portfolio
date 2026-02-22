#!/bin/bash
set -e

echo "🔄 Restarting OpenHands and All Agent Servers"
echo "============================================"

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

echo ""
echo "1. Stopping all agent containers..."
AGENT_CONTAINERS=$(docker ps --filter "name=agent" --format "{{.Names}}" 2>/dev/null || true)
if [ -n "$AGENT_CONTAINERS" ]; then
    echo "   Found agent containers:"
    echo "$AGENT_CONTAINERS" | while read name; do
        echo "   - $name"
    done
    echo "$AGENT_CONTAINERS" | xargs -r docker stop 2>/dev/null || true
    echo "✅ Stopped all agent containers"
else
    echo "   No agent containers found"
fi

echo ""
echo "2. Stopping OpenHands main container..."
if docker ps --format '{{.Names}}' | grep -q "^openhands-app$"; then
    docker stop openhands-app 2>/dev/null || true
    docker rm openhands-app 2>/dev/null || true
    echo "✅ Stopped and removed openhands-app"
else
    echo "⚠️  openhands-app not running"
fi

echo ""
echo "3. Cleaning up any remaining agent containers..."
docker ps -a --filter "name=agent" --format "{{.Names}}" 2>/dev/null | xargs -r docker rm -f 2>/dev/null || true
echo "✅ Cleaned up stopped agent containers"

echo ""
echo "4. Starting OpenHands with binding fixes..."
# Use existing fix_agent_binding.sh script
if [ -f "./scripts/fix_agent_binding.sh" ]; then
    bash ./scripts/fix_agent_binding.sh
else
    echo "❌ fix_agent_binding.sh not found"
    echo "   Falling back to basic startup..."
    
    # Create persistence directory if needed
    mkdir -p ~/.openhands
    
    # Load or generate secret key
    KEY_FILE="$HOME/.openhands/oh_secret_key"
    if [ ! -f "$KEY_FILE" ]; then
        python3 -c "import secrets; print(secrets.token_hex(32))" > "$KEY_FILE"
        chmod 600 "$KEY_FILE"
    fi
    OH_SECRET_KEY=$(cat "$KEY_FILE")
    
    # Start OpenHands
    docker run --rm -d \
        --name openhands-app \
        --network host \
        -e AGENT_SERVER_IMAGE_REPOSITORY=ghcr.io/openhands/agent-server \
        -e AGENT_SERVER_IMAGE_TAG=1.10.0-python \
        -e LOG_ALL_EVENTS=true \
        -e OH_SECRET_KEY="$OH_SECRET_KEY" \
        -e BIND_ADDRESS=0.0.0.0 \
        -e HOST=0.0.0.0 \
        -e AGENT_SERVER_BIND_ADDRESS=0.0.0.0 \
        -e AGENT_SERVER_HOST=0.0.0.0 \
        -e AGENT_ENV_BIND_ADDRESS=0.0.0.0 \
        -e AGENT_ENV_HOST=0.0.0.0 \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$HOME/.openhands:/.openhands" \
        --add-host host.docker.internal:host-gateway \
        docker.openhands.dev/openhands/openhands:1.3
    echo "✅ OpenHands container started"
fi

echo ""
echo "5. Waiting for services to initialize (20 seconds)..."
for i in {1..20}; do
    echo -n "."
    sleep 1
done
echo ""

echo ""
echo "6. Checking service status..."
echo ""
echo "   Docker containers:"
docker ps --format "{{.Names}}\t{{.Status}}\t{{.Ports}}" | grep -E "openhands|agent" || echo "   (No openhands/agent containers found)"

echo ""
echo "   Listening ports (OpenHands and agents):"
sudo ss -tlnp 2>/dev/null | grep -E ":3000|:48431|:60933|:40461" || echo "   (No expected ports found)"

echo ""
echo "📋 Next steps:"
echo "============="
echo "1. Test OpenHands API:"
echo "   curl -H 'Host: opencode.davidlybeck.com' http://\$TS_IP:3000/api/conversations | head -1"
echo ""
echo "2. Test agent server connectivity:"
echo "   curl http://\$TS_IP:48431/ 2>&1 | head -1"
echo ""
echo "3. Check Cloud Run logs for WebSocket connections"
echo "4. Refresh https://opencode.davidlybeck.com/"
