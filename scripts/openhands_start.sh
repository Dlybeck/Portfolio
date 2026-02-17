#!/bin/bash
set -e

# Configuration
WORKSPACE_BASE="${HOME}/workspace"
CONTAINER_NAME="openhands-app"
IMAGE_NAME="docker.all-hands.dev/all-hands-ai/openhands:0.11"

# Ensure workspace exists
mkdir -p "$WORKSPACE_BASE"

echo "Starting OpenHands..."
echo "Workspace: $WORKSPACE_BASE"
echo "Container: $CONTAINER_NAME"

# Clean up existing container if it exists
if command -v docker >/dev/null 2>&1 && docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "Stopping and removing existing container..."
    docker rm -f "$CONTAINER_NAME"
fi

# Run OpenHands
# We use --rm so it cleans up after itself when stopped
# We map port 3000
if command -v docker >/dev/null 2>&1; then
    docker run --rm \
        --name "$CONTAINER_NAME" \
        -p 3000:3000 \
        -e SANDBOX_USER_ID=$(id -u) \
        -e WORKSPACE_MOUNT_PATH="$WORKSPACE_BASE" \
        -v "$WORKSPACE_BASE:/opt/workspace_base" \
        -v /var/run/docker.sock:/var/run/docker.sock \
        --add-host host.docker.internal:host-gateway \
        "$IMAGE_NAME"
else
    echo "Docker not found. Cannot start OpenHands container."
    exit 1
fi
