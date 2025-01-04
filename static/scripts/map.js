document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector(".map");
    
    // Grid unit sizes for different screen widths
    const GRID_UNITS = {
        mobile: 34,
        tablet: 35,
        desktop: 35
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
    const tileInfo = {
        "Home": [
            [0, 0],
            `
            Welcome to davidlybeck.com!
            <br><br>
            Check out the neighboring tiles to explore aspects of David's life.
            <br><br>
            Come back here if you ever get lost!
            `
        ],

        //Home
        "Hobbies": [
            [-1, -1],
            ``
        ],
        "Projects": [
            [1, -1],
            ``
        ],
        "Jobs": [
            [1, 1],
            ``
        ],
        "Education": [
            [-1, 1],
            ``
        ],
        
        //Hobbies
        "3D Printing": [
            [-2, -2],
            ``
        ],
        "Gaming": [
            [0, -2],
            ``
        ],
        "Tennis": [
            [-2, 0],
            ``
        ],
        
        //3D printing
        "Other Models": [
            [-3, -1],
            ``
        ],
        "Puzzles": [
            [-3, -3],
            ``
        ],
        
        //Projects
        "Programs": [
            [2, 0],
            ``
        ],
        "Websites": [
            [2, -2],
            ``
        ],
        
        //Websites
        "Digital Planner": [
            [1, -3],
            ``
        ],
        "This website": [
            [3, -3],
            ``
        ],
        
        //Education
        "College": [
            [-2, 2],
            ``
        ],
        "Early Education": [
            [0, 2],
            ``
        ]
    };

    // Convert grid positions to actual percentages
    function calculatePositions() {
        const gridUnit = getCurrentGridUnit();
        const positions = {};
        const texts = {};
        
        for (const [title, tileData] of Object.entries(tileInfo)) {
            const [coordinates, text] = tileData;
            positions[title] = {
                left: (coordinates[0] * gridUnit),
                top: (coordinates[1] * gridUnit)
            };
            texts[title] = text;
        }
        return [positions, texts];
    }

    let [positions, texts] = calculatePositions();

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

        const tileText = document.createElement('p');
        tileText.className = 'tile-text';
        tileText.innerHTML = `<br> ${texts[title]}`;

        const button = document.createElement('a');
        button.className = 'button';
        button.href = '';
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

    function centerOnTile(title) {
        const centerPos = positions[title];
        console.log(`title is ${title}`);
        console.log(`centerPos is ${centerPos}`);
        const offsetX = 50 - centerPos.left;
        const offsetY = 50 - centerPos.top;
    
        // Move tiles
        const tiles = document.querySelectorAll('.tile-container');
        tiles.forEach(tile => {
            const tileTitle = tile.dataset.title;
            const tilePos = positions[tileTitle];
            
            tile.style.left = `${tilePos.left + offsetX}%`;
            tile.style.top = `${tilePos.top + offsetY}%`;
        });
    
        // Move body background
        const body = document.body;
        body.style.backgroundPosition = `${offsetX-50}% ${-offsetY+50}%`; // Directly apply the same offset logic
    
        updateVisibility(title);
    }
    

    // Create all tiles
    Object.keys(tilesData).forEach(title => {
        console.log(`Creating tile for ${title}`)
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