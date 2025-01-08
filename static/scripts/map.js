document.addEventListener('DOMContentLoaded', function() {
    window.container = document.querySelector(".map");
    
    // Calculate initial positions
    let [positions, texts, routes] = window.calculatePositions();
    window.positions = positions;
    window.texts = texts;
    window.routes = routes;

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

    // Add click handlers
    const tileContainers = document.querySelectorAll('.tile-container');
    tileContainers.forEach(container => {
        const tileElement = container.querySelector('.tile');
        const buttonElement = container.querySelector('.button');

        tileElement.addEventListener('click', function(e) {
            window.handleTileClick(e, container);
        });

        if (buttonElement) {
            buttonElement.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    });

    // Initialize URL handling
    window.addEventListener('hashchange', window.checkUrlHash);
    window.checkUrlHash();
});