//Listen for when page is ready to load in the tiles
document.addEventListener('DOMContentLoaded', function() {
    // Tiles go into the .tile-layer sub-container (fixed 100vh box, so
    // tile % positions stay stable when .map itself grows with paper).
    window.container = document.querySelector(".tile-layer");
    
    // Calculate initial position data
    let [positions, , ] = window.calculatePositions();
    window.positions = positions;

    // Create initial tiles
    const createdTiles = new Set();
    Object.keys(window.tilesData).forEach(title => {
        if (!createdTiles.has(title)) {
            window.createTile(title);
            createdTiles.add(title);
        }

        window.tilesData[title].forEach(childTitle => {
            if (!createdTiles.has(childTitle)) {
                window.createTile(childTitle);
                createdTiles.add(childTitle);
            }
        });
    });

    // Create Dev tile (not in tilesData, but needs to be created before centering)
    if (!createdTiles.has('Dev')) {
        window.createTile('Dev');
        createdTiles.add('Dev');
    }

    // Add click handlers
    const tileContainers = document.querySelectorAll('.tile-container');
    tileContainers.forEach(container => {
        const tileElement = container.querySelector('.tile');
        const buttonElement = container.querySelector('.button');

        //check for tile click
        tileElement.addEventListener('click', function(e) {
            window.handleTileClick(e, container);
        });

        //check for go button click
        if (buttonElement) {
            buttonElement.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    });

    // Initialize URL handling (this calls centerOnTile, which sets the
    // wall's parallax CSS variables to the correct initial position).
    window.addEventListener('hashchange', window.checkUrlHash);
    window.checkUrlHash();

    // Enable wall parallax transition ONLY after the initial center has
    // been painted — otherwise the wall animates from (0,0) to the
    // correct spot on every refresh, which looks like it's "flying in"
    // while the papers are already in place. Two RAFs: first settles
    // layout, second runs after paint, then the transition is safe to
    // enable for subsequent tile clicks.
    requestAnimationFrame(() => {
        requestAnimationFrame(() => {
            const mapEl = document.querySelector('.map');
            if (mapEl) mapEl.classList.add('wall-transition-ready');
        });
    });
});