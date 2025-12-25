# Dev Tile Integration - Final Design

## Your Critique & Questions

### ✅ Critique 1: Dev tile should be a hub (not direct links)
**You're right!** Dev should be a **hub tile** (like "Hobbies" or "Projects") that expands to show VS Code and AgentBridge as buttons/links in the expanded state.

### ✅ Question: How to add 6th tile to 4-corner pattern?
**Answer:** Top-middle works perfectly! The grid system is flexible.

## Understanding Your Tile System

### Current 4-Corner Pattern
```
        [-1, 1]              [1, 1]
      Education          Work Experience

                [0, 0]
                 HOME

        [-1, -1]            [1, -1]
        Hobbies            Projects
```

Grid coordinates: `[x, y]` where:
- `[0, 0]` = Home (center)
- Negative X = Left, Positive X = Right
- Negative Y = Up, Positive Y = Down

### Adding Dev Tile at Top-Middle
```
                [0, -2]
                  DEV      ← NEW!
                   ↓
        [-1, 1]   [0, 0]   [1, 1]
      Education    HOME  Work Experience

        [-1, -1]          [1, -1]
        Hobbies          Projects
```

**Perfect placement:**
- Position: `[0, -2]` (directly above Home)
- Symmetrical with existing tiles
- Natural navigation pattern (top-center)
- Doesn't interfere with 4-corner layout

## Implementation

### Step 1: Add Dev Hub Tile (No Children Initially)

```javascript
// static/scripts/tileData.js

// Add Dev to Home's connections (as a HUB tile)
window.tilesData = {
    "Home": ["Hobbies", "Projects", "Work Experience", "Education", "Dev"],
    "Hobbies": ["3D Printing", "Gaming", "Tennis"],
    "3D Printing": ["Other Models", "Puzzles"],
    "Projects": ["Programs", "Websites"],
    "Websites": ["Digital Planner", "This website", "ScribbleScan"],
    "Education": ["College", "Early Education", "Agile Report"],
    "Dev": [],  // Hub tile with NO children (buttons will open new tabs)
};

// Add Dev tile info
window.tileInfo = {
    // ... existing tiles ...

    "Dev": [
        [0, -2],  // Top-middle position
        `
        Development Tools
        <br><br>
        VS Code, AgentBridge, and more
        <br><br>
        Click a tool to open in new tab
        `,
        ``  // No URL (it's a hub)
    ],
};
```

**Result:**
- Dev tile appears at top-middle when on Home
- Clicking Dev centers it (like clicking Hobbies or Projects)
- Dev expands showing description
- Since `tilesData["Dev"] = []`, it renders as **hub tile** (circular, no sub-tiles)

### Step 2: Add Custom Buttons in Expanded State

**Option A: Modify the tile expansion to show custom buttons**

Update `tileCreation.js` to detect if a hub tile has custom actions:

```javascript
// static/scripts/tileData.js - Add custom button config
window.devToolButtons = {
    "Dev": [
        {
            name: "VS Code",
            url: "/dev/vscode/?folder=/home/dlybeck/Documents/portfolio",
            icon: "⌨️",
            target: "vscode_window"
        },
        {
            name: "AgentBridge",
            url: "/dev/agentbridge",
            icon: "🌉",
            target: "agentbridge_window"
        }
    ]
};
```

```javascript
// static/scripts/tileCreation.js - Modify createTile function

// After line 59 (where it checks if tile is a hub)
if (tilesData.hasOwnProperty(title) == true){
    tile.style.borderRadius = "200px";
    button.style.display = "none";

    // NEW: Check if this hub has custom tool buttons
    if (window.devToolButtons && window.devToolButtons[title]) {
        const toolButtons = window.devToolButtons[title];

        // Create container for tool buttons
        const toolsContainer = document.createElement('div');
        toolsContainer.className = 'dev-tools-container';
        toolsContainer.style.display = 'none'; // Hidden until expanded

        // Create button for each tool
        toolButtons.forEach(tool => {
            const toolBtn = document.createElement('a');
            toolBtn.className = 'dev-tool-button';
            toolBtn.href = tool.url;
            toolBtn.target = tool.target;
            toolBtn.innerHTML = `${tool.icon} ${tool.name}`;
            toolsContainer.appendChild(toolBtn);
        });

        tileContents.appendChild(toolsContainer);

        // Show tool buttons when tile is expanded
        const observer = new MutationObserver(() => {
            if (tileWrapper.classList.contains('expanded')) {
                toolsContainer.style.display = 'flex';
            } else {
                toolsContainer.style.display = 'none';
            }
        });
        observer.observe(tileWrapper, { attributes: true, attributeFilter: ['class'] });
    }
}
```

