#!/bin/bash
# ==============================================================================
# Tmux Session Helper
# Quick commands to manage persistent terminal sessions
# ==============================================================================

SESSION_NAME="code-server-persistent"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

case "${1:-help}" in
    attach|a)
        echo -e "${BLUE}Attaching to session '$SESSION_NAME'...${NC}"
        tmux attach-session -t "$SESSION_NAME"
        ;;

    list|ls)
        echo -e "${BLUE}Active tmux sessions:${NC}"
        tmux ls
        ;;

    kill|k)
        echo -e "${YELLOW}Killing session '$SESSION_NAME'...${NC}"
        tmux kill-session -t "$SESSION_NAME"
        echo -e "${GREEN}✓ Session killed (will restart fresh on next terminal open)${NC}"
        ;;

    new|n)
        NAME="${2:-$SESSION_NAME}"
        echo -e "${BLUE}Creating new session '$NAME'...${NC}"
        tmux new-session -s "$NAME"
        ;;

    status|s)
        echo -e "${BLUE}Session status:${NC}"
        if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
            echo -e "${GREEN}✓ Session '$SESSION_NAME' exists${NC}"
            echo ""
            tmux list-windows -t "$SESSION_NAME"
        else
            echo -e "${YELLOW}Session '$SESSION_NAME' does not exist${NC}"
        fi
        ;;

    help|h|*)
        echo -e "${BLUE}Tmux Session Helper${NC}"
        echo ""
        echo "Usage: $0 <command>"
        echo ""
        echo "Commands:"
        echo "  attach, a      - Attach to persistent session"
        echo "  list, ls       - List all tmux sessions"
        echo "  kill, k        - Kill persistent session (start fresh)"
        echo "  new, n [name]  - Create new named session"
        echo "  status, s      - Show session status"
        echo "  help, h        - Show this help"
        echo ""
        echo "Examples:"
        echo "  $0 attach      # Reconnect to session"
        echo "  $0 list        # See all sessions"
        echo "  $0 kill        # Reset session"
        ;;
esac
