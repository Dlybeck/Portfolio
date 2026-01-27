# OpenCode Web Integration - Research Summary & Implementation Plan

**Date:** 2026-01-26  
**Status:** ✅ Research Complete - Ready for Implementation

---

## Executive Summary

Successfully identified and tested **OpenCode Web** as the solution for mobile-friendly remote development. OpenCode's built-in web interface is fully compatible with **oh-my-opencode (omo)** plugin, providing all Sisyphus orchestrator capabilities in a clean browser UI.

**Key Findings:**
- ✅ OpenCode web works perfectly with omo agents
- ✅ Mobile-optimized interface (much better than terminal)
- ✅ Session persistence across devices (server-side)
- ✅ All omo agents available (Sisyphus, Prometheus, Oracle, Librarian, Explore)
- ✅ User tested and approved ("so clean actually I love it")

---

## Problem Statement (Original Request)

### Issues Identified
1. **VS Code loses state** when switching devices (open files, tabs, settings)
2. **Terminal not working** (SOCKS5 error - separate issue, not addressed in this plan)
3. **Mobile UX poor** - wanted button-based OpenCode interface, not keyboard tricks
4. **File viewing needs** - VS Code essential for images/complex files (TUI insufficient)
5. **No mobile-friendly OpenCode access**

### User Requirements
- ✅ VS Code for file viewing/editing (images, complex files)
- ✅ OpenCode Web for AI assistance (mobile-optimized)
- ✅ All state persistent across devices (Android, iOS, Desktop)
- ✅ Server-side persistence only (no cloud sync)
- ✅ Works with oh-my-opencode (omo) plugin

---

## Solution Architecture

### Current Setup
```
Cloud Run Container (Tailscale SOCKS5 proxy)
    ↓
Ubuntu Server (100.82.216.64)
    ├─ code-server:8888 → /dev/vscode ✅ Working
    ├─ ttyd:7681 → /dev/terminal ❌ Broken (SOCKS5 error)
    └─ OpenCode in tmux ✅ Working (terminal-only)
```

### Proposed Setup
```
Cloud Run Container (Tailscale SOCKS5 proxy)
    ↓
Ubuntu Server (100.82.216.64)
    ├─ code-server:8888 → /dev/vscode ✅ Working + Persistence
    ├─ opencode web:4096 → /dev/opencode ⭐ NEW
    └─ ttyd:7681 → /dev/terminal (optional, not required)
```

### New User Workflow
```
/dev Hub Page
  ├── [VS Code] → File browsing, editing, viewing images
  ├── [OpenCode] → AI chat, code generation, assistance
  └── [Terminal] → (backup option, not primary)

Mobile/Desktop: Same interface, same state, seamless switching
```

---

## Research Findings

### OpenCode Web (Built-in Official Feature)

**Command:**
```bash
opencode web --port 4096 --hostname 0.0.0.0
```

**Features:**
- Browser-based chat UI (not terminal-based)
- Mobile-responsive design
- Session persistence (server-side)
- Authentication support (OPENCODE_SERVER_PASSWORD)
- Can attach TUI with `opencode attach http://server:4096`
- WebSocket support for real-time updates

**Verified Compatible with omo:**
- ✅ All omo agents available (Sisyphus, Prometheus, Oracle, Librarian, Explore)
- ✅ Slash commands work (`/start-work`, `/speckit.specify`, etc.)
- ✅ Multi-agent orchestration preserved
- ✅ Background task execution
- ✅ Session continuity

**Known Issues:**
- ⚠️ Language defaults to Chinese (browser auto-detect)
- **Fix:** User must manually change to English in web UI settings
- **Persistence:** Language choice stored in browser localStorage (per-device)
- **No server-side default** language configuration available

---

## Implementation Plan

### Phase 1: Add /dev/opencode Endpoint

**Goal:** Proxy OpenCode web through existing FastAPI app, similar to /dev/vscode

#### Step 1.1: Start OpenCode Web Service

**Create systemd service** (similar to ttyd-terminal):

**File:** `/home/dlybeck/.config/systemd/user/opencode-web.service`

```ini
[Unit]
Description=OpenCode Web Service
After=network.target

[Service]
Type=simple
WorkingDirectory=/home/dlybeck/Documents/portfolio
Environment="PATH=/home/dlybeck/.opencode/bin:/usr/local/bin:/usr/bin:/bin"
Environment="OPENCODE_SERVER_PASSWORD=<your-password>"
Environment="LANG=en_US.UTF-8"
Environment="LC_ALL=en_US.UTF-8"
ExecStart=/home/dlybeck/.opencode/bin/opencode web --port 4096 --hostname 0.0.0.0
Restart=always
RestartSec=10

[Install]
WantedBy=default.target
```

