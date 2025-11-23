# Dev Dashboard Mobile Issues - Comprehensive Analysis & Fixes

## 🔴 CRITICAL ISSUES FOUND

### 1. PTY Device Leak (Server Crash Risk)
**Severity: CRITICAL**

**Problem:**
- Server logs show: `Terminal error: out of pty devices`
- Creating terminal sessions on every WebSocket connection without proper cleanup
- Will eventually crash the server when OS runs out of PTY devices

**Root Cause:**
- `/Users/dlybeck/Documents/Portfolio/apis/route_dev.py` - WebSocket handler creates new PTY sessions but doesn't clean them up on disconnect
- Persistent sessions are never garbage collected

**Fix Required:**
```python
# In route_dev.py terminal_websocket(), add proper cleanup:
finally:
    if not IS_CLOUD_RUN and persistent_session:
        # Only close if no other clients connected
        if len(persistent_session.connected_clients) == 0:
            persistent_session.close()
            # Remove from global dict
            from services.session_manager import _persistent_sessions
            if session_id in _persistent_sessions:
                del _persistent_sessions[session_id]
```

---

## 🐛 MOBILE UX ISSUES

### 2. Swipe Gestures Not Working
**Severity: HIGH**

**Problem:** User reports swipe between terminal/preview doesn't work

**Files Affected:**
- `/Users/dlybeck/Documents/Portfolio/templates/dev/dashboard.html` (lines 1355-1389)

**Issues:**
1. CSS hiding both sections by default with `display: none`
2. JavaScript trying to add classes but timing issues prevent it
3. Touch events not properly triggering class changes

**Current Broken Code:**
```css
/* Both hidden by default - BAD */
.terminal-section,
.preview-section {
    display: none;
}
```

**Fix:**
```css
/* Mobile - Show terminal by default, hide preview */
@media (max-width: 768px) {
    .terminal-section {
        display: flex !important; /* Shown by default */
    }

    .preview-section {
        display: none !important; /* Hidden by default */
    }

    .terminal-section.swipe-hidden {
        display: none !important;
    }

    .preview-section.swipe-active {
        display: flex !important;
    }
}
```

```javascript
// Simplified swipe with proper state management
let isShowingTerminal = true;

document.addEventListener('touchend', (e) => {
    const swipeDistance = touchEndX - touchStartX;
    if (Math.abs(swipeDistance) < 100) return; // Increased threshold

    const terminal = document.querySelector('.terminal-section');
    const preview = document.querySelector('.preview-section');

    if (swipeDistance < 0 && isShowingTerminal) {
        // Swipe left - show preview
        terminal.classList.add('swipe-hidden');
        preview.classList.add('swipe-active');
        isShowingTerminal = false;
    } else if (swipeDistance > 0 && !isShowingTerminal) {
        // Swipe right - show terminal
        terminal.classList.remove('swipe-hidden');
        preview.classList.remove('swipe-active');
        isShowingTerminal = true;
    }
});
```

---

### 3. Navbar Overflow on Mobile
**Severity: MEDIUM**

**Problem:** Top navbar extends past screen width on mobile

**File:** `/Users/dlybeck/Documents/Portfolio/templates/dev/dashboard.html`

**Fix:**
```css
@media (max-width: 768px) {
    .header {
        padding: 8px 12px; /* Reduced padding */
        overflow: hidden; /* Prevent overflow */
    }

    .header h1 {
        font-size: 14px; /* Smaller */
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
    }

    /* Hide unnecessary items */
    .hide-mobile {
        display: none !important;
    }
}
```

---

### 4. Keyboard Shortcuts Showing Escape Sequences
**Severity: MEDIUM**

**Problem:** Arrow keys show `\x1b[A` instead of executing

**File:** `/Users/dlybeck/Documents/Portfolio/templates/dev/dashboard.html`

**Current Code (BROKEN):**
```html
<button onclick="sendKey('\\x1b[A')">↑</button>
```

