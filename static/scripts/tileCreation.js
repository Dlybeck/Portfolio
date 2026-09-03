/** Stable semantic tile construction. Visual worlds are applied separately. */

/**
 * Create and return one semantic Board location.
 * @param {string} title
 * @returns {HTMLElement}
 */
window.createTile = function(title) {
    const [ , texts, routes ] = window.calculatePositions();
    const legacyPresenter = window.legacyPaperTiles;

    // ---- Container ----
    const tileWrapper = document.createElement('div');
    tileWrapper.className = 'tile-container';
    tileWrapper.dataset.title = title;
    const legacyState = legacyPresenter?.decorateContainer(tileWrapper, title);

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
    const base = document.createElement('button');
    base.className = 'tile tile-base';
    base.type = 'button';
    base.tabIndex = -1;
    base.setAttribute('aria-label', `Go to ${title}`);

    const baseBody = document.createElement('div');
    baseBody.className = 'paper-body';
    base.appendChild(baseBody);

    const baseTitle = document.createElement('span');
    baseTitle.className = 'scrap-title';
    baseTitle.textContent = title;
    baseBody.appendChild(baseTitle);

    // Tape as a sibling of paper-body (scraps only — stickies skip tape).
    legacyPresenter?.addTape(base, legacyState);

    // ---- .tile-expanded : larger cover paper (same nested structure) ----
    // .tile-expanded is the outer animation host. .paper-body inside it
    // carries the background + clip-path. Tape is a sibling of .paper-body
    // so it can overhang past any torn/rip shape.
    const expanded = document.createElement('div');
    expanded.className = 'tile-expanded';
    const expandedBody = document.createElement('div');
    expandedBody.className = 'paper-body';
    expanded.appendChild(expandedBody);
    legacyPresenter?.decorateExpanded(expanded, legacyState);

    const expTitle = document.createElement('h2');
    expTitle.className = 'expanded-title';
    expTitle.textContent = title;
    expTitle.tabIndex = -1;
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
        openLink.tabIndex = -1;
        openLink.setAttribute('aria-label', `Open ${title}`);
        openLink.addEventListener('click', (event) => {
            event.preventDefault();
            event.stopPropagation();
            window.openPage(route);
        });
        openLink.addEventListener('keydown', (event) => {
            if (event.key !== ' ') return;
            event.preventDefault();
            event.stopPropagation();
            window.openPage(route);
        });

        openLink.textContent = 'open →';
        legacyPresenter?.decorateAction(openLink, title);

        expandedBody.appendChild(openLink);
    }

    // Keep a legacy `.button` reference for existing map.js code paths that
    // query for it; we hide it visually (it's display:none) but the DOM node
    // existing prevents null-derefs in older logic.
    const legacyButton = document.createElement('a');
    legacyButton.className = 'button';
    legacyButton.style.display = 'none';
    legacyButton.href = route || '';
    legacyButton.tabIndex = -1;
    legacyButton.setAttribute('aria-hidden', 'true');
    expandedBody.appendChild(legacyButton);

    // Tape as a sibling of expanded's paper-body (scraps only).
    legacyPresenter?.addTape(expanded, legacyState);

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
window._coverLeaveCleanups = window._coverLeaveCleanups || new Map();

function clearCoverLeave(tile, tileTitle) {
    const cleanup = window._coverLeaveCleanups.get(tileTitle);
    if (cleanup) cleanup();
    tile.classList.remove('cover-leaving-up', 'cover-leaving-down');
}

function animationMilliseconds(value) {
    const trimmed = value.trim();
    if (trimmed.endsWith('ms')) return Number.parseFloat(trimmed) || 0;
    if (trimmed.endsWith('s')) return (Number.parseFloat(trimmed) || 0) * 1000;
    return 0;
}

function animationFallbackMilliseconds(element) {
    if (!element) return 200;
    const style = getComputedStyle(element);
    const durations = style.animationDuration.split(',').map(animationMilliseconds);
    const delays = style.animationDelay.split(',').map(animationMilliseconds);
    const count = Math.max(durations.length, delays.length);
    let longest = 0;
    for (let index = 0; index < count; index += 1) {
        longest = Math.max(
            longest,
            durations[index % durations.length] + delays[index % delays.length],
        );
    }
    return longest + 200;
}

function startCoverLeave(tile, expanded, tileTitle, leaveClass) {
    clearCoverLeave(tile, tileTitle);
    tile.classList.add(leaveClass);

    let finished = false;
    let fallback = null;
    const finish = () => {
        if (finished) return;
        finished = true;
        expanded?.removeEventListener('animationend', onAnimationEnd);
        if (fallback !== null) clearTimeout(fallback);
        tile.classList.remove('cover-leaving-up', 'cover-leaving-down');
        window._coverLeaveCleanups.delete(tileTitle);
    };
    const onAnimationEnd = (event) => {
        if (event.target === expanded) finish();
    };

    expanded?.addEventListener('animationend', onAnimationEnd);
    // Animation completion owns the normal lifecycle. This timeout is only a
    // fail-closed escape hatch for browsers that suppress animation events.
    fallback = setTimeout(finish, animationFallbackMilliseconds(expanded));
    window._coverLeaveCleanups.set(tileTitle, finish);

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
        requestAnimationFrame(finish);
    }
}

window.updateVisibility = function(centerTitle) {
    const connectedTiles = tilesData[centerTitle] || [];
    const parentTitle = window.parentTitleFor(centerTitle);

    const visibleTiles = [centerTitle, ...connectedTiles];
    if (parentTitle) visibleTiles.push(parentTitle);

    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;

        const wasExpanded = tile.classList.contains('expanded');
        const shouldBeExpanded = (tileTitle === centerTitle);
        const base = tile.querySelector('.tile-base');
        const expanded = tile.querySelector('.tile-expanded');
        const openLink = tile.querySelector('.expanded-open');
        const isConnected = visibleTiles.includes(tileTitle) && !shouldBeExpanded;

        if (base) {
            base.tabIndex = isConnected ? 0 : -1;
            base.setAttribute('aria-hidden', isConnected ? 'false' : 'true');
        }
        if (openLink) openLink.tabIndex = shouldBeExpanded ? 0 : -1;
        if (expanded) {
            expanded.setAttribute('aria-hidden', shouldBeExpanded ? 'false' : 'true');
            // The cover-enter animation starts from a previously hidden
            // element. Make its visible state explicit before focus moves
            // into it; some browsers otherwise retain the inherited hidden
            // visibility for the first animation frame.
            expanded.style.visibility = shouldBeExpanded ? 'visible' : '';
        }

        // If a user re-selects a tile that's in the middle of its exit
        // sweep, cancel the sweep and re-enter cleanly.
        if (shouldBeExpanded) {
            clearCoverLeave(tile, tileTitle);
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
                startCoverLeave(tile, expanded, tileTitle, leaveClass);
            }
        }
    });

    if (window.updateChalkArrows) window.updateChalkArrows(centerTitle);
};
