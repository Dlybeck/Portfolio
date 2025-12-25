# Secret Dev Tile - Feasibility Analysis

## The Idea
Make Home tile **slidable/draggable** upward to reveal a hidden Dev tile underneath.

```
Initial State:              After Sliding Home Up:

    🎨      🏠      💼          🎨      🏠      💼
  Hobbies  HOME  Work Exp    Hobbies (moved) Work Exp

    📚      💻                  📚      🔧      💻
 Education Projects         Education DEV  Projects
                                      (revealed!)
```

## Feasibility Rating: **7/10** ⭐⭐⭐⭐⭐⭐⭐

### Why 7/10? (Very Doable, But Some Complexity)

#### ✅ **What Makes It Feasible (Pros)**

1. **Event System Already Exists**
   - Tile click handlers already in place (`map.js:33`)
   - Event propagation system works (`e.stopPropagation()`)
   - Can add drag/swipe listeners easily

2. **Positioning System is Flexible**
   - Grid-based positioning (`[x, y]` coordinates)
   - CSS transforms already used (`translate(-50%, -50%)`)
   - Dynamic position updates work (`tile.style.left`, `tile.style.top`)

3. **Tile Visibility System**
   - Already has dimming/showing logic (`updateVisibility()`)
   - Can easily add "hidden" state for Dev tile
   - Initial render can skip Dev tile

4. **Animation Support**
   - Transitions already defined (`.tile-container { transition: all 0.4s ease }`)
   - Smooth movement already works
   - Background parallax exists (`backgroundPosition`)

5. **Touch Support Likely Easy**
   - Mobile-first design already (`viewport` meta)
   - Can use `touchstart`, `touchmove`, `touchend`
   - Or use modern Pointer Events API (supports mouse + touch)

#### ⚠️ **What Adds Complexity (Challenges)**

1. **Gesture Detection (~2 complexity points)**
   - Need to distinguish between:
     - Click (center on tile) - already works
     - Vertical drag (reveal Dev) - NEW
     - Horizontal drag (pan map?) - might conflict
   - Solution: Detect drag direction and distance threshold

2. **State Management (~1 complexity point)**
   - Track whether Dev is revealed or hidden
   - Prevent normal Home click when dragging
   - Handle "snap back" if drag released early

3. **Layout Recalculation (0.5 complexity points)**
   - When Home moves up, other tiles might need adjustment
   - Or keep them static (probably fine)

4. **Animation Polish (0.5 complexity points)**
   - Smooth drag following finger/mouse
   - Snap animation when released
   - Threshold detection (e.g., must drag 50px to trigger)

5. **Edge Cases (1 complexity point)**
   - What if user drags down instead of up?
   - What if Dev is revealed and user tries to center on Home?
   - How to "close" Dev (drag Home back down?)

### Total Complexity Breakdown
- Base functionality: **2/10** (very simple - just move tile)
- Gesture detection: **2/10** (moderate - distinguish drag from click)
- State management: **1/10** (simple - boolean flag)
- Polish & UX: **2/10** (moderate - feel good, handle edge cases)
- **Total: 7/10** (doable with some effort)

## Implementation Plan

### Phase 1: Basic Drag Detection (30 min)

Add drag listeners to Home tile:

```javascript
// static/scripts/dragHome.js (NEW FILE)

let dragStartY = 0;
let isDragging = false;
let isDevRevealed = false;

function initHomeDrag() {
    const homeTile = document.querySelector('[data-title="Home"]');
    const devTile = document.querySelector('[data-title="Dev"]'); // Initially hidden

    homeTile.addEventListener('pointerdown', (e) => {
        dragStartY = e.clientY;
        isDragging = false; // Not dragging yet, just pressed
    });

    homeTile.addEventListener('pointermove', (e) => {
        if (dragStartY === 0) return; // Not pressed

        const deltaY = e.clientY - dragStartY;

        // If moved more than 10px vertically, it's a drag (not a click)
        if (Math.abs(deltaY) > 10) {
            isDragging = true;
            e.preventDefault(); // Prevent click

            // Move Home tile (follow finger/mouse)
            const currentTop = parseFloat(homeTile.style.top);
            homeTile.style.top = `${currentTop + deltaY}px`;
            dragStartY = e.clientY; // Update for next move
        }
    });

    homeTile.addEventListener('pointerup', (e) => {
        if (isDragging) {
            // Check if dragged far enough to reveal Dev
            const movedDistance = dragStartY - e.clientY; // Negative = up

            if (movedDistance > 100) { // Threshold: 100px up
                revealDevTile();
            } else {
                snapHomeBack();
            }
        }

        dragStartY = 0;
        isDragging = false;
    });
}

function revealDevTile() {
    const homeTile = document.querySelector('[data-title="Home"]');
    const devTile = document.querySelector('[data-title="Dev"]');

    // Move Home up
    homeTile.style.top = '20%'; // Move to top

    // Show Dev
    devTile.style.display = 'block';
    devTile.style.opacity = '1';

    isDevRevealed = true;
}

function snapHomeBack() {
    const homeTile = document.querySelector('[data-title="Home"]');

    // Snap back to original position
    homeTile.style.top = '50%'; // Center (original)

    isDevRevealed = false;
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', initHomeDrag);
```