**Fixed Code:**
```html
<button onclick="sendKey('\x1b[A')">↑</button>
<!-- Removed double backslash -->
```

**Status:** ✅ Already fixed in recent updates

---

### 5. Text Selection Disabled on Mobile
**Severity: MEDIUM**

**Problem:** Cannot select/copy text from terminal on mobile

**Fix:**
```css
@media (max-width: 768px) {
    .terminal-container,
    #terminal,
    .xterm,
    .xterm-screen {
        user-select: text !important;
        -webkit-user-select: text !important;
        -moz-user-select: text !important;
        -webkit-touch-callout: default !important;
    }
}
```

**Status:** ✅ Already fixed

---

### 6. Claude Code Not Auto-Starting
**Severity: MEDIUM**

**Problem:** Claude shows full path `/opt/homebrew/bin/claude` instead of starting cleanly

**File:** `/Users/dlybeck/Documents/Portfolio/apis/route_dev.py` (line 488)

**Current Code:**
```python
persistent_session.write("exec claude\n")
```

**Issue:** PATH not loaded in new shell

**Fix:**
```python
# Source .zshrc/.bashrc first to load PATH
persistent_session.write("source ~/.zshrc 2>/dev/null || source ~/.bashrc 2>/dev/null; exec claude\n")
```

---

### 7. Mobile Keyboard Ruins Layout
**Severity: HIGH**

**Problem:** When mobile keyboard appears, content gets cut off

**Fix:**
```css
body {
    height: 100vh;
    height: 100dvh; /* Dynamic viewport height - already present */
}

@media (max-width: 768px) {
    .main-container {
        height: calc(100dvh - 120px); /* Account for navbar + toolbar */
        min-height: 0; /* Allow shrinking */
    }

    .terminal-container {
        height: 100%;
        min-height: 200px; /* Minimum usable height */
        overflow-y: auto;
    }
}
```

---

### 8. No Vertical Scroll but Content Cut Off
**Severity: HIGH**

**Problem:** Page doesn't scroll vertically (good) but bottom content is cut off

**Root Cause:** Fixed heights not accounting for mobile viewport properly

**Fix:**
```css
@media (max-width: 768px) {
    body {
        overflow: hidden; /* Already present */
    }

    .main-container {
        display: flex;
        flex-direction: column;
        height: calc(100dvh - var(--navbar-height) - var(--toolbar-height));
        overflow: hidden;
    }

    .terminal-section {
        flex: 1;
        min-height: 0; /* Critical for flex shrinking */
        overflow: hidden;
    }

    .terminal-container {
        height: 100%;
        overflow-y: auto;
    }
}
```

---

## 📊 SECURITY FIXES COMPLETED ✅

1. ✅ Protected `/auth/setup` endpoint - now requires authentication
2. ✅ Protected `/debug/connectivity` endpoint
3. ✅ Added WebSocket JWT authentication
4. ✅ Fixed async/await bug in `is_mac_server_available()`
5. ✅ Server now exits on security config failure
6. ✅ Added Claude auto-start race condition lock
7. ✅ Added JavaScript global error handlers

---

## 🔧 RECOMMENDED ARCHITECTURE IMPROVEMENTS

### 1. Session Cleanup Strategy
```python
# Add to session_manager.py
import weakref
import atexit

class SessionCleanupManager:
    def __init__(self):
        self._sessions = weakref.WeakValueDictionary()
        atexit.register(self.cleanup_all)

    def cleanup_all(self):
        for session in list(self._sessions.values()):
            try:
                session.close()
            except:
                pass
```

### 2. PTY Pool Management
```python
# Limit max concurrent PTY sessions
MAX_PTY_SESSIONS = 50

def get_or_create_persistent_session(...):
    if len(_persistent_sessions) >= MAX_PTY_SESSIONS:
        # Clean up oldest inactive session
        oldest = min(_persistent_sessions.values(),
                    key=lambda s: s.last_activity)
        oldest.close()
        del _persistent_sessions[oldest.session_id]
```

