# Code-Server Persistence Research Findings

## Key Discoveries from Web Search

### 1. Code-Server Workspace Priority Order
Code-server follows this priority for opening directories:
1. **Workspace query parameter** (`?workspace=`)
2. **Folder query parameter** (`?folder=`)
3. **Last opened item** (workspace or folder) - stored in code-server state
4. **Command-line argument**

### 2. State Persistence Behavior
- Code-server **should** remember last opened directory across sessions
- **BUT**: Users report cross-device/cross-browser persistence issues
- State is stored server-side in `~/.local/share/code-server/`

### 3. Mobile Browser Reality (Critical Finding)
From VS Code webview documentation:
> "The contents of webviews are created when the webview becomes visible and **destroyed when the webview is moved into the background**"

**This means:**
- When mobile browser suspends tab → iframe content destroyed
- State inside iframe is lost
- Regular code-server state persistence **may not help** if iframe reloads

## Solution Evaluation

### ❌ **My Original Solution: Just Add `?folder=` Parameter**
**Problems:**
1. Won't help if iframe gets fully reloaded (mobile tab suspension)
2. Code-server already remembers last workspace (should work without parameter)
3. Doesn't address the root cause: iframe destruction on mobile

### ✅ **Better Solution: Multi-Layered Approach**

#### Layer 1: Explicit Workspace Parameter (Baseline)
```html
<iframe src="/dev/vscode/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}"></iframe>
```
**Why:** Ensures consistent starting point even if state is lost

#### Layer 2: Prevent Iframe Reload (Mobile-Specific)
```javascript
// Detect when page becomes hidden/visible
document.addEventListener('visibilitychange', () => {
    if (document.hidden) {
        console.log('[Mobile] Tab hidden - iframe may be suspended');
    } else {
        console.log('[Mobile] Tab visible - checking iframe state');
        // Optionally: check if iframe needs refresh
    }
});

// iOS-specific: prevent tab from being suspended
if (/iPad|iPhone|iPod/.test(navigator.userAgent)) {
    // Keep connection alive with periodic pings
    setInterval(() => {
        fetch('/api/heartbeat', { method: 'HEAD' });
    }, 30000); // Every 30 seconds
}
```

#### Layer 3: State Restoration (If Iframe Reloads)
Use localStorage to save/restore open files:
```javascript
// Save state before unload
window.addEventListener('beforeunload', () => {
    const state = {
        workspace: currentWorkspace,
        openFiles: getOpenFiles(), // Would need to extract from iframe
        timestamp: Date.now()
    };
    localStorage.setItem('vscode_state', JSON.stringify(state));
});

// Restore state on load
window.addEventListener('load', () => {
    const saved = localStorage.getItem('vscode_state');
    if (saved) {
        const state = JSON.parse(saved);
        // Would need code-server API to restore files
    }
});
```

#### Layer 4: Alternative - Direct Link (No Iframe)
**Most Reliable Option:**
Instead of iframe, open code-server in new tab/window:
```html
<a href="http://localhost:8888/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}"
   target="vscode_window"
   class="nav-item">
   Open VS Code
</a>
```

**Benefits:**
- ✅ Code-server runs in its own context (not iframe)
- ✅ Normal browser tab persistence
- ✅ Mobile browsers treat it like any other tab
- ✅ Code-server's built-in state management works perfectly
- ✅ No iframe reload issues

**Drawbacks:**
- ❌ Not embedded (leaves main dashboard)
- ❌ Navbar isn't unified
- ❌ User has to switch tabs manually

## Recommended Solutions (Ranked)

### 🥇 **Option 1: Direct Link with Navbar Integration** (BEST)
- Open code-server in new tab via navbar link
- Add visual indicator when VS Code window is open
- Keep dashboard available for AgentBridge/navigation

**Implementation:**
```html
<a href="http://localhost:8888/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}"
   target="vscode_tab"
   class="nav-item"
   onclick="markVSCodeOpen()">
   <span class="nav-icon">⌨️</span>
   <span>Editor</span>
   <span id="vscode-indicator" class="status-dot hidden"></span>
</a>
```

### 🥈 **Option 2: Iframe + Folder Parameter + Heartbeat** (GOOD)
- Keep iframe approach
- Add `?folder=` parameter for explicit workspace
- Add heartbeat/keepalive for mobile
- Accept that some state loss may still occur

### 🥉 **Option 3: Hybrid - Iframe Desktop, Direct Link Mobile** (COMPLEX)
- Detect mobile/desktop
- Use iframe on desktop (better integration)
- Use direct link on mobile (better persistence)

```javascript
const isMobile = /iPhone|iPad|iPod|Android/i.test(navigator.userAgent);
if (isMobile) {
    // Show "Open Editor" link instead of iframe
} else {
    // Show embedded iframe
}
```

## My Recommendation

**Go with Option 1 (Direct Link)** because:

1. **Solves persistence completely** - No iframe = no reload issues
2. **Simpler** - Relies on code-server's built-in state management
3. **Works identically everywhere** - Desktop, mobile, all browsers
4. **User-friendly** - Dedicated VS Code tab feels professional
5. **Navbar still unified** - Can still have matching Dracula navbar on dashboard

**How it would work:**
1. User clicks "Editor" in navbar → Opens code-server in new tab
2. Code-server opens with specified folder
3. User works in VS Code (full window, no iframe constraints)
4. Files/state persist perfectly (code-server manages it)
5. User switches back to main dashboard for AgentBridge/other tools
6. Can switch between tabs freely without losing state

**The "embedded" feel is overrated if it doesn't work reliably on mobile.**

## What do you think?

Should we:
- A) Go with direct link (Option 1) - most reliable
- B) Try iframe + heartbeat (Option 2) - more integrated but may still have issues
- C) Something else entirely?
