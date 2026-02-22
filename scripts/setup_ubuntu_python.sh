#!/bin/bash
set -e

echo "🐍 Setting Up Python Environment for Ubuntu Server"
echo "================================================"

echo ""
echo "1. Checking Python installation..."
python3 --version
pip3 --version

echo ""
echo "2. Checking existing requirements.txt..."
if [ -f "requirements.txt" ]; then
    echo "✅ requirements.txt found"
    echo "   Installing dependencies from requirements.txt..."
    
    # Try user install first
    if pip3 install -r requirements.txt --user 2>&1 | tail -5; then
        echo "✅ Dependencies installed to user site"
    else
        echo "⚠️  User install failed, trying system install (may need sudo)..."
        sudo pip3 install -r requirements.txt 2>&1 | tail -5 || echo "⚠️  System install also failed"
    fi
else
    echo "❌ requirements.txt not found"
    echo "   Installing essential packages manually..."
    pip3 install websockets python-socks --user 2>&1 | tail -3
fi

echo ""
echo "3. Verifying installations..."
python3 -c "
try:
    import websockets
    print('✅ websockets:', websockets.__version__)
except ImportError:
    print('❌ websockets not installed')
    print('   Try: sudo apt update && sudo apt install python3-websockets')
" 2>&1

python3 -c "
try:
    import python_socks
    print('✅ python_socks:', python_socks.__version__)
except ImportError:
    print('❌ python_socks not installed')
" 2>&1

echo ""
echo "📋 Alternative installation methods:"
echo "==================================="
echo "If pip install fails, try:"
echo "  sudo apt update"
echo "  sudo apt install python3-websockets python3-pip"
echo "  pip3 install --upgrade pip"
echo "  pip3 install -r requirements.txt --user"
