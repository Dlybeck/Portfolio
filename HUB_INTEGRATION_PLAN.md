# Hub Integration Plan - DRY & Theme-Consistent

## Current Homepage Theme Analysis

### Visual Style
- **Background:** Sand texture (`sand2048.webp`) with `#e0c8ab` base color
- **Navbar:** Blue gradient `linear-gradient(135deg, #006699, #005588)`
- **Tiles:** Blue gradient `linear-gradient(135deg, #0077AA, #004477)`
- **Buttons:** White gradient `linear-gradient(135deg, #FFFFFF, #CCC)` with `#006699` text
- **Border Radius:** 20px for tiles, 10px for navbar
- **Font:** System fonts, white/off-white text
- **Interactive tiles:** Grid-based map navigation system

### Architecture
- **Base Template:** `shared/base.html` - includes navbar component
- **Navbar Component:** `components/navbar.html` - reusable across pages
- **Homepage:** Interactive tile map at `/` (Home tile + connected tiles)
- **Tile System:** JavaScript-driven grid navigation (`tileData.js`, `map.js`)

## Issues with Current Dev Hub

### Issue 1: Localhost Links ❌
```html
<!-- Current (WRONG) -->
<a href="http://localhost:8888/?folder=...">
```
**Problem:** Breaks universal proxy strategy, won't work from Cloud Run

**Fix:** Use `/dev/vscode` proxy endpoint
```html
<!-- Correct -->
<a href="/dev/vscode/?folder=/home/dlybeck/Documents/portfolio&tkn={{token}}">
```

