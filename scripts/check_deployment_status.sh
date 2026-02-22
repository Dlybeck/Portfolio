#!/bin/bash
set -e

echo "🔍 Cloud Run Deployment Status Check"
echo "==================================="

echo ""
echo "1. Checking Dockerfile for required dependencies..."
if [ -f Dockerfile ]; then
    echo "✅ Dockerfile exists"
    grep -n "requirements.txt\|pip install\|python-socks\|websockets" Dockerfile || echo "   (No explicit dependency lines found)"
else
    echo "❌ Dockerfile not found"
fi

echo ""
echo "2. Checking requirements.txt for python-socks..."
if [ -f requirements.txt ]; then
    echo "✅ requirements.txt exists"
    grep -E "python-socks|websockets|aiohttp-socks" requirements.txt || echo "   ❌ Required packages not found in requirements.txt"
else
    echo "❌ requirements.txt not found"
fi

echo ""
echo "3. Checking if our fixes are in the codebase..."
echo "   Checking SOCKS5_PROXY setting in config.py:"
grep -n "SOCKS5_PROXY" core/config.py || echo "   ❌ Not found"
echo "   Checking WebSocket fallback logic in base_proxy.py:"
grep -n "connection_methods\|fall back to direct" services/base_proxy.py | head -5 || echo "   ❌ Not found"

echo ""
echo "4. Checking Cloud Run entrypoint script..."
if [ -f cloud_run_entrypoint.sh ]; then
    echo "✅ cloud_run_entrypoint.sh exists"
    grep -n "0.0.0.0:1055\|SOCKS5 proxy" cloud_run_entrypoint.sh | head -5 || echo "   ❌ SOCKS5 setup not found"
else
    echo "❌ cloud_run_entrypoint.sh not found"
fi

echo ""
echo "📋 Summary:"
echo "=========="
echo "If all checks pass: Code is ready for deployment"
echo "If missing dependencies: WebSocket fallback won't work"
echo ""
echo "Next: Check Cloud Run logs for actual deployment status"
