/**
 * Tile movement — paper-table theme.
 *
 * Centering math is unchanged: we shift every tile's left/top so the named
 * tile ends up at ~50% center of the viewport. What's gone:
 *   - body-background parallax (the tabletop texture lives on .map now and
 *     pans naturally via mapPan.js when a page is open)
 *
 * The "expanded" state is no longer a resize of the tile — updateVisibility
 * in tileCreation.js simply toggles the .expanded class, which makes the
 * already-rendered .tile-expanded child slide in from off-stage to cover the
 * base paper. No single element mutates.
 */

/**
 * Apply a transform string to the tile-layer. On the very first call after
 * page load, skip the CSS transition so the initial position lands without
 * an animation from (0,0). Subsequent calls animate via the CSS rule.
 */
function _applyLayerTransform(tileLayer, transformStr) {
    if (!window._layerInitialized) {
        tileLayer.style.transition = 'none';
        tileLayer.style.transform = transformStr;
        void tileLayer.offsetHeight;
        tileLayer.style.transition = '';
        window._layerInitialized = true;
    } else {
        tileLayer.style.transform = transformStr;
    }
}

/**
 * Center the map on a named tile.
 * @param {string} title
 */
window.centerOnTile = function(title) {
    const centerPos = positions[title];
    if (!centerPos) {
        console.error(`No position found for tile: ${title}`);
        return;
    }

    const offsetX = 50 - centerPos.left;
    const offsetY = 50 - centerPos.top;

    // Pan by translating the entire tile-layer in ONE GPU-composited
    // transform — no per-tile layout. Each tile stays pinned at its
    // tileInfo position; only the layer moves.
    // Using svw/svh (small viewport units) so positions stay aligned
    // with the chrome-visible safe area on mobile — matches the
    // .tile-layer height: 100svh in map.css.
    const tileLayer = document.querySelector('.tile-layer');
    if (tileLayer) {
        // Convert percentage offsets to pixels using the layer's rendered
        // size (100svw × 100svh) so the CSS transition can animate the
        // value without Chrome dropping it (it dislikes svw/svh in
        // transition-bound transform).
        const lr = tileLayer.getBoundingClientRect();
        _applyLayerTransform(tileLayer, `translate3d(${(offsetX/100)*lr.width}px, ${(offsetY/100)*lr.height}px, 0)`);
    }

    // Wall pans 1:1 with the tile-layer — same offset, vw/vh units so
    // it matches the layer's percentage-based pan.
    const mapEl = document.querySelector('.map');
    if (mapEl) {
        mapEl.style.setProperty('--wall-shift-x', `${-centerPos.left}vw`);
        mapEl.style.setProperty('--wall-shift-y', `${-centerPos.top}vh`);
    }

    window.checkHomeButton();
    updateVisibility(title);
};

/**
 * Reset all tiles to the Home layout.
 */
window.returnHome = function() {
    const homeTile = positions['Home'];
    if (!homeTile) {
        console.error('No position found for Home tile');
        return;
    }

    window.location.hash = encodeURIComponent('Home');

    const offsetX = 50 - homeTile.left;
    const offsetY = 50 - homeTile.top;

    // Single transform on the layer — see centerOnTile for the why.
    const tileLayer = document.querySelector('.tile-layer');
    if (tileLayer) {
        // Convert percentage offsets to pixels using the layer's rendered
        // size (100svw × 100svh) so the CSS transition can animate the
        // value without Chrome dropping it (it dislikes svw/svh in
        // transition-bound transform).
        const lr = tileLayer.getBoundingClientRect();
        _applyLayerTransform(tileLayer, `translate3d(${(offsetX/100)*lr.width}px, ${(offsetY/100)*lr.height}px, 0)`);
    }

    // Reset the wall parallax to origin since we're back at Home.
    const mapEl = document.querySelector('.map');
    if (mapEl) {
        mapEl.style.setProperty('--wall-shift-x', '0rem');
        mapEl.style.setProperty('--wall-shift-y', '0rem');
    }

    updateVisibility('Home');
    window.checkHomeButton(document.body);
};

/**
 * Handle a click on a tile. Center on it and update URL hash.
 */
window.handleTileClick = function(e, container) {
    if (e.target.classList.contains('button') || e.target.classList.contains('expanded-open')) {
        return;
    }
    // If already centered, let the click fall through to the expanded paper's
    // "open →" link (which lives inside the .tile-expanded child).
    if (container.classList.contains('expanded')) {
        return;
    }

    e.preventDefault();
    const title = container.dataset.title;
    window.location.hash = encodeURIComponent(title);
    centerOnTile(title);
};
