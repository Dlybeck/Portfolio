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
const SCRAP_VARIANTS = [
    "scrap-ruled", "scrap-graph", "scrap-plain", "scrap-kraft", "scrap-index",
    "scrap-legal", "scrap-dotgrid", "scrap-manila", "scrap-receipt", "scrap-napkin"
];
// Shape (clip-path) variants — ONLY ripped/torn looks. Clean diagonal
// cuts (slant-left/right) were removed because a paper scrap with a
// straight diagonal edge looks like it was cut with scissors, not
// ripped; that's inconsistent with the "scraps of paper" aesthetic.
// "shape-rect" is the no-op default and is duplicated to bias most
// scraps toward plain rectangles.
const SCRAP_SHAPES = [
    "shape-rect", "shape-rect", "shape-rect", "shape-rect",
    "shape-torn-bottom", "shape-torn-top", "shape-torn-both",
    "shape-corner-bite", "shape-ripped-side"
];
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
    // Independent "channels" by dividing the hash down
    const a = h;
    const b = (h / 7)     | 0;
    const c = (h / 53)    | 0;
    const d = (h / 211)   | 0;
    const e = (h / 1031)  | 0;
    const f = (h / 3779)  | 0;
    const g = (h / 9973)  | 0;
    const i = (h / 19937) | 0;
    const j = (h / 39119) | 0;

    return {
        rot:                ((a % 1000) / 1000 * 10 - 5).toFixed(2) + "deg",  // -5..+5
        rotExpanded:        ((b % 1000) / 1000 * 8  - 4).toFixed(2) + "deg",  // -4..+4
        jitterX:            ((c % 1000) / 1000 * 8  - 4).toFixed(2) + "px",   // -4..+4
        jitterY:            ((d % 1000) / 1000 * 8  - 4).toFixed(2) + "px",
        tapeAngle:          ((e % 1000) / 1000 * 16 - 8).toFixed(2) + "deg",  // -8..+8
        colorIdx:           a,
        variantIdx:         b,
        fontIdx:            c,
        inkIdx:             d,
        hasTape:            (e % 2) === 0,
        // Base shape index — only applied to scraps (stickies keep their curl).
        shapeIdx:           i,
        // Independent channels for the expanded (cover) paper so it can
        // be a visually distinct scrap from the one underneath.
        expandedVariantIdx: f,
        expandedHasTape:    (g % 2) === 1,
        expandedShapeIdx:   j,
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

    // Variant class for the BASE scrap (on the tile-container so CSS can
    // scope `.tile-container.<variant> .tile-base`). The expanded cover
    // gets its own independently-hashed variant further down, applied to
    // the .tile-expanded element directly — so base and cover are
    // different pieces of paper from the same family.
    if (paperType === "sticky") {
        tileWrapper.classList.add(pick(STICKY_COLORS, seed.colorIdx));
        // Stickies are self-adhesive — NO tape.
        // Pick a folded-corner variant per tile. Pool is balanced
        // left/right with a flat option so the wall has visible variety
        // in fold direction, not just position on the right side.
        const STICKY_FOLDS = [
            'sticky-fold-br',     // bottom-right (small)
            'sticky-fold-tr',     // top-right
            'sticky-fold-bl',     // bottom-left
            'sticky-fold-tl',     // top-left
            'sticky-fold-big-br', // bigger bottom-right
            'sticky-fold-big-bl', // bigger bottom-left
            'sticky-fold-big-tl', // bigger top-left
            'sticky-fold-flat',   // no fold
        ];
        // Mix the salted hash through a Knuth-style multiplier for
        // better distribution — without this, the small set of hub
        // titles can land in the same hash buckets and produce biased
        // variant assignments.
        function rehash(x) {
            x = (x ^ (x >>> 16)) * 0x85ebca6b >>> 0;
            x = (x ^ (x >>> 13)) * 0xc2b2ae35 >>> 0;
            return (x ^ (x >>> 16)) >>> 0;
        }
        const foldH = rehash(window.stableHash(title + '|fold'));
        tileWrapper.classList.add(STICKY_FOLDS[foldH % STICKY_FOLDS.length]);
    } else {
        tileWrapper.classList.add(pick(SCRAP_VARIANTS, seed.variantIdx));
        // Independent shape (rip/asymmetry) for the base scrap.
        tileWrapper.classList.add(pick(SCRAP_SHAPES, seed.shapeIdx));
        // Scraps aren't self-adhesive — always need tape to hold them down.
        tileWrapper.classList.add("has-tape");
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

    // Hub tiles (sticky paper type — no leaf page) get a handwritten
    // underline on the title via a pseudo-element + SVG mask. Each
    // tile picks an SVG shape, flip direction, and rotation from
    // independent rehashes so neighboring tiles don't accidentally
    // share the same look.
    if (paperType === "sticky") {
        const UNDERLINE_MASKS = [
            // 1. Single wavy line (uneven peaks)
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7' preserveAspectRatio='none'><path d='M2,4 Q15,1 28,4 Q40,7 55,3 Q70,1 85,4 Q93,5 98,3' stroke='white' stroke-width='2.2' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>\")",
            // 2. Double-pass scribble (one above, one below, both wavy)
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7' preserveAspectRatio='none'><path d='M3,3 Q30,2 50,3.5 T96,3' stroke='white' stroke-width='1.6' fill='none' stroke-linecap='round'/><path d='M5,5.2 Q35,4 60,5.4 T94,5' stroke='white' stroke-width='1.4' fill='none' stroke-linecap='round'/></svg>\")",
            // 3. Big single-S squiggle
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7' preserveAspectRatio='none'><path d='M1,4 C12,1 22,6 32,4 S52,1 64,4 S84,7 99,3.5' stroke='white' stroke-width='2.1' fill='none' stroke-linecap='round'/></svg>\")",
            // 4. Quick stroke with a tail flick
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7' preserveAspectRatio='none'><path d='M2,4.5 Q35,2 70,4 Q85,5 95,3 Q97,2.6 99,2' stroke='white' stroke-width='2.2' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>\")",
            // 5. Tight zigzag — short alternating peaks
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7' preserveAspectRatio='none'><path d='M2,3 L12,5 L22,3 L34,5.5 L46,2.8 L58,5.2 L70,3 L82,5 L94,3.2 L98,4' stroke='white' stroke-width='1.8' fill='none' stroke-linecap='round' stroke-linejoin='round'/></svg>\")",
            // 6. Slow undulation that fades at one end (variable thickness via stroke change)
            "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7' preserveAspectRatio='none'><path d='M3,3.6 Q22,2 42,4 Q60,5.6 78,3.4 Q88,2.4 96,4.6' stroke='white' stroke-width='2.6' fill='none' stroke-linecap='round'/></svg>\")",
        ];

        // Three independent rehashes from the title's stableHash —
        // avoids "same shape next to same shape" by making shape, flip,
        // and rotation use uncorrelated bit slices.
        function rehash(x) {
            x = (x ^ (x >>> 16)) * 0x85ebca6b >>> 0;
            x = (x ^ (x >>> 13)) * 0xc2b2ae35 >>> 0;
            return (x ^ (x >>> 16)) >>> 0;
        }
        const h0 = window.stableHash(title);
        const h1 = rehash(h0);
        const h2 = rehash(h1);
        const h3 = rehash(h2);

        const idx = h1 % UNDERLINE_MASKS.length;
        const flip = (h2 % 2) === 0 ? 1 : -1;
        const rot = ((h3 % 100) / 100 - 0.5) * 4; // -2..+2 deg

        tileWrapper.style.setProperty('--title-underline-mask', UNDERLINE_MASKS[idx]);
        tileWrapper.style.setProperty('--title-underline-rot', rot.toFixed(2) + 'deg');
        tileWrapper.style.setProperty('--title-underline-flip', flip);
    }

    // ---- .tile-base : outer wrapper (handles rotation/jitter). ----
    // Structure:
    //   .tile-base            (outer, NO clip-path; tape lives here so it
    //                         can overhang past the paper's shape edges)
    //     .paper-body         (inner, carries background + clip-path/shape)
    //       .scrap-title      (text content, stays inside the clip)
    //     .tape               (sibling of .paper-body, not clipped)
    //
    // The legacy .tile class stays on the outer element so map.js's
    // `.querySelector('.tile')` click binding keeps working.
    const base = document.createElement('div');
    base.className = 'tile tile-base';

    const baseBody = document.createElement('div');
    baseBody.className = 'paper-body';
    base.appendChild(baseBody);

    const baseTitle = document.createElement('h2');
    baseTitle.className = 'scrap-title';
    baseTitle.textContent = title;
    baseBody.appendChild(baseTitle);

    // Tape as a sibling of paper-body (scraps only — stickies skip tape).
    if (paperType !== 'sticky') {
        const tape = document.createElement('div');
        tape.className = 'tape';
        base.appendChild(tape);
    }

    // ---- .tile-expanded : larger cover paper (same nested structure) ----
    // .tile-expanded is the outer animation host. .paper-body inside it
    // carries the background + clip-path. Tape is a sibling of .paper-body
    // so it can overhang past any torn/rip shape.
    const expanded = document.createElement('div');
    expanded.className = 'tile-expanded';
    const expandedBody = document.createElement('div');
    expandedBody.className = 'paper-body';
    expanded.appendChild(expandedBody);
    if (paperType === "sticky") {
        const baseIdx = seed.colorIdx % STICKY_COLORS.length;
        const expIdx  = (seed.expandedVariantIdx + 2) % STICKY_COLORS.length;
        const finalIdx = (expIdx === baseIdx)
            ? (expIdx + 1) % STICKY_COLORS.length
            : expIdx;
        expanded.classList.add(STICKY_COLORS[finalIdx]);
        // Stickies don't need tape — self-adhesive.
    } else {
        const baseIdx = seed.variantIdx % SCRAP_VARIANTS.length;
        const expIdx  = (seed.expandedVariantIdx + 2) % SCRAP_VARIANTS.length;
        const finalIdx = (expIdx === baseIdx)
            ? (expIdx + 1) % SCRAP_VARIANTS.length
            : expIdx;
        expanded.classList.add(SCRAP_VARIANTS[finalIdx]);
        expanded.classList.add(pick(SCRAP_SHAPES, seed.expandedShapeIdx));
        // Covers on non-sticky papers also need tape.
        expanded.classList.add("has-tape");
    }

    const expTitle = document.createElement('h2');
    expTitle.className = 'expanded-title';
    expTitle.textContent = title;
    expandedBody.appendChild(expTitle);

    const expText = document.createElement('p');
    expText.className = 'expanded-text';
    expText.innerHTML = texts[title] || '';
    expandedBody.appendChild(expText);

    // "open" link — handwritten on the paper, with per-tile variety in
    // the wording, font, ink color, rotation, and decoration. Same hash
    // seed used for tile styling, so a given tile always renders the
    // same way across reloads.
    const route = routes[title];
    const isHubWithoutPage = window.tilesData.hasOwnProperty(title) && route === '/';
    if (route && !isHubWithoutPage) {
        const openLink = document.createElement('a');
        openLink.className = 'expanded-open';
        openLink.href = route;
        openLink.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            window.openPage(route);
        });

        const h = window.stableHash(title);
        const OPEN_TEXTS = [
            'open →', '→ open', 'see ▸', 'open it', 'go →',
            'open this', 'check it out',
        ];
        const OPEN_INKS = [
            '#a82828', '#1a3a6e', '#1b1b1b', '#5a3818', '#234a3e',
        ];
        const OPEN_FONTS = [
            "'Architects Daughter', sans-serif",
            "'Patrick Hand', sans-serif",
            "'Gochi Hand', sans-serif",
            "'Kalam', sans-serif",
        ];
        // Every link has SOME sort of decoration (underline, circle, or
        // box) — never plain. Each tile picks one deterministically.
        const OPEN_DECORATIONS = ['underline', 'circled', 'boxed'];

        const textIdx = ((h / 89)   | 0) % OPEN_TEXTS.length;
        const inkIdx  = ((h / 211)  | 0) % OPEN_INKS.length;
        const fontIdx = ((h / 547)  | 0) % OPEN_FONTS.length;
        const decoIdx = ((h / 1361) | 0) % OPEN_DECORATIONS.length;
        const rotDeg  = ((((h / 4099) | 0) % 1000) / 1000 * 6 - 3).toFixed(2);

        openLink.textContent = OPEN_TEXTS[textIdx];
        openLink.style.setProperty('--open-ink', OPEN_INKS[inkIdx]);
        openLink.style.setProperty('--open-font', OPEN_FONTS[fontIdx]);
        openLink.style.setProperty('--open-rot', rotDeg + 'deg');
        openLink.classList.add('deco-' + OPEN_DECORATIONS[decoIdx]);

        expandedBody.appendChild(openLink);
    }

    // Keep a legacy `.button` reference for existing map.js code paths that
    // query for it; we hide it visually (it's display:none) but the DOM node
    // existing prevents null-derefs in older logic.
    const legacyButton = document.createElement('a');
    legacyButton.className = 'button';
    legacyButton.style.display = 'none';
    legacyButton.href = route || '';
    expandedBody.appendChild(legacyButton);

    // Tape as a sibling of expanded's paper-body (scraps only).
    if (paperType !== 'sticky') {
        const expandedTape = document.createElement('div');
        expandedTape.className = 'tape';
        expanded.appendChild(expandedTape);
    }

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
                // Pick exit direction from TILE GEOMETRY, not scroll state.
                // When a new tile becomes the center, every other tile shifts
                // by (new_center - old_center). The de-centered tile moves in
                // viewport by (this_tile.top - new_center.top). We want its
                // cover to follow that motion (same direction), so the cover
                // rides off with the tile rather than opposing the layout.
                //   this.top > center.top → tile moves DOWN → cover exits DOWN
                //   this.top < center.top → tile moves UP   → cover exits UP
                //   tied → fall back to scroll direction (if any), then UP.
                const centerPos = window.positions[centerTitle];
                const thisPos = window.positions[tileTitle];
                let leaveClass = 'cover-leaving-up';
                if (centerPos && thisPos) {
                    if (thisPos.top > centerPos.top) leaveClass = 'cover-leaving-down';
                    else if (thisPos.top < centerPos.top) leaveClass = 'cover-leaving-up';
                    else if ((window._lastScrollDir || 0) < 0) leaveClass = 'cover-leaving-down';
                }
                tile.classList.add(leaveClass);

                const prev = window._coverLeaveTimers.get(tileTitle);
                if (prev) clearTimeout(prev);
                const t = setTimeout(() => {
                    tile.classList.remove('cover-leaving-up', 'cover-leaving-down');
                    window._coverLeaveTimers.delete(tileTitle);
                }, 540); // slightly longer than the 0.5s CSS animation
                window._coverLeaveTimers.set(tileTitle, t);
            }
        }
    });

    if (window.updateChalkArrows) window.updateChalkArrows(centerTitle);
};