### Issue 2: Theme Mismatch ❌
- Dev Hub uses Dracula theme (#21222c, #bd93f9)
- Homepage uses blue gradient theme (#006699, #0077AA)
- Completely different visual language

### Issue 3: Unnecessary Dracula Navbar ❌
- If hub is entry point, individual tools don't need their own navbar
- Violates DRY - navbar duplicated across pages
- Adds visual clutter

## Proposed Solution: Integrate Dev Hub as Homepage Tile

### Option A: "Dev" Tile on Homepage (RECOMMENDED)

Add "Dev" as a tile on the existing homepage map, just like "Hobbies", "Projects", etc.

**Visual Integration:**
```javascript
// tileData.js
window.tilesData = {
    "Home": ["Hobbies", "Projects", "Work Experience", "Education", "Dev"],  // Add Dev
    "Dev": ["VS Code", "AgentBridge"],  // Dev hub children
    // ... existing tiles
};

window.tileInfo = {
    // ... existing tiles ...

    "Dev": [
        [2, 0],  // Position on grid
        `
        Development tools and AI-powered coding
        <br><br>
        VS Code, AgentBridge, and more
        `,
        `/dev/hub`  // Opens dev hub page
    ],

    "VS Code": [
        [3, -1],
        `
        Full IDE with Portfolio workspace
        <br><br>
        Code with VS Code in your browser
        `,
        `/dev/vscode/?folder=/home/dlybeck/Documents/portfolio`  // Direct link
    ],

    "AgentBridge": [
        [3, 1],
        `
        AI-powered spec-driven development
        <br><br>
        Build features with Claude & Gemini
        `,
        `/dev/agentbridge`
    ],
};
```

**Benefits:**
- ✅ **Consistent theme** - Uses existing blue tiles
- ✅ **DRY** - Reuses existing tile system
- ✅ **Familiar UX** - Same navigation as rest of site
- ✅ **No duplication** - One navbar, one design system
- ✅ **Natural discovery** - Dev tools visible from homepage

### Option B: Separate /dev/hub Page (Styled Like Homepage)

Keep separate hub page but style it with homepage theme.

**Implementation:**
```html
<!-- templates/dev/hub.html -->
{% extends "shared/base.html" %}

{% block content %}
<link rel="stylesheet" href="/static/css/map.css">
<div class="map">
    <!-- Create 2-3 tiles for dev tools -->
    <div class="tile-container" style="left: 50%; top: 50%;">
        <div class="tile">
            <div class="tile-contents">
                <div class="tile-title">VS Code</div>
                <div class="tile-text">Full IDE with Portfolio workspace</div>
                <button class="button" onclick="openVSCode()">Open</button>
            </div>
        </div>
    </div>
    <!-- AgentBridge tile ... -->
</div>
{% endblock %}
```

**Benefits:**
- ✅ Consistent theme with homepage
- ✅ Separate dev space
- ❌ Still duplicates tile system (not fully DRY)

## Recommended Approach: Option A

### Implementation Steps

#### 1. Update Tile Data
**File:** `static/scripts/tileData.js`
- Add "Dev" to Home's connections
- Add "Dev", "VS Code", "AgentBridge" tile info
- Use proxy URLs (not localhost)

#### 2. Fix Proxy URLs
**Files:** All dev links
- Change `http://localhost:8888` → `/dev/vscode`
- Change `http://localhost:8080` → proxy routes

#### 3. Remove Unnecessary Navbars
**Files:** `templates/dev/agentbridge_dashboard.html`, future dev pages
- Keep minimal header OR no header at all
- Rely on homepage navbar for navigation
- Tools are "full screen" experiences

#### 4. Optional: Add Dev Hub Landing Page
**File:** `templates/dev/hub.html` (optional intermediate page)
- If someone goes directly to `/dev/hub` instead of via tiles
- Shows simple list/grid of dev tools
- Uses homepage theme (blue gradients)

### URL Strategy (DRY & Universal)

All dev tool URLs go through proxy:

```
/dev                        → Homepage tile for Dev (or minimal hub)
/dev/vscode                 → VS Code proxy (adds folder param)
/dev/agentbridge            → AgentBridge dashboard
/dev/terminal               → Pure terminal (if we keep it)
```

**Proxy Logic:**
```python
# Already exists in route_dev_proxy.py
@dev_proxy_router.get("/vscode/{path:path}")
async def vscode_proxy(...):
    if settings.K_SERVICE:
        # Cloud Run: proxy to Mac via SOCKS5
        target = f"http://{settings.MAC_SERVER_IP}:{settings.CODE_SERVER_PORT}/{path}"
    else:
        # Local: proxy to localhost
        target = f"http://localhost:{settings.CODE_SERVER_PORT}/{path}"
```

**This handles:**
- ✅ Local development (localhost)
- ✅ Cloud Run deployment (proxies to Mac)
- ✅ No hardcoded localhost URLs

## DRY Principles Applied

### Shared Components (Reuse, Don't Duplicate)

1. **Navbar:** One navbar component (`components/navbar.html`)
   - Used across all pages via `shared/base.html`
   - Don't create custom navbars for each tool

2. **Theme:** One CSS theme (`base.css`, `map.css`)
   - Blue gradients: `#006699 → #005588` (navbar), `#0077AA → #004477` (tiles)
   - Sand texture background
   - 20px border radius
   - White text

3. **Tile System:** One JavaScript system (`tileData.js`, `map.js`)
   - Define tiles once in data
   - Rendering logic shared
   - Don't recreate card layouts

4. **Proxy Strategy:** One universal routing system
   - `/dev/vscode` works locally AND on Cloud Run
   - Backend handles environment detection
   - Frontend never needs to know localhost vs proxy

### What to Delete (Violations of DRY)

1. **Delete:** Dracula navbar CSS in `agentbridge_dashboard.html`
   - Use homepage navbar OR no navbar

2. **Delete:** Custom hub HTML in `templates/dev/hub.html` (if going with Option A)
   - Or reskin to match homepage theme

3. **Delete:** Localhost hardcoded URLs
   - Replace with proxy URLs everywhere

## File Changes Summary

### Modified Files
```
static/scripts/tileData.js          - Add Dev, VS Code, AgentBridge tiles
templates/dev/agentbridge_dashboard.html  - Remove custom navbar, use base.html
templates/dev/hub.html              - Either delete OR reskin with homepage theme
apis/route_dev_core.py              - Update /dev route logic
```

### New Files (None if Option A)
- Everything reuses existing infrastructure

### Deleted Files
- None, just remove code blocks

## Migration Path

### Phase 1: Fix URLs (Critical)
1. Replace all `http://localhost:8888` with `/dev/vscode`
2. Replace all `http://localhost:8080` with proxy routes
3. Test locally and on Cloud Run

### Phase 2: Integrate with Homepage
1. Add Dev tile to `tileData.js`
2. Add VS Code and AgentBridge as child tiles
3. Test tile navigation

### Phase 3: Remove Duplication
1. Remove Dracula navbar from dev pages
2. Either delete `/dev/hub` or reskin to match homepage
3. Ensure all pages extend `shared/base.html`

### Phase 4: Polish
1. Ensure all tiles have proper styling
2. Add proper descriptions
3. Test full navigation flow

## Expected Result

**User Flow:**
1. Visit portfolio homepage → see interactive tile map
2. Click "Dev" tile → expands showing dev tools
3. Click "VS Code" → opens in new tab via `/dev/vscode?folder=...`
4. Click "AgentBridge" → opens full-screen dashboard
5. Homepage navbar always visible for navigation back
6. Consistent blue theme throughout
7. Works on local AND Cloud Run (no localhost URLs)

**Benefits:**
- ✅ **DRY:** One theme, one navbar, one tile system
- ✅ **Consistent:** Looks like part of the portfolio
- ✅ **Universal:** Works locally and in Cloud Run
- ✅ **Discoverable:** Dev tools visible from homepage
- ✅ **Simple:** No duplicate code or themes

## Next Steps

Would you like me to:
1. **Option A:** Integrate dev tools as tiles on homepage (recommended)
2. **Option B:** Keep separate hub but reskin with homepage theme
3. **Just fix the URLs first** then decide on integration approach

What's your preference?
