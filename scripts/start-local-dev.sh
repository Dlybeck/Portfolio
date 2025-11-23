#!/bin/bash
# ==============================================================================
# Local Development Startup Script
# Starts all components needed for the Portfolio dev environment
# ==============================================================================

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get project directory (parent of scripts/)
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Portfolio Dev Environment Startup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# ==============================================================================
# 1. Check Python Virtual Environment
# ==============================================================================
echo -e "${YELLOW}[1/5] Checking Python environment...${NC}"

if [ ! -d ".venv" ]; then
    echo -e "${RED}✗ Virtual environment not found${NC}"
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
source .venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"

# Check if dependencies are installed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing Python dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r "$PROJECT_DIR/requirements.txt"
    echo -e "${GREEN}✓ Dependencies installed${NC}"
else
    echo -e "${GREEN}✓ Dependencies already installed${NC}"
fi

echo ""

# ==============================================================================
# 2. Configure and Start code-server
# ==============================================================================
echo -e "${YELLOW}[2/5] Configuring code-server...${NC}"

# Check if code-server is installed
if ! command -v code-server &> /dev/null; then
    echo -e "${RED}✗ code-server not found${NC}"
    echo -e "${YELLOW}Install with: brew install code-server${NC}"
    exit 1
fi

# Create config directory if needed
mkdir -p ~/.config/code-server

# Check current config
CURRENT_PORT=$(grep "bind-addr:" ~/.config/code-server/config.yaml 2>/dev/null | awk '{print $2}' | cut -d: -f2)

if [ "$CURRENT_PORT" != "8888" ]; then
    echo -e "${YELLOW}Updating code-server config to use port 8888...${NC}"
    cat > ~/.config/code-server/config.yaml << EOF
bind-addr: 0.0.0.0:8888
auth: none
cert: false
EOF
    echo -e "${GREEN}✓ code-server config updated${NC}"

    # Restart code-server via LaunchAgent if running
    if launchctl list | grep -q "com.coder.code-server"; then
        echo -e "${YELLOW}Restarting code-server...${NC}"
        launchctl unload ~/Library/LaunchAgents/com.coder.code-server.plist 2>/dev/null || true
        sleep 2
        launchctl load ~/Library/LaunchAgents/com.coder.code-server.plist 2>/dev/null || true
        sleep 3
    fi
else
    echo -e "${GREEN}✓ code-server already configured on port 8888${NC}"
fi

# Check if code-server is running
if lsof -i :8888 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ code-server is running on port 8888${NC}"
else
    echo -e "${YELLOW}Starting code-server manually...${NC}"
    # Kill any process on port 8888
    lsof -ti :8888 | xargs kill -9 2>/dev/null || true
    sleep 1
    # Start code-server in background
    nohup code-server --bind-addr 0.0.0.0:8888 --auth none > /tmp/code-server-manual.log 2>&1 &
    sleep 3

    if lsof -i :8888 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ code-server started${NC}"
    else
        echo -e "${RED}✗ Failed to start code-server${NC}"
        echo -e "${YELLOW}Check logs: /tmp/code-server-manual.log${NC}"
        exit 1
    fi
fi

echo ""

# ==============================================================================
# 3. Initialize and Start Agor
# ==============================================================================
echo -e "${YELLOW}[3/5] Setting up Agor...${NC}"

# Check if agor is installed
if ! command -v agor &> /dev/null; then
    echo -e "${RED}✗ Agor not found${NC}"
    echo -e "${YELLOW}Install with: npm install -g agor-live${NC}"
    exit 1
fi

# Initialize Agor if needed (check for database file, not just directory)
if [ ! -f "$HOME/.agor/agor.db" ]; then
    echo -e "${YELLOW}Initializing Agor (first time setup)...${NC}"
    # Agor needs to be initialized in a directory, but we'll use project dir
    # Run init with default options to avoid prompts
    cd "$PROJECT_DIR"
    # Note: If agor prompts, user should answer to complete first-time setup
    agor init || echo -e "${YELLOW}⚠ Agor init incomplete - run 'agor init' manually if needed${NC}"
    cd "$SCRIPT_DIR"
    echo -e "${GREEN}✓ Agor initialized${NC}"
