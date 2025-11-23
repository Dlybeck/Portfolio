# Dev Dashboard V2 - Implementation Plan
**Based on Questionnaire Responses**

## 📋 Executive Summary

**Chosen Architecture:** Alpine.js (Option C)

**Why Alpine.js:**
- ✅ Lightweight (15KB gzipped) - won't impact mobile performance
- ✅ No build process needed - simpler deployment
- ✅ Reactive state management - fixes current state chaos
- ✅ Declarative syntax - easier to maintain
- ✅ Progressive enhancement - works with existing HTML
- ✅ Perfect for dashboards - designed for this use case

**Timeline:** 2-3 days for core v2, +2 days for cross-device sync

---

## 🎯 User Requirements Addressed

| Requirement | Solution |
|-------------|----------|
| **Primary Use**: Terminal access on mobile | Mobile-first design with optimized touch |
| **Device Priority**: Android Chrome #1 | Chrome-specific optimizations, progressive enhancement |
| **Navigation**: Swipe gestures | Enhanced swipe with Alpine x-swipe directive |
| **Toolbar**: Essential on mobile | Context-aware toolbar with multiple pages |
| **Dream**: Cross-device sync | WebSocket-based session sync (Phase 3) |
| **Theme**: davidlybeck.com style | CSS variables for theming, dark/light preserved |

---

## 📦 Phase 2: Alpine.js Core Refactor (2-3 days)

### Step 1: Setup Alpine.js (30 mins)

**Files to modify:**
- `templates/dev/dashboard.html`

**Changes:**
```html
<!-- Add before closing </head> -->
<script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
```

**Why this approach:**
- CDN version = no build tools needed
- Defer = non-blocking load
- Alpine 3.x = latest stable, great mobile support

---

### Step 2: Split Monolithic File (2-3 hours)

**Current:** 1,565 lines in one file
**Target:** Modular structure

**New Structure:**
```
templates/dev/
├── dashboard.html              # 150 lines (Alpine components)
├── components/
│   ├── terminal-view.html      # Terminal component
│   ├── preview-view.html       # Preview component
│   └── toolbar.html            # Keyboard toolbar
└── static/dev/
    ├── css/
    │   ├── dashboard.css       # Base styles (300 lines)
    │   ├── mobile.css          # Mobile-first (200 lines)
    │   └── desktop.css         # Desktop enhancements (100 lines)
    └── js/
        ├── alpine-store.js     # Centralized state
        ├── terminal.js         # xterm.js logic
        ├── websocket.js        # WebSocket handler
        └── gestures.js         # Touch gestures
```

**Migration Strategy:**
1. Extract CSS to separate files
2. Extract JS to modules
3. Convert HTML sections to Alpine components
4. Test each piece individually

---

### Step 3: Create Alpine Data Store (1 hour)

**File:** `static/dev/js/alpine-store.js`

```javascript
document.addEventListener('alpine:init', () => {
    Alpine.store('dashboard', {
        // View state
        currentView: 'terminal',  // 'terminal' | 'preview'

        // Toolbar state
        toolbarPage: 0,
        toolbarPages: [
            ['↑', '↓', '←', '→', 'Tab', 'Esc', 'Ctrl+C'],
            ['Ctrl+D', 'Ctrl+Z', 'Ctrl+L', 'Clear', '/', 'Enter']
        ],

        // Connection state
        wsConnected: false,
        macServerOnline: false,

        // Terminal state
        terminalReady: false,
        workingDir: '/Users/dlybeck/Documents/Portfolio',

        // Methods
        switchView(view) {
            if (view === 'terminal' || view === 'preview') {
                this.currentView = view;
                this.vibrate(10);
            }
        },

        nextToolbarPage() {
            this.toolbarPage = (this.toolbarPage + 1) % this.toolbarPages.length;
        },

        prevToolbarPage() {
            this.toolbarPage = Math.max(0, this.toolbarPage - 1);
        },

        vibrate(ms) {
            if (navigator.vibrate) {
                navigator.vibrate(ms);
            }
        }
    });
});
```

**Why This Works:**
- Single source of truth
- Reactive - UI updates automatically
- Easy to debug - all state in one place
- Testable - can be mocked

---

### Step 4: Rebuild Main HTML with Alpine (2 hours)

**File:** `templates/dev/dashboard.html`

