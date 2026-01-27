# Draft: Mobile-Friendly Remote Development

## User Requirements (Confirmed)

### Core Issues
1. **Terminal broken**: SOCKS5 error, not accessible (Tailscale proxy issue in Cloud Run)
2. **VS Code loses state**: Open files/tabs not persisting when switching devices
3. **Mobile UX poor**: OpenCode needs button-based mobile interface, not just keyboard tricks
4. **File viewing needs**: VS Code essential for images, complex files (TUI can't handle)

### Desired State Persistence (ALL of these)
- ✅ VS Code open files/tabs
- ✅ VS Code extensions/settings (server-side, no cloud)
- ✅ OpenCode chat history
- ✅ Terminal command history
- ✅ Git state / file changes
- ✅ Running processes (tmux already handles)

### User Preferences
- **VS Code sync**: Server-side persistence only (no Microsoft/GitHub account)
- **Mobile support**: Button-focused UI for OpenCode interactions, not complex keyboard toolbar
- **File management**: VS Code for viewing images/complex files (TUI insufficient)
- **Platforms**: Android (primary), iOS (potential), Desktop (yes)
- **Interface**: Both VS Code and Terminal, not sure which primary yet

---

## Current Architecture (What Works)

```
Cloud Run Container (Tailscale)
    ↓ SOCKS5 proxy (localhost:1055)
    ↓ Tailscale network
Ubuntu Server (100.82.216.64)
    ├─ code-server:8888 → /dev/vscode
    ├─ ttyd:7681 → /dev/terminal (BROKEN - SOCKS5 error)
    └─ tmux sessions (OpenCode runs here)
```

### What's Working
✅ VS Code proxy (`/dev/vscode-proxy`) - accessible
✅ Authentication (TOTP/JWT)
✅ tmux sessions persist
✅ OpenCode runs in tmux
✅ Mobile keyboard toolbar exists (but not what user wants)

### What's Broken
❌ Terminal proxy (`/dev/terminal-proxy`) - SOCKS5 error
❌ VS Code workspace state not persisting across devices
❌ No mobile-optimized UI for OpenCode
❌ Can't view OpenCode chat from mobile easily

---

## Technical Findings

### 1. Terminal SOCKS5 Error (Priority: HIGH)

**Location**: `services/terminal_proxy.py`
```python
if IS_CLOUD_RUN:
    terminal_url = f"http://{MAC_SERVER_IP}:7681/dev/terminal-proxy"
```

**Likely Causes**:
- ttyd not listening on 0.0.0.0 (only localhost)
- SOCKS5 proxy not routing ttyd correctly
- Tailscale firewall blocking port 7681
- ttyd systemd service not running

**Diagnostic Steps Needed**:
1. Check ttyd systemd service status on Ubuntu
2. Verify ttyd bind address (must be 0.0.0.0:7681)
3. Test SOCKS5 connection to port 7681 from Cloud Run
4. Check Tailscale ACL rules

### 2. VS Code State Persistence

**Current Setup**:
- code-server runs with no explicit workspace persistence
- Default behavior: state tied to browser storage (not server-side)

**Solution Options**:

**A. User Data Directory (Recommended)**
```bash
# Configure code-server with persistent user-data-dir
code-server \
  --bind-addr 0.0.0.0:8888 \
  --user-data-dir /home/dlybeck/.config/code-server \
  --workspace /home/dlybeck/Documents/portfolio
```

**Benefits**:
- Open tabs persist across browser sessions
- Extensions stored on server
- Settings synchronized server-side
- No cloud dependency

**B. Workspace State File**
- code-server auto-saves workspace state to `.vscode/`
- Need to ensure workspace folder specified on launch

### 3. Mobile-Optimized OpenCode UI

**User Vision**: Button-based interface for OpenCode chat/interactions

**Current Gap**:
- OpenCode is CLI-only (terminal-based chat)
- No web UI exists for OpenCode
- Mobile users stuck with terminal keyboard

**Solution Approaches**:

**Option A: Custom Web UI for OpenCode**
- Build React/Vue interface
- Connect to OpenCode via API or stdio
- Button-based actions: "Explain code", "Fix bug", "Write test", "Refactor"
- Chat history persisted to server
- Mobile-first design

**Option B: Wrap OpenCode Terminal in Mobile-Friendly UI**
- Keep OpenCode in terminal (tmux)
- Add web layer with:
  - Quick action buttons
  - Touch-optimized chat input
  - Code snippet display
  - File selection UI
- Terminal visible but enhanced

**Option C: OpenCode API Integration**
- Investigate if OpenCode has HTTP API
- Build lightweight mobile frontend
- Direct API calls, no terminal needed

**Research Needed**:
- Does OpenCode expose an API?
- Can we intercept OpenCode stdio?
- What's the best architecture for mobile UI?

### 4. File Viewing in VS Code

**Already Works**: VS Code handles images, PDFs, etc.

**Enhancement Ideas**:
- Preview pane for images in mobile view
- Larger touch targets for file explorer
- Swipe gestures for file navigation

---

## OpenCode Mobile Solutions (Research Findings)

### Built-in OpenCode Web Interface ✅
```bash
opencode web --port 4096 --hostname 0.0.0.0
```
- **Official OpenCode feature** - run as web server
- Browser-based UI (not just terminal)
- Can bind to network address for remote access
- Supports authentication (OPENCODE_SERVER_PASSWORD)
- Can attach TUI with `opencode attach http://server:4096`

**Pros:**
- ✅ Official, maintained by OpenCode team
- ✅ Already mobile-optimized web interface
- ✅ Session persistence via server
- ✅ Chat history saved server-side

**Cons:**
- ❌ Requires OpenCode running as web service
- ❌ Need to expose port or proxy through existing /dev endpoint

### Third-Party Mobile Apps

**1. Remote Code (remote-code.com)**
- Native iPhone app (TestFlight)
- Connects to OpenCode backend via "Uplink" client
- Gesture-based navigation
- Git integration built-in
- Mobile-optimized keyboard

**2. openMode (github.com/easychen/openMode)**
- Flutter-based mobile app
- 64 stars on GitHub
- Android/iOS support
- Open source

**3. opencode-web (github.com/chris-tse/opencode-web)**
- React-based web UI
- 76 stars on GitHub
- Mobile-responsive design
- Chat interface with file explorer

### Community Requests (Not Yet Built)
- GitHub Issue #6536: Official mobile app (requested Dec 2025)
- GitHub Issue #5126: Mobile-friendly web UI improvements

---

## Solution Comparison for Your Setup

| Solution | Persistence | Mobile UX | Setup Effort | Fits Your Stack |
|----------|-------------|-----------|--------------|-----------------|
| **OpenCode Web (Official)** | ✅ Server-side | ✅ Good | LOW | ✅ Perfect fit |
| **Remote Code App** | ✅ Yes | ✅ Excellent | MEDIUM | ⚠️ Requires Uplink install |
| **opencode-web** | ✅ Yes | ✅ Good | HIGH | ⚠️ Separate deployment |
| **Current tmux + ttyd** | ✅ Yes | ❌ Poor (terminal only) | DONE | ✅ Already working (but broken SOCKS5) |

---

## Open Questions

1. **Terminal Debug**: Need to diagnose exact SOCKS5 error
   - Check ttyd service on Ubuntu
   - Verify SOCKS5 proxy routing
   - Test direct connection vs proxy

2. **OpenCode Mobile Strategy**: User doesn't want custom UI
   - **Option A**: Integrate `opencode web` into /dev endpoint (LOW effort, official)
   - **Option B**: Fix existing tmux terminal + better TUI (already done, just needs SOCKS5 fix)
   - **Option C**: Third-party app (Remote Code, openMode) - user install required

3. **VS Code Workspace**: Verify current persistence behavior
   - Check if code-server already saves workspace state
   - Test switching devices with current setup
   - Identify what specifically is lost

---

## Next Steps

1. **Diagnose terminal SOCKS5 error** (blocking issue)
2. **Research OpenCode API/integration options** (mobile UI architecture)
3. **Configure VS Code user-data-dir** (persistence fix)
4. **Design mobile OpenCode UI** (button-based interface)

---

## Implementation Complexity Estimate

| Component | Effort | Priority |
|-----------|--------|----------|
| Fix terminal SOCKS5 error | LOW | HIGH |
| VS Code workspace persistence | LOW | HIGH |
| Mobile keyboard toolbar (existing) | DONE | N/A (user wants different solution) |
| OpenCode mobile web UI | HIGH | HIGH |
| TUI file manager | N/A | N/A (VS Code sufficient) |

---

## User Decisions Still Needed

- [ ] For OpenCode mobile UI: Custom web app vs enhanced terminal wrapper?
- [ ] Should OpenCode mobile UI replace terminal entirely, or supplement it?
- [ ] Any specific OpenCode actions to prioritize for mobile buttons?
