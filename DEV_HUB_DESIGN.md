# Dev Hub Dashboard Design

## Concept: Central Command Center for Dev Tools

Instead of going straight to `/dev/terminal` (VS Code iframe), create a **hub page** at `/dev` that serves as a launcher for all dev tools.

## Visual Design

### Layout: Tool Cards (like VS Code welcome screen)

```
╔═══════════════════════════════════════════════════════════════╗
║  [Logo] Dev Hub                                    🚪 Logout  ║
╠═══════════════════════════════════════════════════════════════╣
║                                                                ║
║   Welcome back, David! Choose your tool:                      ║
║                                                                ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐║
║   │  ⌨️  VS Code      │  │  🌉  AgentBridge │  │ 🖥️ Terminal││
║   │                  │  │                  │  │             │║
║   │  Full IDE        │  │  AI-powered     │  │ Shell       │║
║   │  Portfolio       │  │  spec-driven    │  │ access      │║
║   │  8 files open    │  │  development    │  │             │║
║   │                  │  │                  │  │             │║
║   │  [Open →]        │  │  [Launch →]     │  │ [Open →]   │║
║   └──────────────────┘  └──────────────────┘  └─────────────┘║
║                                                                ║
║   ┌──────────────────┐  ┌──────────────────┐  ┌─────────────┐║
║   │  📊  Logs        │  │  ⚙️  Settings    │  │ 🔧 Admin   ││
║   │                  │  │                  │  │             │║
║   │  View server    │  │  Configure      │  │ Server      │║
║   │  logs & metrics │  │  dev tools      │  │ management  │║
║   │                  │  │                  │  │             │║
║   │  [View →]        │  │  [Edit →]       │  │ [Manage →] │║
║   └──────────────────┘  └──────────────────┘  └─────────────┘║
║                                                                ║
║   Recent Activity:                                             ║
║   • Portfolio: Last modified 2 min ago                         ║
║   • AgentBridge: file-browser fix deployed                     ║
║                                                                ║
╚═══════════════════════════════════════════════════════════════╝
```

## Features

### Tool Cards
Each card shows:
- **Icon** - Visual identifier
- **Name** - Tool name
- **Description** - What it does
- **Status** - e.g., "8 files open", "Ready", "Offline"
- **Action Button** - Opens the tool

### Smart Links
- **VS Code** → Opens `http://localhost:8888/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}` in new tab
- **AgentBridge** → `/dev/agentbridge`
- **Terminal** → `/dev/terminal` (pure terminal, no VS Code)
- **Logs** → `/dev/logs` (new feature - tail server logs)
- **Settings** → `/dev/settings` (configure tools)

### Recent Activity (Optional)
- Show last accessed tools
- Recent git commits
- Deployment status
- Quick stats

## Navigation Flow

```
User visits /dev
    ↓
Lands on Dev Hub (tool cards)
    ↓
Clicks "VS Code" card
    ↓
Opens VS Code in new tab with workspace
    ↓
User works in VS Code
    ↓
Switches back to Dev Hub tab
    ↓
Clicks "AgentBridge" card
    ↓
Opens AgentBridge dashboard
    ↓
All tools accessible from unified Dracula navbar
```

## Updated Navbar

All pages get same navbar with "Hub" link:

```html
<nav class="dev-navbar">
  <div class="navbar-content">
    <img src="/static/images/Logo.webp" alt="Logo" class="navbar-logo">
    <div class="navbar-title">Dev Dashboard</div>
  </div>
  <div class="navbar-links">
    <a href="/dev" class="nav-item" title="Dev Hub">
      <span class="nav-icon">🏠</span>
      <span>Hub</span>
    </a>
    <a href="http://localhost:8888/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}"
       target="vscode_window"
       class="nav-item"
       title="VS Code Editor">
      <span class="nav-icon">⌨️</span>
      <span>Editor</span>
    </a>
    <a href="/dev/agentbridge" class="nav-item" title="Agent Bridge">
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

## File Structure

```
/dev                    → Dev Hub (NEW - tool launcher)
/dev/vscode            → VS Code proxy (keep for iframe compatibility)
/dev/agentbridge       → AgentBridge dashboard
/dev/terminal          → Pure terminal (NEW - no VS Code, just shell)
/dev/logs              → Server logs viewer (NEW - optional)
/dev/settings          → Dev tools settings (NEW - optional)
```

## Implementation

### Phase 1: Core Hub (Essential)
1. Create `/dev` hub page with tool cards
2. Add VS Code card with direct link (workspace parameter)
3. Add AgentBridge card
4. Add unified Dracula navbar to all pages
5. Add "Hub" link to navbar

### Phase 2: Enhanced Features (Optional)
6. Add Terminal card (pure shell, no VS Code)
7. Add recent activity section
8. Add tool status indicators (online/offline)
9. Add workspace selector for VS Code

### Phase 3: Advanced (Nice-to-have)
10. Add Logs viewer card
11. Add Settings card
12. Add quick actions (deploy, restart server, etc.)
13. Add keyboard shortcuts (press 'e' for editor, 'b' for bridge)

## CSS Theme - Dracula Everywhere

All pages use consistent Dracula theme:
- Background: `#121212` with sand texture
- Cards: `#21222c` with `#44475a` border
- Navbar: `#21222c` with `#44475a` border
- Accents: `#bd93f9` (purple) for hover/active
- Text: `#f8f8f2` (off-white)

