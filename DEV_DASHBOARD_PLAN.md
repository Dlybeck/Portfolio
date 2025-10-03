# Dev Dashboard - Implementation Plan

## Project Overview
**Goal:** Build a web-based AI-driven development dashboard accessible remotely from any device (including mobile) as a private extension to davidlybeck.com

**Location:** `/Users/dlybeck/Documents/Portfolio` (integrating into existing FastAPI portfolio)

---

## 🎨 UI/UX Design

### Mobile Layout (Swipeable Panes)
**Pane 1: AI Assistant (Default)**
- Full screen chat interface
- Large text input at bottom
- Quick action buttons (Build, Test, Deploy, Fix, etc.)
- Swipe gesture to access Preview pane

**Pane 2: Preview (Swipe Right)**
- Tabbed interface:
  - Terminal
  - Preview (HTML/images)
  - Code viewer
  - Logs
  - Files
- Swipe back to AI pane

### Desktop Layouts (Customizable - 4 Presets)

**Layout 1: AI-Focused (Default)**
```
┌─────────────── 100% ───────────────┐
│   AI Assistant (60% height)        │
├────────────────────────────────────┤
│   Preview Tabs (40% height)        │
│   [Terminal][Preview][Code][Logs]  │
└────────────────────────────────────┘
```

**Layout 2: Side-by-Side**
```
┌────────── 50% ─────────┬────────── 50% ─────────┐
│   AI Assistant         │   Preview Tabs         │
│   (full height)        │   (full height)        │
└────────────────────────┴────────────────────────┘
```

**Layout 3: Triple Pane**
```
┌──── 40% ────┬───────── 60% ─────────┐
│             │   AI Assistant        │
│  Terminal   │   (60% height)        │
│  (full      ├───────────────────────┤
│  height)    │   Preview             │
│             │   (40% height)        │
└─────────────┴───────────────────────┘
```

**Layout 4: Floating Terminal**
```
┌─────────────── 100% ───────────────┐
│   AI Assistant (70% height)        │
├────────────────────────────────────┤
│   Preview (30% height)             │
└────────────────────────────────────┘
     ┌──────────────┐
     │  Terminal    │  ← Draggable floating window
     │  (Pop-out)   │
     └──────────────┘
```

---

## 📁 File Structure

```
Portfolio/
├── apis/
│   ├── route_general.py          [existing]
│   ├── route_projects.py         [existing]
│   ├── route_education.py        [existing]
│   ├── route_hobbies.py          [existing]
│   ├── route_other.py            [existing]
│   ├── route_dev.py              [NEW] - Dev dashboard routes
│   └── route_auth.py             [NEW] - Authentication endpoints
│
├── core/
│   ├── config.py                 [existing]
│   └── security.py               [NEW] - JWT, password hashing, auth logic
│
├── services/                     [NEW DIRECTORY]
│   ├── __init__.py
│   ├── terminal.py               - WebSocket terminal handler
│   ├── ai_assistant.py           - Claude API integration
│   ├── file_manager.py           - File operations (browse, edit, upload)
│   ├── preview.py                - Preview rendering logic
│   └── project_manager.py        - Project detection & management
│
├── static/
│   └── dev/                      [NEW DIRECTORY]
│       ├── js/
│       │   ├── terminal.js       - xterm.js terminal implementation
│       │   ├── ai-chat.js        - AI chat interface & button actions
│       │   ├── preview.js        - Preview pane logic (tabs, file viewing)
│       │   ├── file-explorer.js  - File tree navigation
│       │   ├── layout-manager.js - Layout switching & customization
│       │   └── main.js           - App initialization & WebSocket setup
│       │
│       └── css/
│           ├── dashboard.css     - Main dashboard styles
│           ├── mobile.css        - Mobile-specific styles
│           └── themes.css        - Dark/light theme variables
│
├── templates/
│   └── dev/                      [NEW DIRECTORY]
│       ├── login.html            - Login page
│       ├── dashboard.html        - Main dashboard interface
│       └── components/           - Reusable template components
│           ├── ai-pane.html
│           ├── terminal-pane.html
│           ├── preview-pane.html
│           └── settings-panel.html
│
├── main.py                       [UPDATE] - Include new routers
├── requirements.txt              [UPDATE] - Add new dependencies
├── .env                          [NEW] - Environment variables (API keys, secrets)
└── DEV_DASHBOARD_PLAN.md         [THIS FILE]
```

---

## 🔧 Technical Stack

### Backend
- **FastAPI** (existing) - Web framework
- **Uvicorn** (existing) - ASGI server
- **WebSockets** - Real-time terminal & AI communication
- **python-jose** - JWT token handling
- **passlib + bcrypt** - Password hashing
- **anthropic** - Claude API client
- **aiofiles** - Async file operations
- **ptyprocess** - Terminal session management

