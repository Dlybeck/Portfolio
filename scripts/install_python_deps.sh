#!/bin/bash
set -e

echo "🐍 Installing Python Dependencies for OpenHands"
echo "=============================================="

echo ""
echo "1. Checking Python version..."
python3 --version

echo ""
echo "2. Installing required Python packages..."
# Install websockets for WebSocket testing
pip3 install websockets --user 2>&1 | tail -5

# Install python-socks for SOCKS5 support (if needed for testing)
pip3 install python-socks --user 2>&1 | tail -5

echo ""
echo "3. Verifying installations..."
python3 -c "import websockets; print('✅ websockets version:', websockets.__version__)" 2>&1 || echo "❌ websockets import failed"
python3 -c "import python_socks; print('✅ python_socks version:', python_socks.__version__)" 2>&1 || echo "❌ python_socks import failed"

echo ""
echo "📋 If installations failed, try:"
echo "   sudo apt update && sudo apt install python3-pip -y"
echo "   pip3 install --upgrade pip"
echo "   pip3 install websockets python-socks"