## Benefits

### User Experience
✅ Clear entry point - no confusion about where to go
✅ See all tools at a glance
✅ Status indicators show what's available
✅ Quick access to frequently used tools
✅ Unified navigation from anywhere

### Technical
✅ Clean separation of concerns
✅ Easy to add new tools (just add a card)
✅ Navbar links work from any page
✅ Direct links = no iframe state issues
✅ Scalable architecture

### Mobile
✅ Cards stack vertically on small screens
✅ Touch-friendly buttons
✅ No iframe persistence issues (direct links)
✅ Same experience as desktop

## Quick Start Implementation

Minimal viable hub (15 minutes):

```html
<!-- templates/dev/hub.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dev Hub</title>
    <link rel="stylesheet" href="/static/css/base.css">
    <style>
        body {
            background: #121212 url("/static/images/sand2048.webp") cover;
            color: #f8f8f2;
            font-family: -apple-system, sans-serif;
            margin: 0;
            padding: 45px 20px 20px;
        }
        .dev-navbar { /* Copy from dev_dashboard.html */ }
        .hub-container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .tools-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-top: 30px;
        }
        .tool-card {
            background: #21222c;
            border: 1px solid #44475a;
            border-radius: 12px;
            padding: 24px;
            transition: transform 0.2s, border-color 0.2s;
        }
        .tool-card:hover {
            transform: translateY(-4px);
            border-color: #bd93f9;
        }
        .tool-icon {
            font-size: 48px;
            margin-bottom: 12px;
        }
        .tool-name {
            font-size: 24px;
            font-weight: 600;
            margin-bottom: 8px;
        }
        .tool-desc {
            color: #888;
            margin-bottom: 16px;
        }
        .tool-btn {
            background: #bd93f9;
            color: #21222c;
            border: none;
            padding: 10px 20px;
            border-radius: 6px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            display: inline-block;
        }
        .tool-btn:hover {
            background: #d4b3ff;
        }
    </style>
</head>
<body>
    <nav class="dev-navbar">
        <!-- Same navbar as dev_dashboard.html -->
    </nav>

    <div class="hub-container">
        <h1>Dev Hub</h1>
        <p>Choose your development tool:</p>

        <div class="tools-grid">
            <div class="tool-card">
                <div class="tool-icon">⌨️</div>
                <div class="tool-name">VS Code</div>
                <div class="tool-desc">Full IDE with Portfolio workspace</div>
                <a href="http://localhost:8888/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}"
                   target="vscode_window"
                   class="tool-btn">Open Editor →</a>
            </div>

            <div class="tool-card">
                <div class="tool-icon">🌉</div>
                <div class="tool-name">AgentBridge</div>
                <div class="tool-desc">AI-powered spec-driven development</div>
                <a href="/dev/agentbridge" class="tool-btn">Launch Bridge →</a>
            </div>

            <div class="tool-card">
                <div class="tool-icon">🖥️</div>
                <div class="tool-name">Terminal</div>
                <div class="tool-desc">Direct shell access</div>
                <a href="/dev/terminal" class="tool-btn">Open Terminal →</a>
            </div>
        </div>
    </div>
</body>
</html>
```

## Routes to Add

```python
# apis/route_dev_core.py

@dev_core_router.get("", response_class=HTMLResponse)
async def dev_hub(request: Request):
    """Dev Hub - central dashboard for all dev tools"""
    token = request.cookies.get("session_token") or request.query_params.get("tkn")
    if not token:
        return RedirectResponse(url="/dev/login", status_code=302)
    return templates.TemplateResponse("dev/hub.html", {"request": request, "token": token})

# Update existing /dev/terminal to NOT redirect
@dev_core_router.get("/terminal", response_class=HTMLResponse)
async def terminal_dashboard(request: Request):
    """Terminal page - keep as pure terminal OR VS Code iframe"""
    # ... existing code, remove redirect to /dev/terminal
```

## Decision Points

1. **What goes on the hub?** Start with 3 cards (VS Code, AgentBridge, Terminal) or add more?
2. **Terminal behavior?** Keep as VS Code iframe or make it pure shell?
3. **Recent activity?** Add now or later?
4. **Keyboard shortcuts?** Add quick keys (e/b/t for tools)?

What do you think? Should we build this minimal hub first, then iterate?