**New Structure:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Dev Dashboard</title>

    <!-- CSS -->
    <link rel="stylesheet" href="/static/dev/css/dashboard.css">
    <link rel="stylesheet" href="/static/dev/css/mobile.css">
    <link rel="stylesheet" href="/static/dev/css/desktop.css">

    <!-- Alpine.js -->
    <script defer src="https://cdn.jsdelivr.net/npm/alpinejs@3.13.3/dist/cdn.min.js"></script>
    <script src="/static/dev/js/alpine-store.js"></script>
</head>

<body
    x-data
    :data-view="$store.dashboard.currentView"
    x-init="init()"
>
    <!-- Header -->
    <header class="header">
        <h1>Claude Code</h1>
        <div class="status">
            <span
                class="status-dot"
                :class="$store.dashboard.wsConnected ? 'online' : 'offline'"
            ></span>
            <span x-text="$store.dashboard.wsConnected ? 'Connected' : 'Connecting...'"></span>
        </div>
    </header>

    <!-- Main Container with Swipe -->
    <main
        class="main-container"
        x-data="swipeHandler()"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
    >
        <!-- Terminal View -->
        <section
            class="terminal-section"
            x-show="$store.dashboard.currentView === 'terminal'"
            x-transition:enter="slide-in-right"
            x-transition:leave="slide-out-left"
        >
            <div id="terminal"></div>
        </section>

        <!-- Preview View -->
        <section
            class="preview-section"
            x-show="$store.dashboard.currentView === 'preview'"
            x-transition:enter="slide-in-left"
            x-transition:leave="slide-out-right"
        >
            <iframe
                id="preview-frame"
                src="about:blank"
                x-bind:src="previewUrl"
            ></iframe>
        </section>

        <!-- Swipe Hint (shows briefly on load) -->
        <div
            class="swipe-hint"
            x-data="{ show: true }"
            x-show="show"
            x-init="setTimeout(() => show = false, 3000)"
        >
            ← Swipe →
        </div>
    </main>

    <!-- Keyboard Toolbar (Mobile Only) -->
    <div
        class="toolbar"
        x-data="toolbarHandler()"
        x-show="window.innerWidth <= 768"
    >
        <!-- Toolbar Page Indicator -->
        <div class="toolbar-pages">
            <template x-for="(page, idx) in $store.dashboard.toolbarPages" :key="idx">
                <span
                    class="page-dot"
                    :class="idx === $store.dashboard.toolbarPage ? 'active' : ''"
                    @click="$store.dashboard.toolbarPage = idx"
                ></span>
            </template>
        </div>

        <!-- Toolbar Buttons -->
        <div class="toolbar-buttons">
            <template x-for="key in $store.dashboard.toolbarPages[$store.dashboard.toolbarPage]">
                <button
                    @click="sendKey(key)"
                    x-text="key"
                ></button>
            </template>
        </div>

        <!-- Toolbar Swipe Navigation -->
        <div
            class="toolbar-nav"
            @touchstart="onToolbarTouchStart"
            @touchmove="onToolbarTouchMove"
            @touchend="onToolbarTouchEnd"
        ></div>
    </div>

    <!-- Scripts -->
    <script src="/static/dev/js/terminal.js"></script>
    <script src="/static/dev/js/websocket.js"></script>
    <script src="/static/dev/js/gestures.js"></script>
    <script>
        function init() {
            // Initialize terminal
            initTerminal();
            // Connect WebSocket
            connectWebSocket();
        }
    </script>
</body>
</html>
```

**Key Alpine Features Used:**
- `x-data` - Component scope
- `x-show` - Conditional visibility (reactive)
- `x-transition` - Smooth animations
- `x-bind:class` / `:class` - Dynamic classes
- `x-text` - Text binding
- `@click` / `@touchstart` - Event handlers
- `$store` - Global state access
- `x-init` - Initialization hooks

---

### Step 5: Mobile-First CSS (2 hours)

**File:** `static/dev/css/mobile.css`

**Strategy:** Base styles for mobile, override for desktop

```css
/* Mobile Base (default) */
:root {
    --header-height: 60px;
    --toolbar-height: 100px;
    --main-height: calc(100dvh - var(--header-height) - var(--toolbar-height));
}

body {
    margin: 0;
    padding: 0;
    overflow: hidden;
    height: 100dvh;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}

.main-container {
    height: var(--main-height);
    position: relative;
    overflow: hidden;
}

.terminal-section,
.preview-section {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
}

