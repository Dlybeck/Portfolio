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
    const offsetY = 52 - centerPos.top;

    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;
        const tilePos = positions[tileTitle];
        if (!tilePos) {
            console.error(`No position found for tile: ${tileTitle}`);
            return;
        }
        tile.style.left = `${tilePos.left + offsetX}%`;
        tile.style.top  = `${tilePos.top  + offsetY}%`;
    });

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

    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;
        const tilePos = positions[tileTitle];
        if (!tilePos) return;
        tile.style.left = `${tilePos.left + offsetX}%`;
        tile.style.top  = `${tilePos.top  + offsetY}%`;
    });

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
