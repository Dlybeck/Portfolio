window.oldBackPosX = 0;
window.oldBackPosY = 0;

window.centerOnTile = function(title) {
    const centerPos = positions[title];
    if (!centerPos) {
        console.error(`No position found for tile: ${title}`);
        return;
    }
    
    // Calculate offsets for tile movement
    const offsetX = 50 - centerPos.left;
    const offsetY = 50 - centerPos.top;
    
    // Move tiles
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
        
        tile.style.left = `${tilePos.left + offsetX}%`;
        tile.style.top = `${tilePos.top + offsetY}%`;
        
        // Restore width/height after moving
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
    oldBackPosX = centerPos.left/1.2;
    oldBackPosY = centerPos.top/1.5;
    document.body.style.backgroundPosition = `${-oldBackPosX}rem ${-oldBackPosY}rem`;
    window.checkHomeButton();
    updateVisibility(title);
}

window.returnHome = function() {
    const homeTile = positions['Home'];
    if (!homeTile) {
        console.error('No position found for Home tile');
        return;
    }

    // Reset offsets to initial positions
    const offsetX = 50 - homeTile.left;
    const offsetY = 50 - homeTile.top;

    // Move all tiles back to their original positions
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

    // Update visibility to focus on "Home"
    updateVisibility('Home');
    window.checkHomeButton(document.body);
}

window.handleTileClick = function(e, container) {
    if (e.target.classList.contains('button')) {
        return;
    }
    e.preventDefault();
    const title = container.dataset.title;
    
    // Update URL hash
    window.location.hash = encodeURIComponent(title);
    
    // Your existing centering code
    centerOnTile(title);
}