/* Alpine transitions */
.slide-in-right {
    animation: slideInRight 0.3s ease-out;
}

.slide-out-left {
    animation: slideOutLeft 0.3s ease-out;
}

@keyframes slideInRight {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

@keyframes slideOutLeft {
    from {
        transform: translateX(0);
        opacity: 1;
    }
    to {
        transform: translateX(-100%);
        opacity: 0;
    }
}

/* Toolbar */
.toolbar {
    position: fixed;
    bottom: 0;
    left: 0;
    right: 0;
    height: var(--toolbar-height);
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-color);
    display: flex;
    flex-direction: column;
    z-index: 1000;
}

.toolbar-buttons {
    display: flex;
    gap: 8px;
    padding: 12px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
}

.toolbar-buttons button {
    flex-shrink: 0;
    padding: 12px 16px;
    border: 1px solid var(--border-color);
    background: var(--bg-primary);
    color: var(--text-primary);
    border-radius: 8px;
    font-size: 14px;
    white-space: nowrap;
    cursor: pointer;
    touch-action: manipulation;
}

.toolbar-buttons button:active {
    transform: scale(0.95);
    background: var(--accent-color);
}
```

**File:** `static/dev/css/desktop.css`

```css
/* Desktop Enhancements */
@media (min-width: 769px) {
    .toolbar {
        display: none; /* Hide on desktop */
    }

    .main-container {
        height: calc(100vh - var(--header-height));
        display: grid;
        grid-template-columns: 1fr 1fr; /* Side-by-side */
    }

    .terminal-section,
    .preview-section {
        position: static; /* Not absolute on desktop */
    }

    .swipe-hint {
        display: none; /* No swipe on desktop */
    }
}
```

---

### Step 6: Enhanced Swipe Gestures (1 hour)

**File:** `static/dev/js/gestures.js`

```javascript
function swipeHandler() {
    return {
        touchStartX: 0,
        touchStartY: 0,
        touchCurrentX: 0,
        touchCurrentY: 0,
        isSwiping: false,

        onTouchStart(e) {
            if (window.innerWidth > 768) return;

            this.touchStartX = e.touches[0].clientX;
            this.touchStartY = e.touches[0].clientY;
            this.isSwiping = false;
        },

        onTouchMove(e) {
            if (window.innerWidth > 768) return;

            this.touchCurrentX = e.touches[0].clientX;
            this.touchCurrentY = e.touches[0].clientY;

            const deltaX = Math.abs(this.touchCurrentX - this.touchStartX);
            const deltaY = Math.abs(this.touchCurrentY - this.touchStartY);

            // Determine if horizontal swipe
            if (deltaX > deltaY && deltaX > 10) {
                this.isSwiping = true;
                e.preventDefault(); // Prevent scroll
            }
        },

        onTouchEnd(e) {
            if (window.innerWidth > 768) return;
            if (!this.isSwiping) return;

            const deltaX = this.touchCurrentX - this.touchStartX;
            const deltaY = Math.abs(this.touchCurrentY - this.touchStartY);

            // Ignore if too vertical or too short
            if (deltaY > Math.abs(deltaX) || Math.abs(deltaX) < 80) {
                this.isSwiping = false;
                return;
            }

            const store = Alpine.store('dashboard');

            if (deltaX < 0 && store.currentView === 'terminal') {
                // Swipe left - show preview
                store.switchView('preview');
            } else if (deltaX > 0 && store.currentView === 'preview') {
                // Swipe right - show terminal
                store.switchView('terminal');
            }

            this.isSwiping = false;
        }
    };
}

