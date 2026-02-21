#!/bin/bash
set -e

echo "🔐 Generating Tailscale auth key via OAuth..."

# Get OAuth access token
TOKEN_RESPONSE=$(curl -s -X POST https://api.tailscale.com/api/v2/oauth/token \
  -u "${TAILSCALE_OAUTH_CLIENT_ID}:${TAILSCALE_OAUTH_CLIENT_SECRET}" \
  -d "grant_type=client_credentials")

echo "OAuth response: $TOKEN_RESPONSE"

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get(\"access_token\", \"\"))" 2>&1)

if [ -z "$ACCESS_TOKEN" ]; then
  echo "❌ Failed to get OAuth token"
  echo "Response: $TOKEN_RESPONSE"
  exit 1
fi

echo "✅ Got OAuth access token"

# Generate auth key using OAuth token
AUTH_KEY_RESPONSE=$(curl -s -X POST https://api.tailscale.com/api/v2/tailnet/-/keys \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"capabilities":{"devices":{"create":{"reusable":false,"ephemeral":true,"preauthorized":true,"tags":["tag:proxy"]}}},"expirySeconds":7776000}')

AUTH_KEY=$(echo $AUTH_KEY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get(\"key\", \"\"))")

if [ -z "$AUTH_KEY" ]; then
  echo "❌ Failed to generate auth key"
  echo "Response: $AUTH_KEY_RESPONSE"
  exit 1
fi

echo "✅ Generated fresh auth key (valid 90 days)"

# Start tailscaled in background
# Fix for Cloud Run packet fragmentation (MTU issue)
export TS_DEBUG_MTU=512
echo "🔧 Starting tailscaled with SOCKS5 server on localhost:1055..."
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
TAILSCALED_PID=$!
sleep 3

# Check if tailscaled is running
if ! kill -0 $TAILSCALED_PID 2>/dev/null; then
echo "❌ tailscaled failed to start"
exit 1
fi

echo "🔍 Checking SOCKS5 server status..."
# Verify SOCKS5 port is listening
if ss -tlnp 2>/dev/null | grep -q ":1055 "; then
echo "✅ SOCKS5 proxy listening on port 1055"
else
echo "⚠️  SOCKS5 port 1055 not listening, checking alternative methods..."
# Try netstat as fallback
netstat -tlnp 2>/dev/null | grep ":1055 " && echo "✅ SOCKS5 proxy found via netstat"
fi

# Connect to Tailscale network
echo "🔗 Connecting to Tailscale network..."
tailscale up --authkey=${AUTH_KEY} --hostname=portfolio-app --accept-routes

# Verify Tailscale connection
sleep 2
if tailscale status >/dev/null 2>&1; then
echo "✅ Connected to Tailscale"
echo "📊 Tailscale status:"
# Get IPv4 address (handle multiple IPs from tailscale ip)
TAILSCALE_IPV4=$(tailscale ip -4 2>/dev/null || tailscale status --json 2>/dev/null | jq -r '.Self.TailscaleIPs[] | select(. | test("^[0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+$"))' | head -1)
if [ -z "$TAILSCALE_IPV4" ]; then
echo "⚠️  Could not extract IPv4 address, using first IP"
TAILSCALE_IPV4=$(tailscale ip | head -1 | awk '{print $1}')
fi
echo "Tailscale IPv4: $TAILSCALE_IPV4"
else
echo "❌ Tailscale connection failed"
exit 1
fi

# Test SOCKS5 connectivity
echo "🧪 Testing SOCKS5 proxy connectivity..."
# Use MAC_SERVER_IP environment variable if set, otherwise use the extracted Tailscale IPv4
TARGET_IP="${MAC_SERVER_IP:-$TAILSCALE_IPV4}"
echo "Target Ubuntu server IP: $TARGET_IP"
echo "Testing connection to $TARGET_IP:3000 via SOCKS5 proxy..."
# Test multiple endpoints - OpenHands might use /health or /api/health
# Accept ANY 200 response as success
if curl --socks5 localhost:1055 -H "Host: opencode.davidlybeck.com" --max-time 5 -f -s -o /dev/null -w "%{http_code}" "http://${TARGET_IP}:3000/api/health" 2>/dev/null | grep -q "200"; then
echo "✅ SOCKS5 proxy test passed - can reach Ubuntu server at $TARGET_IP:3000 (/api/health)"
elif curl --socks5 localhost:1055 -H "Host: opencode.davidlybeck.com" --max-time 5 -f -s -o /dev/null -w "%{http_code}" "http://${TARGET_IP}:3000/health" 2>/dev/null | grep -q "200"; then
echo "✅ SOCKS5 proxy test passed - can reach Ubuntu server at $TARGET_IP:3000 (/health)"
elif curl --socks5 localhost:1055 -H "Host: opencode.davidlybeck.com" --max-time 5 -f -s -o /dev/null -w "%{http_code}" "http://${TARGET_IP}:3000/" 2>/dev/null | grep -q "200"; then
echo "✅ SOCKS5 proxy test passed - can reach Ubuntu server at $TARGET_IP:3000 (/)"
else
echo "⚠️  SOCKS5 proxy test failed - cannot reach Ubuntu server at $TARGET_IP:3000"
echo "Debug: Trying without SOCKS5..."
curl -H "Host: opencode.davidlybeck.com" --max-time 3 -I "http://${TARGET_IP}:3000/" 2>&1 | head -5
fi

echo "🚀 Starting FastAPI application..."
# Start FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 8080