**CSS for tool buttons:**
```css
/* static/css/map.css - Add at end */

.dev-tools-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
    margin-top: 20px;
    width: 100%;
}

.dev-tool-button {
    background: linear-gradient(135deg, #FFFFFF, #CCC);
    color: #006699;
    padding: 12px 20px;
    border-radius: 10px;
    font-weight: bold;
    text-decoration: none;
    text-align: center;
    transition: all 0.3s ease;
    cursor: pointer;
    font-size: 16px;
    border: none;
}

.dev-tool-button:hover {
    background: linear-gradient(135deg, #CCC, #AAA);
    transform: scale(1.05);
}
```

### Step 3: Fix All URLs to Use Proxy Strategy

**Current problems:**
```javascript
// WRONG - localhost URLs won't work from Cloud Run
url: "http://localhost:8888/?folder=..."
```

**Fixed:**
```javascript
// CORRECT - Uses proxy that works everywhere
url: "/dev/vscode/?folder=/home/dlybeck/Documents/portfolio"
```

**All dev tool URLs:**
```javascript
window.devToolButtons = {
    "Dev": [
        {
            name: "VS Code",
            url: "/dev/vscode/?folder=/home/dlybeck/Documents/portfolio",  // Proxy route
            icon: "⌨️",
            target: "vscode_window"
        },
        {
            name: "AgentBridge",
            url: "/dev/agentbridge",  // Direct route (no proxy needed)
            icon: "🌉",
            target: "_blank"  // Opens in new tab
        }
    ]
};
```

## Visual Result

### When on Home Tile
```
         🔧 Dev
         (circle)

    🎨        🏠        💼
 Hobbies    Home    Work Exp

    📚        💻
 Education  Projects
```

### When Dev Tile is Clicked/Centered
```
         🔧 DEV (expanded)
    ┌──────────────────────┐
    │ Development Tools    │
    │                      │
    │ VS Code, AgentBridge │
    │ Click to open        │
    │                      │
    │ [⌨️ VS Code]        │
    │ [🌉 AgentBridge]    │
    └──────────────────────┘

    (other tiles dimmed)
```

Clicking "VS Code" → Opens `/dev/vscode/...` in new tab
Clicking "AgentBridge" → Opens `/dev/agentbridge` in new tab

## Benefits

✅ **DRY** - Reuses existing tile system, no duplicate code
✅ **Consistent** - Uses homepage blue theme
✅ **Natural UX** - Same interaction as Hobbies → Gaming
✅ **Top-middle placement** - Symmetrical, doesn't disrupt 4-corner pattern
✅ **Hub behavior** - Dev is a hub, not a direct link
✅ **New tab links** - VS Code and AgentBridge open in new tabs
✅ **Universal URLs** - Proxy routes work locally AND on Cloud Run
✅ **No custom navbar** - Uses existing homepage navbar

## Files to Modify

```
static/scripts/tileData.js       - Add Dev tile, devToolButtons config
static/scripts/tileCreation.js   - Add custom button rendering logic
static/css/map.css               - Add .dev-tools-container, .dev-tool-button styles
templates/dev/hub.html           - DELETE (not needed)
templates/dev/agentbridge_dashboard.html - Remove Dracula navbar
```

## Migration Path

1. **Add Dev tile data** - Just data, no logic yet
2. **Test navigation** - Verify Dev tile appears and centers
3. **Add custom button logic** - Render tools when expanded
4. **Style tool buttons** - Match homepage theme
5. **Fix proxy URLs** - Update all localhost references
6. **Remove Dracula navbar** - Clean up dev pages
7. **Test end-to-end** - Verify everything works

## Questions?

Does this approach work for you?
- Dev tile at top-middle `[0, -2]`
- Hub tile (circular, no children)
- Expands to show VS Code and AgentBridge buttons
- Buttons open tools in new tabs
- Uses proxy URLs (DRY, universal)
