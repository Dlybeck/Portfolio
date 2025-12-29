# Code-Server Terminal Persistence

## Overview

Your code-server (VS Code) is now configured for **fully persistent terminal sessions** using tmux. This means:

✅ **Terminal sessions survive browser closes**
✅ **Work continues even when disconnected**
✅ **Same session when you reconnect**
✅ **All terminal history preserved**

---

## How It Works

### Architecture

```
VS Code Terminal
    ↓
persistent-shell.sh (wrapper script)
    ↓
tmux session "code-server-persistent"
    ↓
bash shell (your work happens here)
```

When you open a terminal in VS Code:
1. Instead of a normal bash shell, it runs `persistent-shell.sh`
2. This script checks if a tmux session exists
3. **If exists**: Attaches to the existing session (your previous work)
4. **If not**: Creates a new tmux session

### What Persists

| Feature | Persists? | Notes |
|---------|-----------|-------|
| **Terminal session** | ✅ Yes | Same tmux session on reconnect |
| **Running processes** | ✅ Yes | Background jobs keep running |
| **Terminal history** | ✅ Yes | Full command history preserved |
| **Working directory** | ✅ Yes | Stays in same folder |
| **Environment variables** | ✅ Yes | Exports persist in session |
| **Open files (VS Code)** | ✅ Yes | Workspace state saved |
| **VS Code settings** | ✅ Yes | Stored in ~/.local/share/code-server/ |
| **Unsaved file changes** | ⚠️ Maybe | Auto-save enabled (1s delay) |

---

## Usage

### Normal Usage
Just use VS Code terminals normally! The persistence is automatic and invisible.

1. Open VS Code at `/dev/vscode/`
2. Open a terminal (Ctrl+` or Terminal menu)
3. Do your work
4. **Close browser** - session keeps running
5. **Reopen VS Code** - reconnects to same session!

### Manual Session Management

**View active tmux sessions:**
```bash
tmux ls
```

**Manually attach to persistent session:**
```bash
tmux attach-session -t code-server-persistent
```

**Kill the persistent session** (start fresh):
```bash
tmux kill-session -t code-server-persistent
```

**Create multiple persistent sessions:**
Edit `scripts/persistent-shell.sh` and change `SESSION_NAME` to create separate sessions.

---

## Advanced: Multiple Sessions

If you want separate persistent sessions for different projects:

1. Create new wrapper scripts:
```bash
cp scripts/persistent-shell.sh scripts/persistent-shell-project1.sh
```

2. Edit the new script and change `SESSION_NAME`:
```bash
SESSION_NAME="project1"
```

3. In VS Code settings, specify which shell to use per workspace

---

## Troubleshooting

### "Session already attached elsewhere"

If tmux complains the session is already attached:
```bash
# Force detach others and attach
tmux attach-session -d -t code-server-persistent
```

### Reset everything (start completely fresh)

```bash
# Kill all tmux sessions
tmux kill-server

# Restart code-server
launchctl unload ~/Library/LaunchAgents/com.coder.code-server.plist
launchctl load ~/Library/LaunchAgents/com.coder.code-server.plist
```

### See what's running in background

```bash
# List all tmux sessions
tmux ls

# Show processes in the persistent session
tmux send-keys -t code-server-persistent "ps aux | grep -i python" Enter
```

---

## Configuration Files

### VS Code Settings
Location: `~/.local/share/code-server/User/settings.json`

```json
{
  "terminal.integrated.shell.osx": "/path/to/Portfolio/scripts/persistent-shell.sh",
  "files.autoSave": "afterDelay",
  "files.autoSaveDelay": 1000
}
```

### Persistent Shell Wrapper
Location: `scripts/persistent-shell.sh`

```bash
#!/bin/bash
SESSION_NAME="code-server-persistent"

if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    exec tmux attach-session -t "$SESSION_NAME"
else
    exec tmux new-session -s "$SESSION_NAME"
fi
```

---

## Comparison: Dashboard vs Code-Server Terminals

| Feature | Dashboard Terminal | Code-Server Terminal |
|---------|-------------------|---------------------|
| **Persistence** | 1 hour idle timeout | Forever (tmux) |
| **Multiple tabs** | ❌ No | ✅ Yes (tmux windows) |
| **Copy/paste** | Basic | Full VS Code support |
| **Syntax highlighting** | ❌ No | ✅ Yes (via extensions) |
| **File tree integration** | ❌ No | ✅ Yes |
| **Reconnection** | Auto (WebSocket) | Manual (refresh page) |

**Recommendation:** Use code-server terminals for development work, dashboard terminal for quick commands.

---

## Auto-Save Configuration

Your files auto-save after 1 second of inactivity. This minimizes data loss if browser crashes.

To disable auto-save:
1. Open VS Code Settings (Cmd+,)
2. Search for "auto save"
3. Change to "off"

---

## Notes

- **tmux is required** - Already installed on your Mac
- **Sessions are local to the Mac** - Each machine has separate sessions
- **No session limit** - Create as many named sessions as you want
- **Background processes survive** - Long-running tasks keep going

---

## Quick Reference

```bash
# View all sessions
tmux ls

# Attach to main session
tmux attach -t code-server-persistent

# Detach from session (leave it running)
Ctrl+B, then D

# Kill session (restart fresh)
tmux kill-session -t code-server-persistent

# Create new window in session
Ctrl+B, then C

# Switch between windows
Ctrl+B, then N (next) or P (previous)
```

For more tmux commands: https://tmuxcheatsheet.com/