else
    echo -e "${GREEN}✓ Agor already initialized (found database)${NC}"
fi

# Check if Agor daemon is running
if lsof -i :3030 >/dev/null 2>&1; then
    echo -e "${GREEN}✓ Agor daemon already running on port 3030${NC}"
else
    echo -e "${YELLOW}Starting Agor daemon...${NC}"
    # Start daemon in background
    nohup agor daemon start > /tmp/agor-daemon.log 2>&1 &
    sleep 3

    if lsof -i :3030 >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Agor daemon started on port 3030${NC}"
    else
        echo -e "${YELLOW}⚠ Agor daemon may not be running (check /tmp/agor-daemon.log)${NC}"
    fi
fi

echo ""

# ==============================================================================
# 4. Check Security Configuration
# ==============================================================================
echo -e "${YELLOW}[4/5] Checking security configuration...${NC}"

if [ ! -f "$PROJECT_DIR/.env" ]; then
    echo -e "${RED}✗ .env file not found${NC}"
    echo -e "${YELLOW}Run: python setup_security.py${NC}"
    exit 1
fi

# Check for JWT secret (required for token generation)
if ! grep -q "^SECRET_KEY=" "$PROJECT_DIR/.env" 2>/dev/null; then
    echo -e "${RED}✗ SECRET_KEY not configured${NC}"
    echo -e "${YELLOW}Run: python setup_security.py${NC}"
    exit 1
fi

# TOTP is optional for local dev (required for cloud)
if ! grep -q "^TOTP_SECRET=" "$PROJECT_DIR/.env" 2>/dev/null; then
    echo -e "${YELLOW}⚠ TOTP_SECRET not configured - authentication disabled for local dev${NC}"
fi

echo -e "${GREEN}✓ Security configuration looks good${NC}"
echo ""

# ==============================================================================
# 5. Start FastAPI Server
# ==============================================================================
echo -e "${YELLOW}[5/5] Starting FastAPI server...${NC}"

# Kill any existing uvicorn/FastAPI process
pkill -f "uvicorn main:app" 2>/dev/null || true
sleep 1

# Check if SSL certificates exist
SSL_CERT="$HOME/.ssl/cert.pem"
SSL_KEY="$HOME/.ssl/key.pem"

if [ -f "$SSL_CERT" ] && [ -f "$SSL_KEY" ]; then
    PORT=8443
    PROTOCOL="https"
    echo -e "${GREEN}✓ SSL certificates found - starting with HTTPS${NC}"
else
    PORT=8080
    PROTOCOL="http"
    echo -e "${YELLOW}⚠ No SSL certificates - starting with HTTP${NC}"
    echo -e "${YELLOW}  To enable HTTPS, generate certificates:${NC}"
    echo -e "${YELLOW}  mkdir -p ~/.ssl${NC}"
    echo -e "${YELLOW}  openssl req -x509 -newkey rsa:2048 -nodes -keyout ~/.ssl/key.pem -out ~/.ssl/cert.pem -days 365${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}✓ All services configured!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Starting FastAPI server...${NC}"
echo ""
echo -e "${YELLOW}Service URLs:${NC}"
echo -e "  Dev Dashboard:  ${PROTOCOL}://localhost:${PORT}/dev"
echo -e "  VS Code:        http://localhost:8888"
echo -e "  Agor:           http://localhost:3030"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Change to project root so Pydantic Settings can find .env
cd "$PROJECT_DIR"

# Start uvicorn (this will run in foreground)
if [ "$PROTOCOL" = "https" ]; then
    exec python main.py
else
    exec python main.py
fi
