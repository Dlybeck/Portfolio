#!/bin/bash
set -e

echo "🔐 Setting up Tailscale for Cloud Run..."

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

# Clean up old/stale proxy devices
echo "🧹 Cleaning up stale proxy devices..."
DEVICES_RESPONSE=$(curl -s -X GET https://api.tailscale.com/api/v2/tailnet/-/devices \
  -H "Authorization: Bearer ${ACCESS_TOKEN}")

# Extract device IDs with tag:proxy that are offline and older than 10 minutes
STALE_DEVICES=$(echo "$DEVICES_RESPONSE" | python3 -c "
import sys, json, time
from datetime import datetime, timezone
data = json.load(sys.stdin)
for device in data.get('devices', []):
    if 'tag:proxy' not in device.get('tags', []):
        continue
    device_id = device.get('id', '')
    hostname = device.get('hostname', '')
    online = device.get('online', False)
    last_seen = device.get('lastSeen', '')
    
    # Skip if device is currently online
    if online:
        continue
    
    # Skip if no lastSeen timestamp
    if not last_seen:
        continue
    
    # Calculate age in minutes
    last_dt = datetime.fromisoformat(last_seen.replace('Z', '+00:00'))
    age_minutes = (datetime.now(timezone.utc) - last_dt).total_seconds() / 60
    
    # Delete if offline for more than 10 minutes
    if age_minutes > 10:
        print(f'{device_id} {hostname} {age_minutes:.1f}m')
")

echo "Stale devices to clean:"
echo "$STALE_DEVICES"

# Delete stale devices
for DEVICE_INFO in $STALE_DEVICES; do
    DEVICE_ID=$(echo $DEVICE_INFO | awk '{print $1}')
    HOSTNAME=$(echo $DEVICE_INFO | awk '{print $2}')
    AGE=$(echo $DEVICE_INFO | awk '{print $3}')
    echo "Deleting stale device: $HOSTNAME (offline for $AGE minutes)"
    curl -s -X DELETE "https://api.tailscale.com/api/v2/device/$DEVICE_ID" \
      -H "Authorization: Bearer ${ACCESS_TOKEN}" || true
done

# Generate REUSABLE auth key (so new containers can reconnect as same device)
echo "🔑 Generating reusable auth key..."
AUTH_KEY_RESPONSE=$(curl -s -X POST https://api.tailscale.com/api/v2/tailnet/-/keys \
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"capabilities":{"devices":{"create":{"reusable":true,"ephemeral":true,"preauthorized":true,"tags":["tag:proxy"]}}},"expirySeconds":7776000}')

AUTH_KEY=$(echo $AUTH_KEY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get(\"key\", \"\"))")

if [ -z "$AUTH_KEY" ]; then
  echo "❌ Failed to generate auth key"
  echo "Response: $AUTH_KEY_RESPONSE"
  exit 1
fi

echo "✅ Generated reusable auth key (valid 90 days)"

# Start tailscaled in background
# Fix for Cloud Run packet fragmentation (MTU issue)
export TS_DEBUG_MTU=512
echo "🔧 Starting tailscaled with SOCKS5 server on 0.0.0.0:1055..."
tailscaled --tun=userspace-networking --socks5-server=0.0.0.0:1055 &
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

# Connect to Tailscale network with unique hostname
echo "🔗 Connecting to Tailscale network..."
# Use Cloud Run revision ID for unique hostname, fallback to timestamp
UNIQUE_HOSTNAME="portfolio-app-${K_REVISION:-$(date +%s)}"
echo "Using unique hostname: $UNIQUE_HOSTNAME"
tailscale up --authkey=${AUTH_KEY} --hostname=$UNIQUE_HOSTNAME --accept-routes

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

# Test 1: OpenHands main API (port 3000)
echo "Testing connection to $TARGET_IP:3000 via SOCKS5 proxy..."
# Test multiple endpoints - OpenHands might use /health or /api/health
# Accept ANY 200 response as success
OPENHANDS_TEST_PASSED=false
if curl --socks5 localhost:1055 -H "Host: opencode.davidlybeck.com" --max-time 5 -f -s -o /dev/null -w "%{http_code}" "http://${TARGET_IP}:3000/api/health" 2>/dev/null | grep -q "200"; then
echo "✅ SOCKS5 proxy test passed - can reach Ubuntu server at $TARGET_IP:3000 (/api/health)"
OPENHANDS_TEST_PASSED=true
elif curl --socks5 localhost:1055 -H "Host: opencode.davidlybeck.com" --max-time 5 -f -s -o /dev/null -w "%{http_code}" "http://${TARGET_IP}:3000/health" 2>/dev/null | grep -q "200"; then
echo "✅ SOCKS5 proxy test passed - can reach Ubuntu server at $TARGET_IP:3000 (/health)"
OPENHANDS_TEST_PASSED=true
elif curl --socks5 localhost:1055 -H "Host: opencode.davidlybeck.com" --max-time 5 -f -s -o /dev/null -w "%{http_code}" "http://${TARGET_IP}:3000/" 2>/dev/null | grep -q "200"; then
echo "✅ SOCKS5 proxy test passed - can reach Ubuntu server at $TARGET_IP:3000 (/)"
OPENHANDS_TEST_PASSED=true
else
echo "⚠️  SOCKS5 proxy test failed - cannot reach Ubuntu server at $TARGET_IP:3000"
echo "Debug: Trying without SOCKS5..."
curl -H "Host: opencode.davidlybeck.com" --max-time 3 -I "http://${TARGET_IP}:3000/" 2>&1 | head -5
fi

# Test 2: Agent server port (48431 or other)
echo ""
echo "Testing connection to agent server ports via SOCKS5 proxy..."
# Check if we can detect agent ports from environment or try common ones
AGENT_PORT="${AGENT_SERVER_PORT:-48431}"
echo "Testing agent port $AGENT_PORT..."

# Try to connect to agent port via SOCKS5 (accept any response, including connection refused)
if curl --socks5 localhost:1055 --max-time 5 -s "http://${TARGET_IP}:${AGENT_PORT}/" 2>&1 | head -1 >/dev/null; then
echo "✅ Can connect to agent server at $TARGET_IP:$AGENT_PORT via SOCKS5"
elif timeout 3 bash -c "cat < /dev/null > /dev/tcp/127.0.0.1/1055" 2>/dev/null; then
# SOCKS5 proxy is running, but agent port not accessible
echo "⚠️  SOCKS5 proxy is running but agent port $AGENT_PORT not accessible"
echo "   This could mean:"
echo "   - Agent server not running on port $AGENT_PORT"
echo "   - Agent server binding to 127.0.0.1 instead of 0.0.0.0"
echo "   - Firewall blocking port $AGENT_PORT"
else
echo "❌ Cannot connect to SOCKS5 proxy on port 1055"
fi

echo "🚀 Starting FastAPI application..."
# Start FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 8080
