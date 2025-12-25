# Dev Dashboard QoL Improvements Plan

## Issues to Fix

### Issue 1: Navbar Inconsistency
- **Problem:** VS Code has sleek Dracula navbar, AgentBridge has portfolio-style navbar
- **Impact:** Feels like two disconnected apps, one-way navigation

### Issue 2: Code-Server State Loss (Mobile)
- **Problem:** When tab/app goes inactive on mobile, code-server resets to default directory and closes files
- **Impact:** Super tedious - have to reopen project and all files every time

## Root Causes

### Why State is Lost
1. **Iframe Reload:** Browser suspends/kills iframe when tab becomes inactive
2. **No Persistent Workspace Parameter:** URL is `/dev/vscode/?tkn={{token}}` with no folder parameter
3. **Default Behavior:** code-server defaults to `~` (home directory) when no folder specified
4. **Session Storage:** code-server's workspace storage is per-folder-hash, not URL-stable

## Solution: Combined Fix

### Part 1: Persistent Workspace URL
**Change iframe URL from:**
```html
<iframe src="/dev/vscode/?tkn={{token}}"></iframe>
```

**To:**
```html
<iframe src="/dev/vscode/?tkn={{token}}&folder=/home/dlybeck/Documents/portfolio"></iframe>
```

**How it works:**
- code-server accepts `?folder=` parameter to open specific workspace
- This creates stable workspace hash → persistent state
- Even if iframe reloads, it opens same workspace with same files

**Benefits:**
- ✅ Files stay open across tab switches
- ✅ Same workspace every time
- ✅ Workspace state persists in code-server storage
- ✅ No more tedious re-opening files

### Part 2: Dynamic Workspace Selection
Create a workspace selector in the navbar to switch between projects:

```javascript
// Store last workspace in localStorage
const lastWorkspace = localStorage.getItem('vscode_workspace') || '/home/dlybeck/Documents/portfolio';

// Update iframe src dynamically
function switchWorkspace(folder) {
    localStorage.setItem('vscode_workspace', folder);
    const iframe = document.getElementById('vscode-iframe');
    const currentUrl = new URL(iframe.src);
    currentUrl.searchParams.set('folder', folder);
    iframe.src = currentUrl.toString();
}
```

### Part 3: Unified Dracula Navbar (Both Pages)

**Replace AgentBridge navbar with:**
```html
<nav class="dev-navbar">
  <div class="navbar-content">
    <img src="/static/images/Logo.webp" alt="Logo" class="navbar-logo">
    <div class="navbar-title">Dev Dashboard</div>
  </div>
  <div class="navbar-links">
    <a href="/dev/terminal" class="nav-item" title="VS Code Editor">
      <span class="nav-icon">⌨️</span>
      <span>Editor</span>
    </a>
    <a href="/dev/agentbridge" class="nav-item active" title="Agent Bridge">
      <span class="nav-icon">🌉</span>
      <span>Bridge</span>
    </a>
    <button class="nav-item" onclick="logout()" title="Logout">
      <span class="nav-icon">🚪</span>
      <span>Logout</span>
    </button>
  </div>
</nav>
```

**Navbar CSS (Dracula theme):**
```css
.dev-navbar {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    width: 100%;
    height: 35px;
    background: #21222c;  /* Dracula bg */
    border-bottom: 1px solid #44475a;  /* Dracula border */
    z-index: 9999;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 16px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

.nav-item:hover {
    background: #44475a;  /* Dracula hover */
    color: #bd93f9;  /* Dracula purple */
}

.nav-item.active {
    background: #282a36;  /* Dracula darker */
    color: #bd93f9;  /* Dracula purple */
    border-bottom: 2px solid #bd93f9;
}
```

## Implementation Steps

### Step 1: Fix Code-Server Persistence
1. Update `dev_dashboard.html` iframe URL to include `&folder=` parameter
2. Add JavaScript to remember last workspace in localStorage
3. Test: Open on mobile, switch tabs, come back → files should stay open

### Step 2: Unified Navbar (AgentBridge)
1. Replace AgentBridge navbar HTML (lines 542-550)
2. Replace navbar CSS with Dracula theme
3. Update `.main-container` padding-top from 70px → 45px (smaller navbar)
4. Add logout() function to agentbridge.js

### Step 3: Unified Navbar (Dev Dashboard)
1. Already has correct navbar structure
2. Just ensure "Bridge" link is styled/working
3. Already done! (line 166-169)

### Step 4: Optional Enhancement - Workspace Switcher
Add dropdown in navbar to switch between common projects:
```html
<select class="workspace-selector" onchange="switchWorkspace(this.value)">
  <option value="/home/dlybeck/Documents/portfolio">Portfolio</option>
  <option value="/home/dlybeck/Documents/other-project">Other Project</option>
</select>
```

## Files to Modify

1. **templates/dev/dev_dashboard.html**
   - Line 179: Add `&folder=` parameter to iframe src
   - Add JavaScript for localStorage workspace persistence

2. **templates/dev/agentbridge_dashboard.html**
   - Lines 542-550: Replace navbar HTML
   - Lines 11-536: Update navbar CSS to Dracula theme
   - Line 40: Update padding-top from 70px → 45px
   - Add logout() function to JavaScript section

## Testing Plan

### Test 1: Workspace Persistence
1. Open `/dev/terminal` on mobile
2. Open portfolio project and 3-4 files
3. Switch to another app for 2+ minutes
4. Return to browser tab
5. **Expected:** Same files still open, same workspace

### Test 2: Bidirectional Navigation
1. Start at `/dev/terminal`
2. Click "Bridge" → should go to `/dev/agentbridge`
3. Click "Editor" → should go back to `/dev/terminal`
4. **Expected:** Seamless two-way navigation

### Test 3: Visual Consistency
1. Open both `/dev/terminal` and `/dev/agentbridge`
2. **Expected:** Both have identical Dracula navbar
3. **Expected:** Same height, colors, button styles

## Expected Benefits

### For Mobile Users
- ✅ No more re-opening files after tab switches
- ✅ Workspace state persists across sessions
- ✅ Faster workflow (no tedious setup)

### For All Users
- ✅ Unified visual experience
- ✅ Easy navigation between Editor ↔ Bridge
- ✅ Professional, cohesive dev environment
- ✅ Matches VS Code theme perfectly

## Next Steps

1. Implement Part 1 (Workspace Persistence) - **HIGH PRIORITY** (fixes mobile issue)
2. Implement Part 3 (Unified Navbar) - **MEDIUM PRIORITY** (visual consistency)
3. Implement Part 2 (Workspace Switcher) - **OPTIONAL** (nice-to-have)

Ready to proceed with implementation?
