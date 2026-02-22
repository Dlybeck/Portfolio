#!/bin/bash
set -e

echo "🔍 OpenHands Logs Check"
echo "======================"

echo "1. Checking OpenHands container status..."
if docker ps --format '{{.Names}}' | grep -q "^openhands-app$"; then
    echo "✅ OpenHands container is running"
else
    echo "❌ OpenHands container NOT running"
    echo "   To start it: bash scripts/openhands_start.sh"
    exit 1
fi

echo ""
echo "2. Checking Docker permissions..."
if ! docker ps >/dev/null 2>&1; then
    echo "❌ User cannot access Docker"
    echo "   Fix with: sudo usermod -aG docker \$USER"
    echo "   Then log out and back in"
    echo ""
    echo "   For temporary access: newgrp docker"
    echo "   Then restart OpenHands: docker rm -f openhands-app && bash scripts/openhands_start.sh"
else
    echo "✅ User has Docker access"
fi

echo ""
echo "3. Recent OpenHands logs (last 30 lines):"
echo "----------------------------------------"
docker logs openhands-app --tail 30 2>&1

echo ""
echo "4. Looking for agent-related logs:"
echo "---------------------------------"
docker logs openhands-app 2>&1 | grep -i "agent\|spawn\|container\|port\|docker\|error\|fail" | tail -20

echo ""
echo "5. Checking for agent containers:"
echo "--------------------------------"
AGENT_CONTAINERS=$(docker ps --filter "name=agent" --format "{{.Names}}" 2>/dev/null || echo "none")
if [ "$AGENT_CONTAINERS" != "none" ] && [ -n "$AGENT_CONTAINERS" ]; then
    echo "✅ Agent containers found:"
    echo "$AGENT_CONTAINERS" | while read name; do echo "   - $name"; done
else
    echo "❌ No agent containers found"
fi

echo ""
echo "📋 What to look for:"
echo "==================="
echo "If you see errors about:"
echo "- 'permission denied' or 'cannot connect to Docker' → Docker permissions issue"
echo "- 'failed to spawn agent' → OpenHands configuration issue"
echo "- 'agent server' or 'container created' → Agent servers are spawning"
echo ""
echo "💡 Next steps:"
echo "1. If Docker permission errors: sudo usermod -aG docker \$USER, log out/in"
echo "2. If no agent containers: check OpenHands configuration"
echo "3. If agent containers but no WebSocket: check binding (should be 0.0.0.0)"
