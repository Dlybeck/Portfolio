FROM python:3.11-slim

# Install Tailscale and dependencies
RUN apt-get update && apt-get install -y \
    curl \
    iptables \
    iproute2 \
    && curl -fsSL https://tailscale.com/install.sh | sh \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY proxy_main.py .

# Create startup script with OAuth key generation
RUN echo '#!/bin/bash\n\
set -e\n\
\n\
echo "🔐 Generating Tailscale auth key via OAuth..."\n\
\n\
# Get OAuth access token\n\
TOKEN_RESPONSE=$(curl -s -X POST https://api.tailscale.com/api/v2/oauth/token \\\n\
  -u "${TAILSCALE_OAUTH_CLIENT_ID}:${TAILSCALE_OAUTH_CLIENT_SECRET}" \\\n\
  -d "grant_type=client_credentials")\n\
\n\
ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)[\"access_token\"])")\n\
\n\
if [ -z "$ACCESS_TOKEN" ]; then\n\
  echo "❌ Failed to get OAuth token"\n\
  echo "Response: $TOKEN_RESPONSE"\n\
  exit 1\n\
fi\n\
\n\
# Generate auth key using OAuth token\n\
AUTH_KEY_RESPONSE=$(curl -s -X POST https://api.tailscale.com/api/v2/tailnet/-/keys \\\n\
  -H "Authorization: Bearer ${ACCESS_TOKEN}" \\\n\
  -H "Content-Type: application/json" \\\n\
  -d "{\"capabilities\":{\"devices\":{\"create\":{\"reusable\":false,\"ephemeral\":true,\"preauthorized\":true,\"tags\":[\"tag:proxy\"]}}},\"expirySeconds\":7776000}")\n\
\n\
AUTH_KEY=$(echo $AUTH_KEY_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin).get(\"key\", \"\"))")\n\
\n\
if [ -z "$AUTH_KEY" ]; then\n\
  echo "❌ Failed to generate auth key"\n\
  echo "Response: $AUTH_KEY_RESPONSE"\n\
  exit 1\n\
fi\n\
\n\
echo "✅ Generated fresh auth key (valid 90 days)"\n\
\n\
# Start tailscaled in background with MTU fix for Cloud Run packet fragmentation
# See: https://github.com/tailscale/tailscale/issues/9894
export TS_DEBUG_MTU=512
tailscaled --tun=userspace-networking --socks5-server=localhost:1055 &
sleep 2
# Connect to Tailscale network\n\
tailscale up --authkey=${AUTH_KEY} --hostname=cloud-proxy --accept-routes\n\
\n\
echo "✅ Connected to Tailscale"\n\
\n\
# Start FastAPI proxy\n\
exec python proxy_main.py\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port
EXPOSE 8080

# Start services
CMD ["/app/start.sh"]
