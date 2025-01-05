document.addEventListener('DOMContentLoaded', function() {
    const container = document.querySelector(".map");
    
    // Grid unit sizes for different screen widths
    const GRID_UNITS = 34;

    var oldBackPosX = 0;
    var oldBackPosY = 0;

    // Define positions using grid coordinates
    const tileInfo = {
        "Home": [
            [0, 0],
            `
            Welcome!
            <br><br>
            Check out the neighboring tiles to explore aspects of David's life.
            <br><br>
            Come back here if you ever get lost!
            `,
            ``
        ],

        //Home
        "Hobbies": [
            [-1, -1],
            `
            What I like to do with my free time!
            <br><br>
            (minus coding)
            <br><br>
            ((It's somewhere else))
            <br><br>
            (((----->)))
            `,
            `/`
        ],
        "Projects": [
            [1, -1],
            `
            The home for personal or Team projects I've developed
            <br><br>
            Don't judge too hard
            `,
            `/`
        ],
        "Jobs": [
            [1, 1],
            `
            Look here for my professional info:
            <br><br>
            <small>#opentowork</small>
            `,
            `/jobs`
        ],
        "Education": [
            [-1, 1],
            `
            Schools I've gone to and classes I've taken
            `,
            `/`
        ],
        
        //Hobbies
        "3D Printing": [
            [-2, -2],
            `
            Here's some 3d models I've designed and printed for fun
            `,
            `/`
        ],
        "Gaming": [
            [0, -2],
            `
            Check out some of my favorite video games!
            <br><br>
            I'll race you in Mariokart Wii
            `,
            `/hobbies/gaming`
        ],
        "Tennis": [
            [-2, 0],
            `
            I've played for as long as I remember.
            <br><br>
            Let me know if you need someone to hit with!
            `,
            `/hobbies/tennis`
        ],
        
        //3D printing
        "Other Models": [
            [-3, -1],
            `
            Random models I've made over the years
            `,
            `/hobbies/3d_printing/other_models`
        ],
        "Puzzles": [
            [-3, -3],
            `
            I always wanted more puzzle boxes to have around. So I started making them.
            <br><br>
            I bet you can't solve them.
            `,
            `/hobbies/3d_printing/puzzles`
        ],
        
        //Projects
        "Programs": [
            [2, 0],
            `
            Programs I've made both for fun and for class
            <br><br>
            (Some of them are pretty old lol)
            `,
            `/projects/programs`
        ],
        "Websites": [
            [2, -2],
            `
            Web apps I've developed, and how they were made.
            <br><br>
            This is my favorite :)
            `,
            `/`
        ],
        
        //Websites
        "Digital Planner": [
            [1, -3],
            `
            A calander and to-do list mashed into one
            <br><br>
            Made in partnership with Svetlana and Aleksandra Solodilov, Matthew Zou and Sumneet Brar
            `,
            `/projects/websites/digital_planner`
        ],
        "This website": [
            [3, -3],
            `
            You're looking at it!
            <br><br>
            Check out some old versions and how it was made
            `,
            `/projects/websites/this_website`
        ],
        
        //Education
        "College": [
            [-2, 2],
            `
            "Once a logger always a logger"
            <br><br>
            "Hack Hack, Chop Chop"
            `,
            `/education/college`
        ],
        "Early Education": [
            [0, 2],
            `
            Don't come looking for me here
            <br><br>
            (I graduated)
            `,
            `/education/early_education`
        ]
    };

    // Convert grid positions to actual percentages
    function calculatePositions() {
        const positions = {};
        const texts = {};
        const routes = {}
        
        for (const [title, tileData] of Object.entries(tileInfo)) {
            const [coordinates, text, tileRoute] = tileData;
            positions[title] = {
                left: (coordinates[0] * GRID_UNITS),
                top: (coordinates[1] * GRID_UNITS)
            };
            texts[title] = text;
            routes[title] = tileRoute;

        }
        return [positions, texts, routes];
    }

    let [positions, texts, routes] = calculatePositions();

    const tilesData = {
        "Home": ["Hobbies", "Projects", "Jobs", "Education"],
        "Hobbies": ["3D Printing", "Gaming", "Tennis"],
        "3D Printing": ["Other Models", "Puzzles"],
        "Projects": ["Programs", "Websites"],
        "Websites": ["Digital Planner", "This website"],
        "Education": ["College", "Early Education"]
    };

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
            tile.style.borderStyle = "solid"
            tile.style.borderWidth = "5px"
            tile.style.borderColor = "#111111"

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
    

    // Create all tiles with duplicate prevention
    const createdTiles = new Set();


    Object.keys(tilesData).forEach(title => {
        if (!createdTiles.has(title)) {
            createTile(title);
            createdTiles.add(title);
        }
        
        tilesData[title].forEach(childTitle => {
            if (!createdTiles.has(childTitle)) {
                createTile(childTitle);
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
            const title = container.dataset.title;
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
        
        // Check if position exists
        if (!positions[title]) {
            console.error(`No position found for tile: ${title}`);
            return;
        }
        
        centerOnTile(title);
    }

    function centerOnTile(title) {
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
            
            tile.style.left = `${tilePos.left + offsetX}%`;
            tile.style.top = `${tilePos.top + offsetY}%`;
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
        // Update the tracked old positions
        oldBackPosX = centerPos.left/1.2;
        oldBackPosY = centerPos.top/1.5;
    
        // Apply new background position
        document.body.style.backgroundPosition = `${-oldBackPosX}rem ${-oldBackPosY}rem`;
        
        window.checkHomeButton();
    
        // Update visibility of tiles
        updateVisibility(title);
    }

    function returnHome() {
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

    window.returnHome = returnHome;
    
    

    // Initially center on Home
    if (positions['Home']) {
        centerOnTile('Home');
    } else {
        console.error('No position found for Home tile');
    }
});