### Frontend
- **Vanilla JavaScript** (no framework overhead)
- **xterm.js** - Terminal emulator
- **Marked.js** - Markdown rendering
- **Prism.js** - Code syntax highlighting
- **Split.js** - Resizable panes
- **Hammer.js** - Touch gestures (mobile swipe)

### Security
- JWT-based authentication
- HTTPS (Let's Encrypt in production)
- CORS configuration
- Password hashing (bcrypt)
- Optional IP whitelist
- Session timeout (configurable)

---

## 🚀 Features Breakdown

### 1. Authentication System
- [x] Login page (`/dev` redirects if not authenticated)
- [x] JWT token generation & validation
- [x] Password hashing
- [x] Session management (30 min timeout default)
- [ ] Optional: SSH key authentication
- [ ] Optional: 2FA support

### 2. AI Assistant Pane
- [x] Chat interface with Claude API
- [x] Conversation history
- [x] Code block syntax highlighting
- [x] Quick action buttons:
  - 🔨 Build Project
  - 🧪 Run Tests
  - 📤 Git Push
  - 🐛 Debug Last Error
  - 📝 Generate Code
  - 🗂️ New File
  - 🔍 Search Project
- [x] Context-aware suggestions (based on project type)
- [x] Voice input (mobile friendly)
- [ ] Continuous mode: "Keep working until tests pass"
- [x] Auto-attach current file context

### 3. Terminal Pane
- [x] Full interactive terminal (xterm.js)
- [x] WebSocket connection to PTY process
- [x] Command history
- [x] Copy/paste support
- [x] Auto-scroll
- [ ] Multiple terminal tabs
- [ ] Split terminal view
- [x] Mobile keyboard support

### 4. Preview Pane (Tabbed)
**Tab: Preview**
- [x] HTML/web page live preview (iframe)
- [x] Auto-refresh on file save
- [x] Responsive size toggles (mobile/tablet/desktop)

**Tab: Terminal** (duplicate for convenience)
- [x] Same as Terminal Pane

**Tab: Code Viewer**
- [x] Syntax highlighted file viewer
- [x] Line numbers
- [x] Side-by-side diff view
- [x] Jump to file from AI suggestions

**Tab: Logs**
- [x] Tail view of log files
- [x] Filter/search
- [x] Auto-scroll
- [x] Color-coded log levels

**Tab: Files**
- [x] Tree view of project
- [x] Quick file open
- [x] Upload/download files
- [x] Right-click context menu
- [x] Create/delete/rename

### 5. Layout Customization
- [x] 4 preset layouts (AI-Focused, Side-by-Side, Triple, Floating)
- [x] Settings panel (⚙️ icon)
- [x] Drag-to-reorder preview tabs
- [x] Resizable panes (desktop)
- [x] Layout preference saved to localStorage
- [ ] Per-project layout memory

### 6. Mobile Experience
- [x] Swipeable panes (AI ↔ Preview)
- [x] Touch-friendly buttons
- [x] Single-pane focus mode
- [x] Bottom action toolbar
- [x] Portrait/landscape optimization
- [ ] Voice input for AI chat

### 7. Project Management
- [x] Auto-detect project type (React, Python, Node, etc.)
- [x] Project switcher dropdown
- [x] Recent projects list
- [x] Bookmarks/favorites
- [ ] Multi-root workspace support
- [x] `.env` file detection

---

## 📦 Dependencies to Add

```txt
# Authentication & Security
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6

# AI Integration
anthropic==0.18.1

# Terminal & File Operations
websockets==12.0
ptyprocess==0.7.0
aiofiles==23.2.1

# Utilities
python-dotenv==1.0.0
```

---

## 🔐 Environment Variables (.env)

```env
# Authentication
SECRET_KEY=your-secret-key-here  # Generate with: openssl rand -hex 32
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# AI Integration
ANTHROPIC_API_KEY=your-anthropic-api-key

# Dashboard Settings
DASHBOARD_USERNAME=admin  # Change this!
DASHBOARD_PASSWORD_HASH=  # Generated on first run

# Optional
ALLOWED_IPS=  # Comma-separated IPs for whitelist
ENABLE_SSH_AUTH=false
```

---

## 🛣️ API Routes

### Authentication Routes (`/auth`)
- `POST /auth/login` - Login with username/password
- `POST /auth/logout` - Invalidate token
- `GET /auth/verify` - Verify token validity

### Dev Dashboard Routes (`/dev`)
- `GET /dev` - Dashboard HTML (requires auth)
- `GET /dev/login` - Login page
- `WS /dev/ws/terminal` - WebSocket for terminal
- `WS /dev/ws/ai` - WebSocket for AI chat

### File Management Routes (`/dev/api`)
- `GET /dev/api/files` - List files in directory
- `GET /dev/api/files/read` - Read file content
- `POST /dev/api/files/write` - Write file content
- `POST /dev/api/files/upload` - Upload file
- `DELETE /dev/api/files/delete` - Delete file
- `GET /dev/api/projects` - List available projects

### AI Routes (`/dev/api/ai`)
- `POST /dev/api/ai/chat` - Send message to AI
- `POST /dev/api/ai/action` - Execute quick action (build, test, etc.)
- `GET /dev/api/ai/context` - Get current project context

### Preview Routes (`/dev/api/preview`)
- `GET /dev/api/preview/file` - Preview file content
- `GET /dev/api/preview/logs` - Tail log file
- `POST /dev/api/preview/refresh` - Trigger preview refresh

---

## 📋 Implementation Phases

### Phase 1: Core Infrastructure ✅
- [x] Create directory structure
- [ ] Set up authentication system
- [ ] Configure environment variables
- [ ] Update `main.py` with new routes
- [ ] Create basic login page

### Phase 2: Backend Services
- [ ] Implement `services/terminal.py` (WebSocket terminal)
- [ ] Implement `services/ai_assistant.py` (Claude integration)
- [ ] Implement `services/file_manager.py` (file operations)
- [ ] Implement `services/preview.py` (preview logic)
- [ ] Create API routes in `route_dev.py`

### Phase 3: Frontend - Dashboard Layout
- [ ] Create `dashboard.html` template
- [ ] Implement layout manager (4 presets)
- [ ] Create mobile swipeable interface
- [ ] Add settings panel
- [ ] Implement theme switching (dark/light)

### Phase 4: Frontend - AI Pane
- [ ] Build chat interface UI
- [ ] Implement WebSocket AI chat
- [ ] Add quick action buttons
- [ ] Syntax highlighting for code blocks
- [ ] Context-aware suggestions

### Phase 5: Frontend - Terminal Pane
- [ ] Integrate xterm.js
- [ ] WebSocket terminal connection
- [ ] Command history
- [ ] Mobile keyboard support

### Phase 6: Frontend - Preview Pane
- [ ] Create tabbed interface
- [ ] Implement HTML preview (iframe)
- [ ] Implement code viewer (syntax highlighting)
- [ ] Implement log viewer (tail with auto-scroll)
- [ ] Implement file explorer tree

### Phase 7: Polish & Testing
- [ ] Mobile responsiveness testing
- [ ] Security audit
- [ ] Performance optimization
- [ ] Error handling & user feedback
- [ ] Documentation

### Phase 8: Deployment
- [ ] Docker configuration update
- [ ] HTTPS setup (Let's Encrypt)
- [ ] Cloudflare Tunnel setup (optional)
- [ ] Systemd service for auto-start
- [ ] Backup strategy

---

## 🎯 Success Criteria

- [x] Can access dashboard from phone browser
- [x] Authentication protects `/dev` routes
- [x] Can browse and edit files remotely
- [x] Can execute terminal commands from any device
- [x] AI assistant can build, test, and deploy projects
- [x] Preview shows HTML/images/code correctly
- [x] Mobile swipe gestures work smoothly
- [x] Desktop layouts are customizable
- [x] Sessions persist (reconnect without losing state)
- [x] Secure (HTTPS, JWT, password hashing)

---

## 🚧 Known Limitations & Future Enhancements

### Current Limitations
- Single user (one login at a time)
- No session history/replay
- No collaborative features
- Limited file upload size

### Future Enhancements
- Multi-user support (separate workspaces)
- Session recording & replay
- Real-time collaboration (shared terminals)
- Cloud storage integration (S3, Dropbox)
- Custom AI model selection (GPT-4, local models)
- Plugin system for custom actions
- Mobile app (React Native wrapper)
- Voice commands
- Screen sharing for debugging

---

## 📝 Notes & Decisions

### Why Vanilla JS instead of React?
- Faster initial load
- No build step needed
- Easier to customize
- Less complexity for single-page app

### Why JWT instead of session cookies?
- Better for API authentication
- Mobile-friendly
- Stateless (scales easier)
- Can be used with mobile apps later

### Why xterm.js?
- Industry standard (used by VS Code, Hyper, etc.)
- Full terminal emulation
- Excellent mobile support
- Active maintenance

### Project Detection Logic
- Check for `package.json` → Node/React/Vue
- Check for `requirements.txt` or `setup.py` → Python
- Check for `Cargo.toml` → Rust
- Check for `go.mod` → Go
- Default to generic project

---

## 🔗 Useful Resources

- [xterm.js Documentation](https://xtermjs.org/)
- [FastAPI WebSockets](https://fastapi.tiangolo.com/advanced/websockets/)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [python-jose JWT](https://python-jose.readthedocs.io/)
- [Split.js (Resizable Panes)](https://split.js.org/)

---

**Last Updated:** 2025-10-01
**Status:** Planning Phase
**Next Action:** Begin Phase 1 - Core Infrastructure
