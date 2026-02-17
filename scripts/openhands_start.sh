#!/bin/bash
set -e

# Configuration
WORKSPACE_BASE="${HOME}/workspace"
CONFIG_FILE="${HOME}/.openhands-config.toml"
CONTAINER_NAME="openhands-app"
IMAGE_NAME="ghcr.io/all-hands-ai/openhands:0.11"
DOCKER_BINARY="/usr/bin/docker"
BUILDX_PATH="$HOME/.docker/cli-plugins/docker-buildx"

# Ensure workspace exists
mkdir -p "$WORKSPACE_BASE"

# Ensure config file exists
touch "$CONFIG_FILE"

# Install buildx if missing (required for sandbox build)
if [ ! -f "$BUILDX_PATH" ]; then
    echo "Installing docker-buildx..."
    mkdir -p "$(dirname "$BUILDX_PATH")"
    curl -Lo "$BUILDX_PATH" https://github.com/docker/buildx/releases/download/v0.12.1/buildx-v0.12.1.linux-amd64
    chmod +x "$BUILDX_PATH"
fi

echo "Starting OpenHands..."
echo "Workspace: $WORKSPACE_BASE"
echo "Config: $CONFIG_FILE"
echo "Container: $CONTAINER_NAME"

# Clean up existing container if it exists
if command -v docker >/dev/null 2>&1 && docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping and removing existing container..."
    docker rm -f "$CONTAINER_NAME"
fi

# Run OpenHands
if command -v docker >/dev/null 2>&1; then
    docker run --rm \
        --name "$CONTAINER_NAME" \
        -p 3000:3000 \
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH="$WORKSPACE_BASE" \
        -v "$WORKSPACE_BASE:/opt/workspace_base" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        -v "$DOCKER_BINARY:/usr/bin/docker" \
        -v "$BUILDX_PATH:/usr/libexec/docker/cli-plugins/docker-buildx" \
        -v "$CONFIG_FILE:/app/config.toml" \
        --add-host host.docker.internal:host-gateway \
        "$IMAGE_NAME"
else
    echo "Docker not found. Cannot start OpenHands container."
    exit 1
fi