**Enable and start:**
```bash
systemctl --user daemon-reload
systemctl --user enable opencode-web
systemctl --user start opencode-web
systemctl --user status opencode-web
```

**Verify running:**
```bash
curl http://localhost:4096
```

#### Step 1.2: Create OpenCode Proxy Service

**File:** `services/opencode_web_proxy.py`

```python
"""
OpenCode Web HTTP and WebSocket Proxy
Inherits from BaseProxy to reuse connection logic
"""

from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class OpenCodeWebProxy(BaseProxy):
    """Reverse proxy for OpenCode web interface"""

    def __init__(self, opencode_url: str = None):
        if not opencode_url:
            if IS_CLOUD_RUN:
                opencode_url = f"http://{MAC_SERVER_IP}:4096"
            else:
                opencode_url = "http://127.0.0.1:4096"

        super().__init__(opencode_url)
        logger.info(f"OpenCode Web Proxy initialized: {opencode_url}")

    def _prepare_headers(self, request: Request):
        """Prepare headers for OpenCode web requests"""
        headers = super()._prepare_headers(request)
        # OpenCode web doesn't need special header modifications
        return headers

# Global instance
_proxy_instance = None

def get_opencode_proxy() -> OpenCodeWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenCodeWebProxy()
    return _proxy_instance
```

#### Step 1.3: Add OpenCode Routes

**File:** `apis/route_dev_opencode.py` (NEW)

```python
from fastapi import APIRouter, Request, HTTPException, WebSocket
from core.dev_utils import require_auth
from services.opencode_web_proxy import get_opencode_proxy

opencode_router = APIRouter(tags=["Dev OpenCode"])

@opencode_router.api_route("/opencode-proxy/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_opencode(request: Request, path: str):
    """Proxy HTTP requests to OpenCode web"""
    token = request.query_params.get("tkn") or request.cookies.get("session_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth.replace("Bearer ", "")
            
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    proxy = get_opencode_proxy()
    return await proxy.proxy_request(request, path)

@opencode_router.websocket("/opencode-proxy/{path:path}")
async def proxy_opencode_ws(websocket: WebSocket, path: str):
    """Proxy WebSocket connections to OpenCode web"""
    token = websocket.query_params.get("tkn") or websocket.cookies.get("session_token")
    if not token:
        await websocket.close(code=1008, reason="Missing authentication")
        return
        
    proxy = get_opencode_proxy()
    await proxy.proxy_websocket(websocket, path)
```

**File:** `apis/route_dev_pages.py` (MODIFY - add OpenCode page)

```python
# Add this route to existing file

@dev_pages_router.get("/opencode", response_class=HTMLResponse)
@require_auth
async def opencode_page(request: Request):
    return templates.TemplateResponse("dev/opencode.html", get_context(request))
```

#### Step 1.4: Create OpenCode Template

**File:** `templates/dev/opencode.html` (NEW)

```html
{% extends "shared/dev_base.html" %}

{% block page_title %}OpenCode - Dev Env{% endblock %}
{% block title %}OpenCode AI{% endblock %}

{% block navbar %}
{% endblock %}

{% block nav_links %}
<a href="/dev" class="nav-item">
    <span>🏠</span>
    <span class="desktop-only">Hub</span>
</a>
<a href="/dev/vscode" class="nav-item" onclick="event.preventDefault(); DevUtils.navigateTo('/dev/vscode')">
    <span>📁</span>
    <span class="desktop-only">VS Code</span>
</a>
{% endblock %}

{% block content %}
<style>
    .opencode-container {
        width: 100%;
        height: 100%;
        background: #1e1e1e;
    }
    iframe {
        border: none;
        width: 100%;
        height: 100%;
    }
</style>
<div class="opencode-container">
    <iframe id="opencode-iframe" src="/dev/opencode-proxy/?tkn={{ token }}"></iframe>
</div>
{% endblock %}
```

#### Step 1.5: Update Dev Router

**File:** `apis/route_dev.py` (MODIFY)

```python
from fastapi import APIRouter
from .route_dev_pages import dev_pages_router
from .route_dev_proxy import dev_proxy_router
from .route_dev_opencode import opencode_router  # NEW

dev_router = APIRouter(prefix="/dev", tags=["Dev Environment"])

dev_router.include_router(dev_pages_router)
dev_router.include_router(dev_proxy_router)
dev_router.include_router(opencode_router)  # NEW
```

#### Step 1.6: Update Dev Hub Page

