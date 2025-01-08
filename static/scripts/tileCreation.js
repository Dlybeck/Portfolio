window.createTile = function(title) {
    const tileWrapper = document.createElement('div');
    tileWrapper.className = 'tile-container';
    tileWrapper.dataset.title = title;

    const tile = document.createElement('div');
    tile.className = 'tile';

    const tileContents = document.createElement('div');
    tileContents.className = 'tile-contents';

    const tileTitle = document.createElement('h2');
    tileTitle.className = 'tile-title';
    tileTitle.innerHTML = title;

    const tileText = document.createElement('p');
    tileText.className = 'tile-text';
    tileText.innerHTML = `${texts[title]}`;

    const button = document.createElement('a');
    button.className = 'button';
    // button.href = `${routes[title]}`;
    button.setAttribute("onclick", `openPage('${routes[title]}')`);
    button.textContent = 'GO';

    tileContents.appendChild(tileTitle);
    tileContents.appendChild(tileText);
    tileContents.appendChild(button);
    tile.appendChild(tileContents);
    tileWrapper.appendChild(tile);
    container.appendChild(tileWrapper);

    positionTile(tileWrapper, title);

    //Make Pages look different
    if (tilesData.hasOwnProperty(title) == true){
        tile.style.borderRadius = "200px";
        button.style.display = "none"
    }
    //Make home look identifiable
    if (title === "Home") {
        tile.style.background = "linear-gradient(135deg, #004477, #002255)"
    }
    return tileWrapper;
}

window.positionTile = function(tile, title) {
    const pos = window.positions[title];
    if (pos) {
        tile.style.position = 'absolute';
        tile.style.left = `${pos.left}%`;
        tile.style.top = `${pos.top}%`;
        tile.style.transform = 'translate(-50%, -50%)';
    }
};

window.updateVisibility = function(centerTitle) {
    // Get connected tiles
    const connectedTiles = tilesData[centerTitle] || [];
    // If this tile is a child, find its parent
    const parentTitle = Object.entries(tilesData).find(([parent, children]) => 
        children.includes(centerTitle)
    )?.[0];
    
    const visibleTiles = [centerTitle, ...connectedTiles];
    if (parentTitle) {
        visibleTiles.push(parentTitle);
    }

    // Update all tile visibilities
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
    });
}