function toolbarHandler() {
    return {
        touchStartX: 0,

        sendKey(key) {
            // Send key to terminal
            const keyMap = {
                '↑': '\x1b[A',
                '↓': '\x1b[B',
                '←': '\x1b[D',
                '→': '\x1b[C',
                'Tab': '\t',
                'Esc': '\x1b',
                'Ctrl+C': '\x03',
                'Ctrl+D': '\x04',
                'Ctrl+Z': '\x1a',
                'Ctrl+L': '\x0c',
                'Enter': '\r',
                'Clear': '\x0c'
            };

            const sequence = keyMap[key] || key;
            if (window.terminalSocket && window.terminalSocket.readyState === WebSocket.OPEN) {
                window.terminalSocket.send(JSON.stringify({
                    type: 'input',
                    data: sequence
                }));
            }

            Alpine.store('dashboard').vibrate(5);
        },

        onToolbarTouchStart(e) {
            this.touchStartX = e.touches[0].clientX;
        },

        onToolbarTouchMove(e) {
            // Optional: show visual feedback
        },

        onToolbarTouchEnd(e) {
            const deltaX = e.changedTouches[0].clientX - this.touchStartX;
            const store = Alpine.store('dashboard');

            if (Math.abs(deltaX) < 50) return;

            if (deltaX < 0) {
                store.nextToolbarPage();
            } else {
                store.prevToolbarPage();
            }
        }
    };
}
```

---

### Step 7: Testing Checklist

**Mobile (Android Chrome - Priority #1):**
- [ ] Terminal visible on page load (no blank screen)
- [ ] Swipe left → preview appears with animation
- [ ] Swipe right → terminal returns with animation
- [ ] Swipe hint disappears after 3 seconds
- [ ] Toolbar buttons work (arrow keys, Ctrl+C, etc.)
- [ ] Toolbar swipe changes pages
- [ ] Status indicator shows connection state
- [ ] Can select/copy terminal text
- [ ] Keyboard doesn't break layout
- [ ] No horizontal scroll

**Desktop (Chrome - Priority #2):**
- [ ] Terminal and preview side-by-side
- [ ] No toolbar visible
- [ ] No swipe gestures
- [ ] Resizing works smoothly

**iPhone (Safari - Priority #3):**
- [ ] Same as Android tests
- [ ] Safari-specific CSS works

---

## 🔄 Phase 3: Cross-Device Session Sync (2 days)

**Dream Feature:** "Being able to stop one session on my phone and seamlessly continue on my pc. Or even at the same time"

### Architecture Design

**Backend Changes:**

**File:** `services/session_manager.py`

```python
class SyncedSession:
    """Session that syncs across multiple devices"""

    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id
        self.connected_clients = {}  # {device_id: websocket}
        self.terminal_state = {
            'cwd': '/Users/dlybeck/Documents/Portfolio',
            'history': [],
            'scrollback': [],
            'cursor_position': (0, 0)
        }
        self.pty_process = None

    async def broadcast_state(self, exclude_device=None):
        """Send current terminal state to all connected devices"""
        state_msg = {
            'type': 'state_sync',
            'data': {
                'cwd': self.terminal_state['cwd'],
                'cursor': self.terminal_state['cursor_position'],
                'timestamp': time.time()
            }
        }

        for device_id, ws in self.connected_clients.items():
            if device_id != exclude_device:
                try:
                    await ws.send_json(state_msg)
                except Exception as e:
                    logger.error(f"Failed to sync to {device_id}: {e}")

    async def handle_input(self, device_id: str, input_data: str):
        """Receive input from one device, broadcast to all"""
        # Write to PTY
        if self.pty_process:
            self.pty_process.write(input_data)

        # Broadcast to other devices
        await self.broadcast_input(input_data, exclude_device=device_id)

    async def broadcast_input(self, data: str, exclude_device=None):
        """Send input to all connected devices (for echo)"""
        input_msg = {
            'type': 'input_echo',
            'data': data
        }

        for device_id, ws in self.connected_clients.items():
            if device_id != exclude_device:
                try:
                    await ws.send_json(input_msg)
                except Exception as e:
                    logger.error(f"Failed to echo to {device_id}: {e}")
```

**File:** `apis/route_dev.py`

```python
@router.websocket("/ws/terminal")
async def terminal_websocket(websocket: WebSocket):
    # ... JWT auth ...

    device_id = request.query_params.get('device_id', str(uuid.uuid4()))
    user_id = token_data.get('user_id', 'default')

    # Get or create synced session
    session = get_or_create_synced_session(user_id, session_id)

    await websocket.accept()
    session.connected_clients[device_id] = websocket

    # Send current state to new device
    await websocket.send_json({
        'type': 'state_sync',
        'data': session.terminal_state
    })

    try:
        while True:
            data = await websocket.receive_json()

            if data['type'] == 'input':
                # Handle input and broadcast to other devices
                await session.handle_input(device_id, data['data'])

            elif data['type'] == 'resize':
                # Sync terminal size across devices
                session.terminal_state['size'] = data['data']
                await session.broadcast_state(exclude_device=device_id)

    finally:
        # Remove device but keep session alive for other devices
        del session.connected_clients[device_id]

        # Only close session if no devices left
        if len(session.connected_clients) == 0:
            session.close()
