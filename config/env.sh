#!/bin/bash
# OpenHands Environment Configuration
# Store this file safely - contains secrets!

# Ubuntu Server IP (Tailscale)
export UBUNTU_TS_IP="100.79.140.119"

# OpenHands Settings
export OPENHANDS_PORT="3000"
export OPENHANDS_IMAGE="docker.openhands.dev/openhands/openhands:1.3"
export AGENT_SERVER_IMAGE="ghcr.io/openhands/agent-server:1.10.0-python"

# Cloud Run Settings
export CLOUD_RUN_SERVICE="portfolio"
export CLOUD_RUN_REGION="us-central1"

# WebSocket Settings  
export WEBSOCKET_PATH="/sockets/events"

# Tailscale OAuth (set in Cloud Run environment)
# export TAILSCALE_OAUTH_CLIENT_ID=""
# export TAILSCALE_OAUTH_CLIENT_SECRET=""

echo "✅ Environment configuration loaded"
