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
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
sleep 2

# Connect to Tailscale network
tailscale up --authkey=${AUTH_KEY} --hostname=portfolio-app --accept-routes

echo "✅ Connected to Tailscale"

# Start FastAPI app
exec uvicorn main:app --host 0.0.0.0 --port 8080
