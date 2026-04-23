/**
 * Tile creation — paper-table theme.
 *
 * Each tile is TWO stacked papers in the same .tile-container:
 *   .tile-base     — small scrap/sticky always visible
 *   .tile-expanded — larger paper that COVERS the base when centered
 *
 * Per-tile variability (rotation, color, paper variant, font) is derived from
 * a stable hash of the title so reloads look the same but every tile differs.
 */

// Option pools used for stable-hash selection
const STICKY_COLORS = ["sticky-yellow", "sticky-pink", "sticky-blue", "sticky-green", "sticky-orange"];
const SCRAP_VARIANTS = ["scrap-ruled", "scrap-graph", "scrap-plain", "scrap-kraft", "scrap-index"];
const TILE_FONTS = ["var(--font-hand-casual)", "var(--font-hand-neat)", "var(--font-hand-thin)"];
const INK_COLORS_SCRAP = ["var(--ink-blue)", "var(--ink-black)", "var(--ink-pencil)"];
const INK_COLORS_STICKY = ["var(--ink-black)", "var(--ink-blue)", "var(--ink-red)"];

function pick(arr, seed) { return arr[seed % arr.length]; }

/**
 * Derive stable per-tile presentation variables from a title.
 * Returns the values as strings ready to drop into styles/classes.
 */
function tileStyleSeed(title) {
    const h = window.stableHash(title);
    // 5 independent "channels" by dividing the hash down
    const a = h;
    const b = (h / 7)    | 0;
    const c = (h / 53)   | 0;
    const d = (h / 211)  | 0;
    const e = (h / 1031) | 0;

    return {
        rot:          ((a % 1000) / 1000 * 10 - 5).toFixed(2) + "deg",       // -5..+5
        rotExpanded:  ((b % 1000) / 1000 * 8  - 4).toFixed(2) + "deg",       // -4..+4
        jitterX:      ((c % 1000) / 1000 * 8  - 4).toFixed(2) + "px",        // -4..+4
        jitterY:      ((d % 1000) / 1000 * 8  - 4).toFixed(2) + "px",
        tapeAngle:    ((e % 1000) / 1000 * 16 - 8).toFixed(2) + "deg",       // -8..+8
        colorIdx:     a,
        variantIdx:   b,
        fontIdx:      c,
        inkIdx:       d,
        hasTape:      (e % 2) === 0,
        torn:         (a % 3) === 0, // ~1/3 of scraps
    };
}

/**
 * Create and return a tile wrapper (paper-table version).
 * @param {string} title
 * @returns {HTMLElement}
 */
window.createTile = function(title) {
    const [ , texts, routes ] = window.calculatePositions();
    const paperType = window.getPaperType(title); // "sticky" | "scrap"
    const seed = tileStyleSeed(title);

    // ---- Container ----
    const tileWrapper = document.createElement('div');
    tileWrapper.className = `tile-container ${paperType}`;
    tileWrapper.dataset.title = title;

    // Paper-family specific variant class
    if (paperType === "sticky") {
        tileWrapper.classList.add(pick(STICKY_COLORS, seed.colorIdx));
        if (seed.hasTape) tileWrapper.classList.add("has-tape");
    } else {
        tileWrapper.classList.add(pick(SCRAP_VARIANTS, seed.variantIdx));
        if (seed.torn) tileWrapper.classList.add("torn");
    }

    // Per-tile CSS variables (stable)
    const inkPool = paperType === "sticky" ? INK_COLORS_STICKY : INK_COLORS_SCRAP;
    tileWrapper.style.setProperty('--rot',          seed.rot);
    tileWrapper.style.setProperty('--rot-expanded', seed.rotExpanded);
    tileWrapper.style.setProperty('--jitter-x',     seed.jitterX);
    tileWrapper.style.setProperty('--jitter-y',     seed.jitterY);
    tileWrapper.style.setProperty('--tape-angle',   seed.tapeAngle);
    tileWrapper.style.setProperty('--tile-font',    pick(TILE_FONTS, seed.fontIdx));
    tileWrapper.style.setProperty('--ink-color',    pick(inkPool,    seed.inkIdx));

    // ---- .tile-base : the small always-visible scrap/sticky ----
    // (we keep the legacy .tile class on this element too so map.js's
    //  existing click binding `.querySelector('.tile')` still works)
    const base = document.createElement('div');
    base.className = 'tile tile-base';

    const baseTitle = document.createElement('h2');
    baseTitle.className = 'scrap-title';
    baseTitle.textContent = title === 'Dev' ? 'Dev' : title;
    base.appendChild(baseTitle);

    // ---- .tile-expanded : larger paper that covers the base when centered ----
    const expanded = document.createElement('div');
    expanded.className = 'tile-expanded';

    const expTitle = document.createElement('h2');
    expTitle.className = 'expanded-title';
    expTitle.textContent = title === 'Dev' ? 'Dev Hub' : title;
    expanded.appendChild(expTitle);

    const expText = document.createElement('p');
    expText.className = 'expanded-text';
    expText.innerHTML = texts[title] || '';
    expanded.appendChild(expText);

    // "open →" link — only for tiles that actually have a leaf route (scrap + Dev).
    // Hub stickies (keys of tilesData other than Home/Dev) have routes "/" in
    // tileData.js, which would just reload the current map, so we skip them.
    const route = routes[title];
    const isHubWithoutPage = window.tilesData.hasOwnProperty(title) && route === '/';
    if (route && !isHubWithoutPage) {
        const openLink = document.createElement('a');
        openLink.className = 'expanded-open';
        openLink.href = route;
        openLink.textContent = title === 'Dev' ? 'enter →' : 'open →';
        openLink.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            window.openPage(route);
        });
        expanded.appendChild(openLink);
    }

    // Keep a legacy `.button` reference for existing map.js code paths that
    // query for it; we hide it visually (it's display:none) but the DOM node
    // existing prevents null-derefs in older logic.
    const legacyButton = document.createElement('a');
    legacyButton.className = 'button';
    legacyButton.style.display = 'none';
    legacyButton.href = route || '';
    expanded.appendChild(legacyButton);

    // Preserve the legacy .tile-contents/.tile-title/.tile-text element names too,
    // pointing them at the real nodes — so older code that queries these still
    // finds SOMETHING valid rather than null. We don't actually rely on them.
    baseTitle.classList.add('tile-title');
    expText.classList.add('tile-text');

    tileWrapper.appendChild(base);
    tileWrapper.appendChild(expanded);

    container.appendChild(tileWrapper);

    // Position using existing grid math
    positionTile(tileWrapper, title);

    return tileWrapper;
};

