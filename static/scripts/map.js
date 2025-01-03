document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector(".map");
    
    // Grid unit sizes for different screen widths
    const GRID_UNITS = {
        mobile: 32,    // More space between tiles on mobile
        tablet: 36,    // Slightly less space on tablet
        desktop: 40    // Original spacing for desktop
    };

    // Function to get current grid unit based on screen size
    function getCurrentGridUnit() {
        if (window.innerWidth <= 480) {
            return GRID_UNITS.mobile;
        } else if (window.innerWidth <= 768) {
            return GRID_UNITS.tablet;
        }
        return GRID_UNITS.desktop;
    }

    // Define positions using grid coordinates
    const tilePositions = {
        "Home": [0, 0],
        
        // First level (slightly further apart)
        "Hobbies": [-1, -1],
        "Projects": [1, -1],
        "Jobs": [1, 1],
        "Education": [-1, 1],
        
        // Second level from Hobbies (adjusted spacing)
        "3D Printing": [-2, -2],
        "Gaming": [0, -2],
        "Tennis": [-2, 0],
        
        // Third level from 3D Printing (further spread)
        "Other Models": [-3, -1],
        "Puzzles": [-3, -3],
        
        // Second level from Projects (adjusted)
        "Programs": [2, 0],
        "Websites": [2, -2],
        
        // Third level from Websites (spread out)
        "Digital Planner": [1, -3],
        "This website": [3, -3],
        
        // Second level from Education
        "College": [-2, 2],
        "Early Education": [0, 2]
    };

    // Convert grid positions to actual percentages
    function calculatePositions() {
        const gridUnit = getCurrentGridUnit();
        const positions = {};
        
        for (const [title, [x, y]] of Object.entries(tilePositions)) {
            positions[title] = {
                left: 50 + (x * gridUnit),
                top: 50 + (y * gridUnit)
            };
        }
        return positions;
    }

    let positions = calculatePositions();

    const tilesData = {
        "Home": ["Hobbies", "Projects", "Jobs", "Education"],
        "Hobbies": ["3D Printing", "Gaming", "Tennis"],
        "3D Printing": ["Other Models", "Puzzles"],
        "Projects": ["Programs", "Websites"],
        "Websites": ["Digital Planner", "This website"],
        "Education": ["College", "Early Education"]
    };

    // Update positions on window resize
    let resizeTimer;
    window.addEventListener('resize', function() {
        clearTimeout(resizeTimer);
        resizeTimer = setTimeout(function() {
            positions = calculatePositions();
            const currentTitle = document.querySelector('.tile-container.expanded')?.dataset.title || 'Home';
            centerOnTile(currentTitle);
        }, 250);
    });

    function createTile(title) {
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

        const button = document.createElement('a');
        button.className = 'button';
        button.href = '';
        button.textContent = 'GO';

        tileContents.appendChild(tileTitle);
        tileContents.appendChild(button);
        tile.appendChild(tileContents);
        tileWrapper.appendChild(tile);
        container.appendChild(tileWrapper);

        positionTile(tileWrapper, title);
        return tileWrapper;
    }

    function positionTile(tile, title) {
        const pos = positions[title];
        if (pos) {
            tile.style.left = `${pos.left}%`;
            tile.style.top = `${pos.top}%`;
            tile.style.transform = 'translate(-50%, -50%)';
        }
    }

    function updateVisibility(centerTitle) {
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

        // Update all tiles' visibility
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

    function centerOnTile(title) {
        const centerPos = positions[title];
        const offsetX = 50 - centerPos.left;
        const offsetY = 50 - centerPos.top;

        const tiles = document.querySelectorAll('.tile-container');
        tiles.forEach(tile => {
            const tileTitle = tile.dataset.title;
            const tilePos = positions[tileTitle];
            
            tile.style.left = `${tilePos.left + offsetX}%`;
            tile.style.top = `${tilePos.top + offsetY}%`;
        });

        updateVisibility(title);
    }

    // Create all tiles
    Object.keys(tilesData).forEach(title => {
        createTile(title);
        tilesData[title].forEach(childTitle => {
            createTile(childTitle);
        });
    });

    // Add click handlers
    const tileContainers = document.querySelectorAll('.tile-container');
    tileContainers.forEach(container => {
        const tileElement = container.querySelector('.tile');
        const buttonElement = container.querySelector('.button');

        tileElement.addEventListener('click', function(e) {
            handleTileClick(e, container);
        });

        if (buttonElement) {
            buttonElement.addEventListener('click', function(e) {
                e.stopPropagation();
            });
        }
    });

    function handleTileClick(e, container) {
        if (e.target.classList.contains('button')) {
            return;
        }
        e.preventDefault();
        const title = container.dataset.title;
        centerOnTile(title);
    }

    // Initially center on Home
    centerOnTile('Home');
});