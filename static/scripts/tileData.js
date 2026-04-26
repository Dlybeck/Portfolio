// Grid unit sizes for different screen widths
window.GRID_UNITS = 34;

// Connections for each "Hub" tile (no go button)
window.tilesData = {
    "Home": ["Hobbies", "Projects", "Work Experience", "Education"],
    "Hobbies": ["3D Printing", "Gaming", "Tennis"],
    "3D Printing": ["Other Models", "Puzzles"],
    "Projects": ["Programs", "Websites"],
    "Websites": ["Digital Planner", "This website", "ScribbleScan"],
    "Education": ["College", "Early Education", "Agile Report"],
};

// Set up all variables for each tile. Position (grid based), Text for the tile, and the URL for it's content (if applicable)
window.tileInfo = {
    "Home": [
        [0, 0],
        `
        Welcome!
        <br><br>
        Check out the neighboring tiles and look out for "Open" buttons for more info!
        <br><br>
        Come back here if you ever get lost!
        `,
        ``
    ],

    //Home
    "Hobbies": [
        [-1, -1],
        `
        All my favorites!
        <br><br>
        (Coding gets its own section)
        `,
        `/`
    ],
    "Projects": [
        [1, -1],
        `
        Personal Projects I've developed
        `,
        `/`
    ],
    "Work Experience": [
        [1, 1],
        `
        Junior Tennis Pro --> Innovation AI Developer
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
        Let me know if you want to hit
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
        (Some of them are pretty old)
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
    "ScribbleScan": [
        [3, -1],
        `
        AI-powered OCR with industry leading accuracy on handwritten text.
        <br><br>
        Also my capstone project!
        `,
        `/projects/websites/scribblescan`
    ],

    //Education
    "College": [
        [-2, 2],
        `
        Don't come looking for me here
        <br><br>
        (I graduated)
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
    ],

    //Hidden standalone tiles
    "Agile Report": [
        [6, -6],
        `
        My report on Agile Management
        <br><br>
        Made in 2024
        `,
        `/education/agile_report`
    ]
};


/**
 * Classify a tile as "sticky" (hub) or "scrap" (leaf page) for the paper-table theme.
 * Keys of tilesData are hubs. Home is always a hub.
 * @param {string} title
 * @returns {"sticky"|"scrap"}
 */
window.getPaperType = function(title) {
    if (title === "Home") return "sticky";
    if (window.tilesData.hasOwnProperty(title)) return "sticky";
    return "scrap";
};

/**
 * Deterministic string hash → 32-bit int.
 * Used to seed stable per-tile "randomness" (rotation, color, variant, font)
 * so the tabletop looks organic but consistent across reloads.
 * @param {string} s
 * @returns {number}
 */
window.stableHash = function(s) {
    let h = 2166136261;
    for (let i = 0; i < s.length; i++) {
        h ^= s.charCodeAt(i);
        h = Math.imul(h, 16777619);
    }
    return Math.abs(h | 0);
};

/**
 * Creates maps to acces data for positions, text contents, and routes, by tile title
 * @returns {positions map, pexts map, routes map}]
 */
window.calculatePositions = function() {
    const positions = {};
    const texts = {};
    const routes = {};
    
    for (const [title, tileData] of Object.entries(window.tileInfo)) {
        const [coordinates, text, tileRoute] = tileData;
        positions[title] = {
            left: (coordinates[0] * window.GRID_UNITS),
            top: (coordinates[1] * window.GRID_UNITS*.9) //.9 for offset to give space to navbar
        };
        texts[title] = text;
        routes[title] = tileRoute;
    }
    return [positions, texts, routes];
};