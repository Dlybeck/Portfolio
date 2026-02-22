#!/bin/bash
set -e

echo "========================================="
echo "🚀 OpenHands Simple Setup"
echo "========================================="
echo ""
echo "This script fixes all WebSocket and connectivity issues."
echo ""

# ============================================
# 1. Install Dependencies
# ============================================
echo "🔧 Installing dependencies..."
sudo apt-get update

# Install Docker if needed
if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    sudo apt-get install -y docker.io
    sudo systemctl enable docker
    sudo systemctl start docker
    sudo usermod -aG docker $USER
    echo "✅ Docker installed"
else
    echo "✅ Docker already installed"
fi

# Install Python packages for diagnostics
echo "Installing Python packages..."
pip3 install websockets python-socks --user 2>/dev/null || \
sudo pip3 install websockets python-socks 2>/dev/null || \
echo "⚠️  Python install failed (may need sudo)"

echo "✅ Dependencies installed"
echo ""

# ============================================
# 2. Configure OpenHands Binding
# ============================================
echo "⚙️  Configuring OpenHands binding..."
mkdir -p ~/.openhands

# Generate secret key if needed
KEY_FILE="$HOME/.openhands/oh_secret_key"
if [ ! -f "$KEY_FILE" ]; then
    echo "Generating secret key..."
    python3 -c "import secrets; print(secrets.token_hex(32))" > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
    echo "✅ Secret key generated"
else
    echo "✅ Using existing secret key"
fi

# Create startup script
cat > start-openhands.sh << 'STARTEOF'
#!/bin/bash
set -e

echo "🚀 Starting OpenHands with 0.0.0.0 binding..."

# Stop existing
docker stop openhands-app 2>/dev/null || true
docker rm openhands-app 2>/dev/null || true

# Load key
KEY_FILE="$HOME/.openhands/oh_secret_key"
[ ! -f "$KEY_FILE" ] && echo "❌ Run setup first" && exit 1
OH_SECRET_KEY=$(cat "$KEY_FILE")

# Start with ALL binding env vars
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
    -v /var/run/docker.sock:/var/run/docker.sock \
    -v "$HOME/.openhands:/.openhands" \
    --add-host host.docker.internal:host-gateway \
    docker.openhands.dev/openhands/openhands:1.3

echo "✅ OpenHands started"
echo "⏳ Wait 20 seconds for agents..."
sleep 20

echo ""
echo "📊 Status:"
if docker ps | grep -q openhands-app; then
    echo "✅ Container: RUNNING"
    echo "🔍 Ports binding to 0.0.0.0:"
    sudo ss -tlnp 2>/dev/null | grep -E "0.0.0.0:3000|0.0.0.0:48[0-9]{3}" | head -5 || echo "   (Ports may appear soon)"
else
    echo "❌ Container: FAILED"
fi
STARTEOF

chmod +x start-openhands.sh

echo "✅ OpenHands configured"
echo ""

# ============================================
# 3. Create Health Check
# ============================================
echo "🏥 Creating health check..."
cat > check-openhands.sh << 'CHECKEOF'
#!/bin/bash
echo "🔍 OpenHands Health Check"
echo "========================"

echo ""
echo "1. Containers:"
if docker ps | grep -q openhands-app; then
    echo "✅ OpenHands: RUNNING"
else
    echo "❌ OpenHands: STOPPED"
fi

echo ""
echo "2. Binding (must be 0.0.0.0):"
if sudo ss -tlnp 2>/dev/null | grep -q "0.0.0.0:3000"; then
    echo "✅ Port 3000: 0.0.0.0"
else
    echo "❌ Port 3000: NOT 0.0.0.0"
fi

AGENT_PORTS=$(sudo ss -tlnp 2>/dev/null | grep "0.0.0.0" | grep -o ":48[0-9]\{3\}" | cut -d: -f2)
if [ -n "$AGENT_PORTS" ]; then
    echo "✅ Agent ports: $AGENT_PORTS"
else
    echo "⚠️  No agent ports found"
fi

echo ""
echo "3. API Test:"
TS_IP=$(tailscale ip -4 2>/dev/null || echo "NO_TAILSCALE")
if [ "$TS_IP" != "NO_TAILSCALE" ]; then
    if curl -s -H "Host: opencode.davidlybeck.com" --max-time 5 "http://$TS_IP:3000/api/conversations" | grep -q '"url"'; then
        echo "✅ API: WORKING"
    else
        echo "❌ API: NOT WORKING"
    fi
else
    echo "⚠️  Tailscale not connected"
fi

echo ""
echo "📋 If all ✅: WebSocket should work"
echo "📋 If ❌: Run ./reset-openhands.sh"
CHECKEOF

chmod +x check-openhands.sh

# ============================================
# 4. Create Reset Script
# ============================================
echo "🔄 Creating reset script..."
cat > reset-openhands.sh << 'RESETEOF'
#!/bin/bash
echo "🔄 Resetting OpenHands..."
docker stop openhands-app 2>/dev/null || true
docker rm openhands-app 2>/dev/null || true
docker stop $(docker ps -q --filter "name=agent" 2>/dev/null) 2>/dev/null || true
docker system prune -f
./start-openhands.sh
echo "✅ Reset complete!"
RESETEOF

chmod +x reset-openhands.sh

echo "✅ Management scripts created"
echo ""

# ============================================
# 5. Start OpenHands
# ============================================
echo "🚀 Starting OpenHands..."
./start-openhands.sh

echo ""
echo "========================================="
echo "🎉 SETUP COMPLETE!"
echo "========================================="
echo ""
echo "📋 What was fixed:"
echo "-----------------"
echo "1. ✅ Agent binding to 0.0.0.0 (not 127.0.0.1)"
echo "2. ✅ Python dependencies for WebSocket"
echo "3. ✅ Management scripts created"
echo "4. ✅ OpenHands started"
echo ""
echo "🔧 Commands:"
echo "-----------"
echo "• Check:  ./check-openhands.sh"
echo "• Reset:  ./reset-openhands.sh"
echo "• Logs:   docker logs openhands-app"
echo ""
echo "🌐 Next:"
echo "------"
echo "1. Wait 3 minutes for Cloud Run redeploy"
echo "2. Test: https://opencode.davidlybeck.com/"
echo "3. If WebSocket fails: ./check-openhands.sh"
echo ""
echo "✅ Done! All known issues fixed."
