/**
 * creates a tile for the specified title
 * @param {string} title - Title of node to be created
 * @returns - html object representing the wrapper for the tile
 */
window.createTile = function(title) {
    let [ , texts, routes] = window.calculatePositions();

    // Create the container for tile
    const tileWrapper = document.createElement('div');
    tileWrapper.className = 'tile-container';
    tileWrapper.dataset.title = title;

    // Create the tile
    const tile = document.createElement('div');
    tile.className = 'tile';

    // Create the div for tile contents
    const tileContents = document.createElement('div');
    tileContents.className = 'tile-contents';

    // Title for the tile
    const tileTitle = document.createElement('h2');
    tileTitle.className = 'tile-title';
    tileTitle.innerHTML = title;

    // Go button for the tile (will be hidden later if not applicable)
    const button = document.createElement('a');
    button.className = 'button';
    button.href = routes[title];
    button.textContent = `${title}`;

    // Attach event listener to handle iframe behavior
    button.addEventListener('click', (event) => {
        event.preventDefault(); // Prevent the default anchor navigation
        openPage(routes[title]); // Call your function to load the iframe
    });

    // Text contents of the tile
    const tileText = document.createElement('p');
    tileText.className = 'tile-text';
    tileText.innerHTML = `${texts[title]}`;

    // Append the children and create the tile
    tileContents.appendChild(tileTitle);
    tileContents.appendChild(button);
    tileContents.appendChild(tileText);
    tile.appendChild(tileContents);
    tileWrapper.appendChild(tile);
    container.appendChild(tileWrapper);

    // Properly position this tile relative to the others
    positionTile(tileWrapper, title);

    // If the page is just a hub (no go button) make it a circle and hide the button
    if (tilesData.hasOwnProperty(title) == true){
        tile.style.borderRadius = "200px";
        button.style.display = "none";
    }

    // Make home look identifiable
    if (title === "Home") {
        tile.style.background = "linear-gradient(135deg, #004477, #002255)";
    }

    return tileWrapper;
}


/**
 * Move the tile to its proper position on the map
 * @param {*} tile - html object for the tile
 * @param {*} title - title of the tile
 */
window.positionTile = function(tile, title) {
    // grab the position
    const pos = window.positions[title];

    // If a position is found, move the tile to that position
    if (pos) {
        tile.style.position = 'absolute';
        tile.style.left = `${pos.left}%`;
        tile.style.top = `${pos.top}%`;
        // center it
        tile.style.transform = 'translate(-50%, -50%)';
    } else {
        console.error("No position found");
    }
};

/**
 * Update the tiles visibility based on the centered tile (make tiles dimmed if not connected, expand center, shrink non-center)
 * @param {*} centerTitle 
 */
window.updateVisibility = function(centerTitle) {
    // Get connected tiles (if none, use [])
    const connectedTiles = tilesData[centerTitle] || [];

    // Find the tiles directly connected to this one
    const parentTitle = Object.entries(tilesData).find(([_, children]) => 
        // If there is a key ([0]) for the parent title, add it.
        children.includes(centerTitle)
    )?.[0];

    // Add the center tile, all directly connected tiles to visible tiles
    const visibleTiles = [centerTitle, ...connectedTiles];
    if (parentTitle) {
        visibleTiles.push(parentTitle);
    }

    // Update all tile visibilities based on connection
    const tiles = document.querySelectorAll('.tile-container');
    tiles.forEach(tile => {
        const tileTitle = tile.dataset.title;

        // Reset all states first
        tile.classList.remove('expanded', 'connected', 'dimmed');

        if (tileTitle === centerTitle) {
            // Center tile is expanded
            tile.classList.add('expanded');
        } else if (visibleTiles.includes(tileTitle)) {
            // Connected tiles show title only
            tile.classList.add('connected');
        } else {
            // Other tiles are dimmed
            tile.classList.add('dimmed');
        }

        // After the visibility change, recheck if the title should be hidden for expanded tile
        const button = tile.querySelector('.button');
        const tileTitleElem = tile.querySelector('.tile-title');

        // Hide the title if the tile is expanded and the button is visible
        if (tile.classList.contains('expanded') && button.style.display !== "none") {
            tileTitleElem.style.display = 'none';
        } else {
            tileTitleElem.style.display = 'block';
        }
    });
}
