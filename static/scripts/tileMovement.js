window.oldBackPosX = 0;
window.oldBackPosY = 0;

/**
 * 
 * @param {string} title - The title of the tile to center on
 * @returns - nothing
 */
window.centerOnTile = function(title) {
    const centerPos = positions[title];

    if (!centerPos) {
        console.error(`No position found for tile: ${title}`);
        return;
    }
    
    // Calculate offsets for tile movement
    const offsetX = 50 - centerPos.left;
    const offsetY = 52 - centerPos.top;
    
    // Move tiles to proper position
    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;
        const tilePos = positions[tileTitle];
        
        if (!tilePos) {
            console.error(`No position found for tile: ${tileTitle}`);
            return;
        }
        
        // Store current width/height before moving
        const currentWidth = tile.style.width;
        const currentHeight = tile.style.height;
        
        // Update pos with new offsets
        tile.style.left = `${tilePos.left + offsetX}%`;
        tile.style.top = `${tilePos.top + offsetY}%`;
        
        // Restore width/height after moving (IDK why but this is needed)
        if (currentWidth && currentHeight) {
            tile.style.width = currentWidth;
            tile.style.height = currentHeight;
        }
    });
    
    // Determine movement direction for the background
    if (centerPos.left > oldBackPosX) {
        moveX = GRID_UNITS; // Move background left
    } else if (centerPos.left < oldBackPosX) {
        moveX = -GRID_UNITS; // Move background right
    }

    if (centerPos.top > oldBackPosY) {
        moveY = GRID_UNITS; // Move background down
    } else if (centerPos.top < oldBackPosY) {
        moveY = -GRID_UNITS; // Move background up
    }
    
    // Update the tracked old positions
    oldBackPosX = centerPos.left/2; // divisor is arbitrary value to change background speed (lower=faster)
    oldBackPosY = centerPos.top/2;
    //Invert since it is background movement
    document.body.style.backgroundPosition = `${-oldBackPosX}rem ${-oldBackPosY}rem`;

    //Check to see if the home button should be visible or not
    window.checkHomeButton();

    // Update the visibility of all tiles based on the center tile
    updateVisibility(title);
}

/**
 * Moves all tiles back to home positions. Back to how the page is intially loaded
 * @returns - Nothing
 */
window.returnHome = function() {
    const homeTile = positions['Home'];
    if (!homeTile) {
        console.error('No position found for Home tile');
        return;
    }

    // Update URL hash to Home
    window.location.hash = encodeURIComponent('Home');

    // Reset offsets to initial positions
    const offsetX = 50 - homeTile.left;
    const offsetY = 50 - homeTile.top;

    // Move all tiles back to the original (home) positions
    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;
        const tilePos = positions[tileTitle];
        
        if (!tilePos) {
            console.error(`No position found for tile: ${tileTitle}`);
            return;
        }

        tile.style.left = `${tilePos.left + offsetX}%`;
        tile.style.top = `${tilePos.top + offsetY}%`;
    });

    // Reset background position
    oldBackPosX = homeTile.left;
    oldBackPosY = homeTile.top;
    document.body.style.backgroundPosition = '0rem 0rem';

    // Update visibility of all tiles with focus on home
    updateVisibility('Home');
    // Check of the home button should be visible or not
    window.checkHomeButton(document.body);
}

/**
 * Runs when a tile is clicked. It centers the screen on the desired tile and updates the url
 * @param {*} e 
 * @param {*} container 
 * @returns 
 */
window.handleTileClick = function(e, container) {
    // Don't handle tile click if it was actually the button that should be clicked
    if (e.target.classList.contains('button')) {
        return;
    }

    // Don't handle tile click if already expanded (tile should be inert when centered)
    if (container.classList.contains('expanded')) {
        return;
    }

    e.preventDefault();

    // Grab the title
    const title = container.dataset.title;

    // Update URL hash
    window.location.hash = encodeURIComponent(title);

    //Move to tile
    centerOnTile(title);
}