**File:** `templates/dev/hub.html` (MODIFY - add OpenCode link)

```html
{% extends "shared/page.html" %}

{% block title %}
    <title>Dev | David Lybeck</title>
{% endblock %}

{% block content %}
<div class="container">
    <h2 id="location">Dev Environment</h2>

    <div class="section">
        <p>Remote development environment with secure access to VS Code, OpenCode AI, and Terminal.</p>
    </div>

    <!-- NEW SECTION -->
    <div class="section">
        <h3>🤖 OpenCode AI</h3>
        <p>AI-powered coding assistant with oh-my-opencode (omo) agents. Chat interface optimized for mobile and desktop.</p>
        <a class="link internal-link" href="/dev/opencode" target="_blank">Open OpenCode →</a>
    </div>

    <div class="section">
        <h3>📁 VS Code</h3>
        <p>Full persistent IDE for file editing, code browsing, and viewing images/complex files.</p>
        <a class="link internal-link" href="/dev/vscode" target="_blank">Open VS Code Editor →</a>
    </div>

    <div class="section">
        <h3>⌨️ Terminal</h3>
        <p>Persistent tmux sessions for long-running tasks, servers, and builds.</p>
        <a class="link internal-link" href="/dev/terminal" target="_blank">Open Terminal →</a>
    </div>
</div>
{% endblock %}
```

---

### Phase 2: Configure VS Code Persistence

**Goal:** Preserve open files, tabs, and settings across device switches

#### Step 2.1: Configure code-server User Data Directory

**Current Issue:**  
code-server stores workspace state in browser localStorage by default, which doesn't sync across devices.

**Solution:**  
Configure code-server to use server-side user-data-dir.

**Modify code-server startup** (if running as systemd service):

