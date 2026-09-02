const portfolioStateElement = document.getElementById('portfolio-state');
window.portfolioState = portfolioStateElement
    ? JSON.parse(portfolioStateElement.textContent)
    : {
        initialDestination: null,
        destinationMap: {},
        documentTitles: {},
        boardRoutes: {},
        documentPrefix: '/_documents',
    };

window.documentUrlForRoute = function(route) {
    const prefix = window.portfolioState.documentPrefix || '/_documents';
    return `${prefix}${route.startsWith('/') ? route : `/${route}`}`;
};

window.setDestinationUrl = function(route, { replace = false } = {}) {
    const method = replace ? 'replaceState' : 'pushState';
    window.history[method]({ documentRoute: route }, '', route);
};

window.setBoardUrl = function(title, { replace = false } = {}) {
    const method = replace ? 'replaceState' : 'pushState';
    const route = title && title !== 'Home'
        ? `/#${encodeURIComponent(title)}`
        : '/';
    window.history[method]({ boardTitle: title || 'Home' }, '', route);
};

window.centerOnDestination = function(route) {
    const title = window.portfolioState.destinationMap[route];
    if (title) window.centerOnTile(title);
};

window.checkUrlHash = function() {
    const initial = window.portfolioState.initialDestination;
    if (initial && !window._initialDestinationHandled) {
        window._initialDestinationHandled = true;
        window.centerOnTile(initial.title);
        window.openPage(initial.route, { syncUrl: false });
        return;
    }

    //Grab the hashed part of the url
    const hash = decodeURIComponent(window.location.hash.slice(1));

    //If a window position matched the hash
    if (hash && window.positions[hash]) {
        //Move to the tile
        window.centerOnTile(hash);
    } else {
        //Go to home
        window.centerOnTile('Home');
    }
};