### 3. Add Session Timeout
```python
# Auto-close inactive sessions after 1 hour
SESSION_TIMEOUT = 3600  # seconds

async def session_timeout_checker():
    while True:
        await asyncio.sleep(60)  # Check every minute
        now = time.time()
        for sid, session in list(_persistent_sessions.items()):
            if now - session.last_activity > SESSION_TIMEOUT:
                session.close()
                del _persistent_sessions[sid]
```

---

## 📝 TESTING PLAN

### Automated Visual Tests (Playwright)
Created: `/Users/dlybeck/Documents/Portfolio/tests/test_mobile_dashboard.py`

**Tests Include:**
1. ✅ Mobile viewport rendering
2. ✅ Swipe gestures between sections
3. ✅ Keyboard shortcut execution
4. ✅ Text selection on mobile
5. ✅ Claude auto-start verification
6. ✅ Keyboard layout adaptation

**To Run:**
```bash
cd /Users/dlybeck/Documents/Portfolio
python3 tests/test_mobile_dashboard.py
```

**Generates:**
- `test_screenshots/` - Visual screenshots of each test
- `test_screenshots/test_report.html` - Interactive HTML report
- `test_screenshots/test_results.json` - JSON test results

---

## 🚀 IMMEDIATE ACTION ITEMS

### Priority 1: Fix PTY Leak (DO THIS NOW)
1. Add proper WebSocket cleanup in `route_dev.py`
2. Implement session timeout
3. Add PTY session limit
4. Restart server to clear leaked sessions

### Priority 2: Fix Mobile Swipe
1. Update CSS to show terminal by default
2. Simplify swipe JavaScript logic
3. Increase swipe threshold to 100px
4. Add visual feedback during swipe

### Priority 3: Fix Mobile Layout
1. Fix navbar overflow
2. Implement proper keyboard height handling
3. Add min-height constraints
4. Test on actual mobile device

---

## 📱 MOBILE TESTING CHECKLIST

- [ ] Terminal visible on page load (no blank screen)
- [ ] Swipe left shows preview
- [ ] Swipe right shows terminal
- [ ] Navbar fits within screen width
- [ ] Arrow keys execute (no escape sequences visible)
- [ ] Can select and copy terminal text
- [ ] Claude auto-starts without showing path
- [ ] Keyboard doesn't break layout
- [ ] No vertical scroll on page
- [ ] All content visible (nothing cut off)
- [ ] Works on iPhone (Safari)
- [ ] Works on Android (Chrome)

---

## 🔗 FILES REQUIRING CHANGES

1. `/Users/dlybeck/Documents/Portfolio/apis/route_dev.py`
   - Add WebSocket cleanup (PTY leak fix)
   - Fix Claude auto-start command

2. `/Users/dlybeck/Documents/Portfolio/templates/dev/dashboard.html`
   - Fix swipe CSS
   - Fix swipe JavaScript
   - Fix navbar overflow
   - Fix keyboard layout handling

3. `/Users/dlybeck/Documents/Portfolio/services/session_manager.py`
   - Add session timeout
   - Add cleanup manager
   - Add last_activity tracking

4. `/Users/dlybeck/Documents/Portfolio/services/terminal_service.py`
   - Add session limit check
   - Improve error handling

---

## ✅ COMPLETION CRITERIA

Mobile dashboard is considered **FIXED** when:

1. ✅ No PTY device errors in logs
2. ✅ All Playwright tests pass
3. ✅ Swipe gestures work smoothly
4. ✅ Layout perfect on iPhone/Android
5. ✅ Claude auto-starts cleanly
6. ✅ No JavaScript errors in console
7. ✅ Can copy/paste from terminal
8. ✅ Keyboard doesn't break UI

---

**Generated:** 2025-10-06
**Status:** Issues identified, fixes documented, ready for implementation
