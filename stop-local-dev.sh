#!/bin/bash
# ==============================================================================
# Local Development Stop Script
# Stops all components of the Portfolio dev environment
# ==============================================================================

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Stopping Portfolio Dev Environment${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Stop FastAPI/uvicorn
echo -e "${YELLOW}Stopping FastAPI server...${NC}"
pkill -f "uvicorn main:app" 2>/dev/null && echo -e "${GREEN}✓ FastAPI stopped${NC}" || echo -e "${YELLOW}⚠ FastAPI not running${NC}"

# Stop Agor daemon
echo -e "${YELLOW}Stopping Agor daemon...${NC}"
if command -v agor &> /dev/null; then
    agor daemon stop 2>/dev/null && echo -e "${GREEN}✓ Agor daemon stopped${NC}" || echo -e "${YELLOW}⚠ Agor not running${NC}"
else
    echo -e "${YELLOW}⚠ Agor not installed${NC}"
fi

# Note about code-server
echo ""
echo -e "${YELLOW}Note: code-server is managed by LaunchAgent${NC}"
echo -e "${YELLOW}To stop it:${NC}"
echo -e "  launchctl unload ~/Library/LaunchAgents/com.coder.code-server.plist"
echo ""
echo -e "${GREEN}✓ Development environment stopped${NC}"