### Phase 2: Hide Dev Initially (10 min)

```javascript
// static/scripts/tileData.js

window.tileInfo = {
    // ... existing tiles ...

    "Dev": [
        [0, 0],  // Same position as Home (underneath)
        `
        Development Tools
        <br><br>
        🔓 Secret unlocked!
        `,
        ``
    ],
};

// Mark Dev as initially hidden
window.hiddenTiles = ["Dev"];
```

```javascript
// static/scripts/tileCreation.js - Add after creating tile

// Hide tiles that should be initially hidden
if (window.hiddenTiles && window.hiddenTiles.includes(title)) {
    tileWrapper.style.display = 'none';
    tileWrapper.style.opacity = '0';
}
```

### Phase 3: Prevent Normal Click When Dragging (5 min)

```javascript
// static/scripts/map.js - Modify handleTileClick

window.handleTileClick = function(e, container) {
    // NEW: Don't handle click if it was a drag
    if (window.isDragging) {
        return;
    }

    // Don't handle tile click if it was actually the button that should be clicked
    if (e.target.classList.contains('button')) {
        return;
    }

    // ... existing click logic
}
```

### Phase 4: Polish & Snap Animation (15 min)

```css
/* static/css/map.css */

.tile-container {
    /* ... existing styles ... */
    transition: all 0.4s cubic-bezier(0.25, 0.8, 0.25, 1); /* Smooth spring */
}

.tile-container.dragging {
    transition: none; /* No animation while actively dragging */
}

.tile-container.dev-revealed {
    z-index: 1000; /* Bring to front */
    transform: scale(1.05); /* Slight grow effect */
}
```

### Phase 5: Add Close Gesture (10 min)

Allow dragging Home back down to hide Dev:

```javascript
function snapHomeBack() {
    const homeTile = document.querySelector('[data-title="Home"]');
    const devTile = document.querySelector('[data-title="Dev"]');

    // Snap Home back to center
    homeTile.style.top = '50%';

    // Hide Dev with fade
    devTile.style.opacity = '0';
    setTimeout(() => {
        devTile.style.display = 'none';
    }, 400); // After transition

    isDevRevealed = false;
}
```

## Alternative: Swipe Instead of Drag

**Simpler approach** (reduces complexity to **5/10**):

Instead of continuous drag-and-follow, use discrete swipe detection:

```javascript
// Detect swipe up on Home tile
let touchStartY = 0;

homeTile.addEventListener('touchstart', (e) => {
    touchStartY = e.touches[0].clientY;
});

homeTile.addEventListener('touchend', (e) => {
    const touchEndY = e.changedTouches[0].clientY;
    const swipeDistance = touchStartY - touchEndY;

    if (swipeDistance > 50) { // Swiped up
        revealDevTile();
    }
});
```

**Benefits:**
- ✅ Simpler (no continuous tracking)
- ✅ Fewer edge cases
- ✅ Easier to distinguish from click
- ❌ Less "tactile" feel (no drag-and-follow)

## Recommendation

### Go with **Swipe Approach** (5/10 complexity)

**Why:**
1. **Simpler implementation** - Less code, fewer bugs
2. **Clear gesture** - Swipe up is unambiguous
3. **Mobile-friendly** - Works great on phones
4. **Quick to build** - 30-45 minutes total
5. **Easy to polish** - Add particle effects, sound, etc.

### User Experience

1. **Discovery:**
   - Subtle hint? (Home tile pulses occasionally)
   - Or completely secret (users discover by accident)
   - Or tooltip: "Swipe up on Home for dev tools"

2. **Interaction:**
   - Swipe up on Home → Home slides up, Dev fades in
   - Click Dev tile → Expands with VS Code/AgentBridge buttons
   - Swipe down on Home (or click Home again) → Hides Dev

3. **Visual Feedback:**
   - Dev tile glows when revealed
   - Home tile darkens/dims slightly
   - Background darkens (focus on Dev)

## Files to Create/Modify

```
static/scripts/dragHome.js         - NEW: Swipe detection logic
static/scripts/tileData.js         - Add Dev tile, mark as hidden
static/scripts/tileCreation.js     - Hide initially hidden tiles
static/css/map.css                 - Add .dev-revealed, transition styles
static/scripts/map.js              - Prevent click when swiping
```

## Timeline Estimate

- **Swipe detection:** 15 minutes
- **Hide/show logic:** 10 minutes
- **Prevent click conflict:** 5 minutes
- **CSS polish:** 10 minutes
- **Testing & tweaks:** 15 minutes
- **Total: ~1 hour**

## My Rating: 7/10 → 5/10 with Swipe

**Original drag-and-follow:** 7/10 (doable but moderate complexity)
**Swipe gesture:** 5/10 (very doable, low complexity)

**Recommended:** Go with swipe gesture. It's:
- ✅ Cleaner UX
- ✅ Easier to implement
- ✅ More reliable
- ✅ Fun Easter egg feel
- ✅ Mobile-optimized

Want me to implement the swipe version?
