#!/bin/bash
# ==============================================================================
# Persistent Terminal Wrapper for code-server
# Automatically creates or attaches to a tmux session
# This ensures terminal sessions persist even when browser closes
# ==============================================================================

SESSION_NAME="code-server-persistent"

# Check if tmux session exists
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    # Session exists - attach to it
    exec tmux attach-session -t "$SESSION_NAME"
else
    # Session doesn't exist - create new one
    exec tmux new-session -s "$SESSION_NAME"
fi
