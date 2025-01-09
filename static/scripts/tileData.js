// Grid unit sizes for different screen widths
window.GRID_UNITS = 34;

// Connections for each "Hub" tile (no go button)
window.tilesData = {
    "Home": ["Hobbies", "Projects", "Jobs", "Education"],
    "Hobbies": ["3D Printing", "Gaming", "Tennis"],
    "3D Printing": ["Other Models", "Puzzles"],
    "Projects": ["Programs", "Websites"],
    "Websites": ["Digital Planner", "This website"],
    "Education": ["College", "Early Education"]
};

// Set up all variables for each tile. Position (grid based), Text for the tile, and the URL for it's content (if applicable)
window.tileInfo = {
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
        Look here for information on my work history
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
            top: (coordinates[1] * window.GRID_UNITS)
        };
        texts[title] = text;
        routes[title] = tileRoute;
    }
    return [positions, texts, routes];
};