#!/bin/bash
set -e

# OpenHands v1.3.0 startup script

# Ensure persistence directory exists
mkdir -p ~/.openhands

# Load or generate OH_SECRET_KEY (stored outside the repo, never committed)
KEY_FILE="$HOME/.openhands/oh_secret_key"
if [ ! -f "$KEY_FILE" ]; then
    python3 -c "import secrets; print(secrets.token_hex(32))" > "$KEY_FILE"
    chmod 600 "$KEY_FILE"
fi
OH_SECRET_KEY=$(cat "$KEY_FILE")

# Configuration (v1.3.0): use new image and minimal mounts
CONTAINER_NAME="openhands-app"

# Preserve container cleanup pattern (lines 31-35 in original): stop/rm existing container if present
if command -v docker >/dev/null 2>&1 && docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping and removing existing container..."
    docker rm -f "$CONTAINER_NAME"
fi

# Run OpenHands (detached background service, no interactive mounts)
if command -v docker >/dev/null 2>&1; then
    docker run --rm -d \
        --name "$CONTAINER_NAME" \
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
else
    echo "Docker not found. Cannot start OpenHands container."
    exit 1
fi
