//Listen for when page is ready to load in the tiles
document.addEventListener('DOMContentLoaded', function() {
    // Grab the map
    window.container = document.querySelector(".map");
    
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

    // Initialize URL handling
    window.addEventListener('hashchange', window.checkUrlHash);
    window.checkUrlHash();
});