#!/bin/bash
set -e

echo "🔧 Fixing OpenHands Agent Server Binding"
echo "========================================"

# Get Tailscale IP
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NOT_FOUND")
echo "Tailscale IPv4: $TS_IP"

# Stop current OpenHands container
echo ""
echo "1. Stopping current OpenHands container..."
if docker ps --format '{{.Names}}' | grep -q "^openhands-app$"; then
    docker stop openhands-app 2>/dev/null || true
    docker rm openhands-app 2>/dev/null || true
    echo "✅ Stopped openhands-app"
else
    echo "⚠️  openhands-app not running"
fi

# Create persistence directory if needed
mkdir -p ~/.openhands

# Load or generate secret key
KEY_FILE="$HOME/.openhands/oh_secret_key"
if [ ! -f "$KEY_FILE" ]; then
    python3 -c "import secrets; print(secrets.token_hex(32))" > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo "✅ Generated new secret key"
fi
OH_SECRET_KEY=$(cat "$KEY_FILE")

echo ""
echo "2. Starting OpenHands with agent binding fixes..."
echo "   (Agent servers will bind to 0.0.0.0 instead of 127.0.0.1)"

# Start OpenHands with environment variables that should make agent servers bind to 0.0.0.0
# Try multiple environment variable patterns to make agent servers bind to 0.0.0.0
docker run --rm -d \
    --name openhands-app \
    --network host \
    -e AGENT_SERVER_IMAGE_REPOSITORY=ghcr.io/openhands/agent-server \
    -e AGENT_SERVER_IMAGE_TAG=1.10.0-python \
    -e LOG_ALL_EVENTS=true \
    -e OH_SECRET_KEY="$OH_SECRET_KEY" \
    -e BIND_ADDRESS=0.0.0.0 \
    -e HOST=0.0.0.0 \
    -e LISTEN_HOST=0.0.0.0 \
    -e HTTP_HOST=0.0.0.0 \
    -e AGENT_SERVER_BIND_ADDRESS=0.0.0.0 \
    -e AGENT_SERVER_HOST=0.0.0.0 \
    -e AGENT_SERVER_LISTEN_HOST=0.0.0.0 \
    -e AGENT_ENV_BIND_ADDRESS=0.0.0.0 \
    -e AGENT_ENV_HOST=0.0.0.0 \
    -e AGENT_EXTRA_ENV="BIND_ADDRESS=0.0.0.0 HOST=0.0.0.0" \
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$HOME/.openhands:/.openhands" \
    --add-host host.docker.internal:host-gateway \
    docker.openhands.dev/openhands/openhands:1.3

echo "✅ OpenHands container started with binding fixes"

echo ""
echo "3. Waiting for OpenHands to initialize (15 seconds)..."
sleep 15

echo ""
echo "4. Testing the fix..."
# Run diagnostic to check if agent servers now bind correctly
bash ./scripts/diagnostic.sh

echo ""
echo "📋 Next Steps:"
echo "=============="
echo "1. Refresh https://opencode.davidlybeck.com/"
echo "2. Check Cloud Run logs for WebSocket connections"
echo "3. If still failing, check if agent ports now bind to 0.0.0.0:"
echo "   sudo ss -tlnp | grep '36[0-9]\{3\}'"
echo "   (Should show 0.0.0.0:PORT, not 127.0.0.1:PORT)"