```

**Frontend Changes:**

**File:** `static/dev/js/alpine-store.js`

```javascript
Alpine.store('dashboard', {
    // ... existing state ...

    // Sync state
    deviceId: localStorage.getItem('device_id') || generateDeviceId(),
    otherDevices: [],
    syncEnabled: true,

    // Methods
    enableSync() {
        this.syncEnabled = true;
        localStorage.setItem('sync_enabled', 'true');
    },

    disableSync() {
        this.syncEnabled = false;
        localStorage.setItem('sync_enabled', 'false');
    },

    handleStateSync(data) {
        // Update terminal state from another device
        if (this.syncEnabled) {
            this.workingDir = data.cwd;
            // Update terminal display without re-executing
            console.log('Synced state from another device');
        }
    },

    notifyDeviceConnected(deviceInfo) {
        this.otherDevices.push(deviceInfo);
        this.vibrate(20); // Haptic feedback
    }
});

function generateDeviceId() {
    const id = `${navigator.userAgent.includes('Mobile') ? 'mobile' : 'desktop'}_${Date.now()}`;
    localStorage.setItem('device_id', id);
    return id;
}
```

**File:** `static/dev/js/websocket.js`

```javascript
function connectWebSocket() {
    const store = Alpine.store('dashboard');
    const deviceId = store.deviceId;

    const wsUrl = `wss://${window.location.host}/dev/ws/terminal?session_id=${sessionId}&device_id=${deviceId}&token=${token}`;

    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        const msg = JSON.parse(event.data);

        switch (msg.type) {
            case 'state_sync':
                // Another device changed state
                store.handleStateSync(msg.data);
                break;

            case 'input_echo':
                // Another device sent input
                // (xterm will handle display)
                break;

            case 'device_connected':
                store.notifyDeviceConnected(msg.data);
                break;

            case 'device_disconnected':
                store.otherDevices = store.otherDevices.filter(d => d.id !== msg.data.id);
                break;

            case 'output':
                // Terminal output
                if (window.term) {
                    window.term.write(msg.data);
                }
                break;
        }
    };

    window.terminalSocket = ws;
}
```

**UI Indicator:**

```html
<!-- Add to dashboard.html header -->
<div class="sync-indicator" x-show="$store.dashboard.otherDevices.length > 0">
    <span class="sync-icon">🔄</span>
    <span x-text="`${$store.dashboard.otherDevices.length} other device(s)`"></span>
</div>
```

---

## 📊 Success Metrics

**Phase 2 (Alpine.js Refactor):**
- ✅ Page load < 2 seconds on mobile
- ✅ Swipe response < 100ms
- ✅ No blank screens
- ✅ Code reduced from 1,565 lines to <600 total
- ✅ Zero JavaScript errors in console
- ✅ Lighthouse mobile score > 90

**Phase 3 (Cross-Device Sync):**
- ✅ State syncs within 200ms between devices
- ✅ Can seamlessly switch mid-command
- ✅ Terminal history preserved across devices
- ✅ Works with 3+ devices simultaneously

---

## 🚀 Deployment Strategy

**Phase 2:**
1. Deploy to staging branch first
2. Test on real Android device
3. Test on iPhone
4. Test on desktop
5. Merge to main
6. Deploy to Cloud Run

**Phase 3:**
1. Backend changes first (backwards compatible)
2. Frontend changes with feature flag
3. Gradual rollout (opt-in for cross-device sync)
4. Monitor WebSocket connection counts
5. Full release

---

## 🛠️ Rollback Plan

If Phase 2 breaks:
- Revert to commit a379fed (emergency fix)
- Emergency fix is stable baseline

If Phase 3 breaks:
- Disable sync feature flag
- Phase 2 works standalone

---

## 📝 Next Steps

1. **User tests emergency fix** (commit a379fed)
   - Refresh mobile browser
   - Verify terminal visible
   - Test swipe gestures
   - Report results

2. **Begin Phase 2** (if emergency fix works)
   - Setup Alpine.js
   - Split files
   - Rebuild with Alpine components

3. **Phase 3** (after Phase 2 stable)
   - Implement WebSocket sync
   - Add device indicators
   - Enable cross-device sessions

---

**Ready to proceed?**
Once you test the emergency fix on Android Chrome and confirm it works, I'll begin Phase 2 implementation.