/**
 * Position a tile absolutely on the map via grid math (unchanged from original).
 * @param {HTMLElement} tile
 * @param {string} title
 */
window.positionTile = function(tile, title) {
    const pos = window.positions[title];
    if (pos) {
        tile.style.position = 'absolute';
        tile.style.left = `${pos.left}%`;
        tile.style.top  = `${pos.top}%`;
        // Keep the wrapper on-center; inner papers carry jitter/rotation.
        tile.style.transform = 'translate(-50%, -50%)';
    } else {
        console.error("No position found");
    }
};

/**
 * Update tile visibility based on which tile is centered.
 * Physical-paper rule: the cover paper on a de-centered tile doesn't just
 * fade out. It plays a short "sweep off to the right" animation (driven by
 * the .cover-leaving class + CSS keyframe) that's horizontal so map-pan
 * can't catch up with it and freeze it mid-screen.
 * @param {string} centerTitle
 */
window._coverLeaveTimers = window._coverLeaveTimers || new Map();

window.updateVisibility = function(centerTitle) {
    const connectedTiles = tilesData[centerTitle] || [];
    const parentTitle = Object.entries(tilesData).find(([_, children]) =>
        children.includes(centerTitle)
    )?.[0];

    const visibleTiles = [centerTitle, ...connectedTiles];
    if (parentTitle) visibleTiles.push(parentTitle);

    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;
        if (tileTitle === 'Dev') return;

        const wasExpanded = tile.classList.contains('expanded');
        const shouldBeExpanded = (tileTitle === centerTitle);

        // If a user re-selects a tile that's in the middle of its exit
        // sweep, cancel the sweep and re-enter cleanly.
        if (shouldBeExpanded) {
            tile.classList.remove('cover-leaving-up', 'cover-leaving-down');
            const pending = window._coverLeaveTimers.get(tileTitle);
            if (pending) { clearTimeout(pending); window._coverLeaveTimers.delete(tileTitle); }
        }

        tile.classList.remove('expanded', 'connected', 'dimmed');

        if (shouldBeExpanded) {
            tile.classList.add('expanded');
        } else {
            tile.classList.add(visibleTiles.includes(tileTitle) ? 'connected' : 'dimmed');
            // Kick off the sweep-off animation only if this tile was the
            // previously-centered one. Other tiles have no cover on-stage.
            if (wasExpanded) {
                // Pick the exit direction based on last scroll direction.
                // User scrolling down (map panning up) → cover exits upward.
                // User scrolling up (map panning down) → cover exits downward.
                // Default (no recent scroll) → upward (plays nice with tile-
                // click flows which usually don't involve a scroll state).
                const dir = window._lastScrollDir || 0;
                const leaveClass = (dir < 0) ? 'cover-leaving-down' : 'cover-leaving-up';
                tile.classList.add(leaveClass);

                const prev = window._coverLeaveTimers.get(tileTitle);
                if (prev) clearTimeout(prev);
                const t = setTimeout(() => {
                    tile.classList.remove('cover-leaving-up', 'cover-leaving-down');
                    window._coverLeaveTimers.delete(tileTitle);
                }, 380); // slightly longer than the 0.35s CSS animation
                window._coverLeaveTimers.set(tileTitle, t);
            }
        }
    });
};