**File:** `/home/dlybeck/.config/systemd/user/code-server.service` (or wherever it's defined)

```ini
[Unit]
Description=code-server (VS Code in browser)
After=network.target

[Service]
Type=simple
Environment="PASSWORD=<your-password>"
ExecStart=/usr/bin/code-server \
  --bind-addr 0.0.0.0:8888 \
  --user-data-dir /home/dlybeck/.config/code-server \
  --workspace /home/dlybeck/Documents/portfolio \
  --auth password
Restart=always

[Install]
WantedBy=default.target
```

**Key flags:**
- `--user-data-dir`: Server-side storage for extensions, settings, UI state
- `--workspace`: Default workspace to open (your portfolio)
- `--auth password`: Use password auth (already configured)

**Apply changes:**
```bash
systemctl --user daemon-reload
systemctl --user restart code-server
```

#### Step 2.2: Enable Settings Sync (Optional)

If you want VS Code extensions/settings to sync server-side:

**In VS Code (browser):**
1. Open Settings (Gear icon)
2. Search for "Settings Sync"
3. Enable "Settings Sync"
4. Select what to sync: Settings, Keybindings, Extensions, UI State

This stores everything in `--user-data-dir`, accessible from any device.

#### Step 2.3: Verify Persistence

**Test:**
1. Open VS Code from Device A
2. Open several files, create tabs
3. Change a setting (e.g., theme)
4. Close browser
5. Open VS Code from Device B
6. **Expected:** Same files open, same settings

---

### Phase 3: Documentation

#### Step 3.1: Update DEPLOYMENT.md

**File:** `docs/DEPLOYMENT.md` (ADD section)

```markdown
## OpenCode Web Integration

### Architecture
```
Cloud Run Container
    ↓ SOCKS5 proxy
    ↓ Tailscale network
Ubuntu Server (100.82.216.64)
    ├─ code-server:8888 → /dev/vscode
    ├─ opencode web:4096 → /dev/opencode ⭐ NEW
    └─ ttyd:7681 → /dev/terminal
```

### Service Management

**OpenCode Web Service:**
```bash
# Status
systemctl --user status opencode-web

# Logs
journalctl --user -u opencode-web -f

# Restart
systemctl --user restart opencode-web
```

**Direct Access (for debugging):**
- Local: http://localhost:4096
- Network: http://100.82.216.64:4096

### Features
- AI coding assistance via browser
- oh-my-opencode (omo) agents: Sisyphus, Prometheus, Oracle, Librarian, Explore
- Session persistence across devices
- Mobile-optimized interface
- Real-time WebSocket updates

### Language Setting
- Default: Auto-detected by browser (may default to Chinese)
- **Fix:** Click settings icon in web UI → Change language to English
- **Persistence:** Per-browser localStorage (set once per device)
```

#### Step 3.2: Create User Guide

**File:** `docs/OPENCODE_WEB_USAGE.md` (NEW)

```markdown
# OpenCode Web Usage Guide

## Accessing OpenCode

1. Navigate to: https://your-domain.run.app/dev
2. Click "OpenCode AI" button
3. Login with your dev environment credentials

## First Time Setup

### Change Language to English
1. Click the settings/gear icon (top right)
2. Find "Language" or "语言" setting
3. Select "English"
4. Refresh page

This setting persists in your browser.

## Using omo Agents

OpenCode includes **oh-my-opencode (omo)** agents for advanced workflows:

### Available Agents
- **Sisyphus** - Main orchestrator, delegates work to specialists
- **Prometheus** - Planning and architecture agent
- **Oracle** - High-IQ reasoning for debugging/design
- **Librarian** - Documentation and external code search
- **Explore** - Codebase contextual search

### Slash Commands
- `/start-work` - Start Sisyphus work session
- `/speckit.specify` - Create feature specification
- `/speckit.plan` - Generate implementation plan
- `/speckit.tasks` - Generate task list
- `/speckit.implement` - Execute implementation

### Example Workflow

1. **Specify Feature:**
   ```
   /speckit.specify
   User: Add user authentication with JWT
   ```

2. **Generate Plan:**
   ```
   /speckit.plan
   ```

3. **Implement:**
   ```
   /speckit.implement
   ```

## Session Persistence

- **Chat history** persists on server
- **Switch devices** seamlessly - continue conversations anywhere
- **Background tasks** run even after disconnect

## Mobile Usage

### Optimized for Touch
- Large touch targets
- Swipe gestures
- Mobile keyboard support
- Responsive layout

### Tips
- Use VS Code for viewing images/files
- Use OpenCode for AI assistance
- Switch between tabs as needed

## VS Code Integration

### Open Files from OpenCode
When OpenCode suggests code changes:
1. Click file path link
2. Opens in VS Code tab
3. Edit, save, return to OpenCode

### Workflow
```
OpenCode (AI chat) ←→ VS Code (file editing)
      ↓
  Git commits
```

## Troubleshooting

### OpenCode not loading
```bash
# Check service status
ssh ubuntu-server
systemctl --user status opencode-web

# Check logs
journalctl --user -u opencode-web -f
```

### Session lost
- Sessions persist server-side
- If lost, check server restarted
- Sessions auto-cleanup after 24h idle

### Language reset to Chinese
- Browser localStorage issue
- Re-set language in settings
- Happens once per new browser/incognito
```

---

## Configuration Reference

### Environment Variables

**OpenCode Web Service:**
```bash
OPENCODE_SERVER_PASSWORD=<password>  # Required for network access
OPENCODE_SERVER_USERNAME=opencode    # Optional, defaults to 'opencode'
LANG=en_US.UTF-8                     # Attempt English locale (limited effect)
LC_ALL=en_US.UTF-8
```

**FastAPI Proxy:**
```python
# In services/opencode_web_proxy.py
OPENCODE_WEB_PORT = 4096
OPENCODE_WEB_HOST = "100.82.216.64" if IS_CLOUD_RUN else "127.0.0.1"
```

### Ports Summary

| Service | Port | Endpoint | Status |
|---------|------|----------|--------|
| FastAPI | 8080/8443 | /dev | ✅ Running |
| code-server | 8888 | /dev/vscode-proxy | ✅ Running |
| opencode web | 4096 | /dev/opencode-proxy | ⭐ NEW |
| ttyd | 7681 | /dev/terminal-proxy | ❌ SOCKS5 error (optional) |

---

## Pros & Cons

### Advantages

✅ **Official Solution**
- Built into OpenCode, maintained by core team
- No third-party dependencies

✅ **Full omo Compatibility**
- All agents work (Sisyphus, Prometheus, Oracle, etc.)
- Slash commands preserved
- Multi-agent orchestration intact

✅ **Mobile Optimized**
- Responsive design
- Touch-friendly
- Better than terminal UI

✅ **Session Persistence**
- Server-side storage
- Cross-device continuity
- Background task execution

✅ **Easy Integration**
- Simple proxy setup (same pattern as VS Code)
- Reuses existing auth
- Minimal code changes

✅ **User Approved**
- Tested and loved by user
- "So clean actually I love it"

### Disadvantages

⚠️ **Language Default**
- Auto-detects browser language (may be Chinese)
- Must manually change to English per browser
- No server-side override available

⚠️ **Additional Service**
- Another systemd service to manage
- Another port to expose (4096)
- Slightly more memory usage

⚠️ **Browser Dependency**
- Requires modern browser with WebSocket support
- No offline mode
- Network-dependent

---

## Testing Checklist

### Phase 1: OpenCode Web Service
- [ ] systemd service starts successfully
- [ ] `curl http://localhost:4096` returns HTTP 200
- [ ] Web interface loads in browser
- [ ] omo agents visible (Sisyphus, Prometheus, etc.)
- [ ] Can start new chat session
- [ ] WebSocket connection stable
- [ ] Language changeable to English

### Phase 2: FastAPI Proxy
- [ ] `/dev/opencode` page loads
- [ ] Authentication required
- [ ] iframe loads OpenCode web interface
- [ ] Chat works through proxy
- [ ] WebSocket proxy functional
- [ ] Token auth works (tkn parameter)

### Phase 3: VS Code Persistence
- [ ] Open files persist after browser close
- [ ] Settings persist across devices
- [ ] Extensions installed server-side
- [ ] Workspace state saved
- [ ] Git state visible

### Phase 4: Mobile Testing
- [ ] Interface loads on mobile
- [ ] Touch targets appropriate size
- [ ] Keyboard input works
- [ ] Scrolling smooth
- [ ] Can switch between VS Code and OpenCode

### Phase 5: Cross-Device Testing
- [ ] OpenCode session continues from phone to desktop
- [ ] VS Code shows same open files across devices
- [ ] Authentication persists appropriately
- [ ] No data loss on device switch

---

## Maintenance

### Regular Tasks

**Weekly:**
- Check service status: `systemctl --user status opencode-web`
- Review logs for errors: `journalctl --user -u opencode-web --since "7 days ago"`

**Monthly:**
- Update OpenCode: `opencode upgrade`
- Check omo plugin updates: `opencode config get plugin`
- Verify disk space: `df -h ~/.opencode`

**As Needed:**
- Restart after crashes: `systemctl --user restart opencode-web`
- Clear old sessions: OpenCode auto-cleans 24h idle sessions

### Troubleshooting Commands

```bash
# Check all dev services
systemctl --user status code-server
systemctl --user status opencode-web
systemctl --user status ttyd-terminal

# Check ports
ss -tlnp | grep -E "8888|4096|7681"

# Test direct access
curl http://localhost:4096
curl http://localhost:8888

# Check proxy from Cloud Run
# (requires Cloud Run context)
curl http://100.82.216.64:4096
```

---

## Alternative Solutions Considered

### 1. Custom OpenCode Web UI
**Rejected:** Too much work, maintenance burden, duplicates official feature

### 2. Third-Party Apps (Remote Code, openMode)
**Rejected:** Requires user app install, not web-based

### 3. Enhanced Terminal + TUI
**Rejected:** Terminal UX inferior to web on mobile, user wanted button-based UI

### 4. opencode-web (chris-tse's React UI)
**Rejected:** Separate deployment, less mature than official OpenCode web

---

## Future Enhancements

### Potential Improvements

1. **Custom Landing Page**
   - Show recent sessions
   - Quick action buttons
   - Recent files from VS Code

2. **Unified Auth**
   - Single login for all /dev services
   - SSO across OpenCode and VS Code

3. **Mobile PWA**
   - Install as app on phone
   - Offline mode
   - Push notifications for task completion

4. **Split View**
   - VS Code + OpenCode side-by-side
   - Drag-and-drop between interfaces

5. **Language Override**
   - Server-side English default
   - Requires upstream OpenCode feature request

---

## References

- **OpenCode Docs:** https://opencode.ai/docs/web/
- **oh-my-opencode:** https://github.com/code-yeongyu/oh-my-opencode
- **Your OpenCode Config:** `~/.config/opencode/opencode.json`
- **Test Instance:** http://100.82.216.64:4096 (Ubuntu server)

---

## Summary

### What Works
✅ OpenCode web + omo fully compatible  
✅ Mobile-friendly interface approved by user  
✅ Clear implementation path with existing patterns  
✅ Session persistence built-in  
✅ VS Code persistence via user-data-dir  

### What's Left
📋 Implement proxy in FastAPI app  
📋 Create systemd service for opencode web  
📋 Configure VS Code persistence  
📋 Update documentation  
📋 Test cross-device workflow  

### Estimated Effort
- **Phase 1 (OpenCode proxy):** 1-2 hours
- **Phase 2 (VS Code persistence):** 30 minutes
- **Phase 3 (Documentation):** 30 minutes
- **Testing:** 1 hour
- **Total:** ~3-4 hours

### Risk Level
**LOW** - Following proven patterns (VS Code proxy), official OpenCode feature, user-tested.

---

**Status:** Ready for implementation when you are! 🚀
