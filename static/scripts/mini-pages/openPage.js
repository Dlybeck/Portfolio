class MiniWindow {
    constructor() {
        this.container = document.querySelector(".mini-window-container");
        this.page = document.querySelector(".mini-window");
        this.closeButton = document.querySelector(".close-button");
        this.backButton = document.querySelector(".back-button");
        this.backButton.style.visibility = "hidden";
        this.navigationHistory = [];

        this.setEvents();
    }

    /**
     * Open a mini-window with a given route
     * @param {String} route - the route for fast-api
     */
    open(route) {
        this.initialRoute = route;
        this.navigationHistory = [route];

        // Ensure route uses same protocol as parent page
        const normalizedRoute = this.normalizeUrl(route);
        this.page.setAttribute("src", normalizedRoute);
        this.show();
        this.updateBackButtonState();
    }

    /**
     * Normalize URL to ensure it uses the correct protocol
     * @param {String} url - the URL to normalize
     * @returns {String} - normalized URL
     */
    normalizeUrl(url) {
        // For relative URLs, construct absolute HTTPS URL explicitly
        // This prevents mixed content issues if browser somehow uses HTTP origin
        if (url.startsWith('/')) {
            // Use protocol detection (matches pattern in agentbridge.js, speckit.js, websocket.js, tabs.js)
            const protocol = window.location.protocol; // 'https:' or 'http:'
            const hostname = window.location.hostname;

            // If parent page is HTTPS, construct absolute HTTPS URL
            if (protocol === 'https:') {
                const httpsUrl = `https://${hostname}${url}`;
                console.log('[MiniWindow] Converting relative to absolute HTTPS:', url, '->', httpsUrl);
                return httpsUrl;
            }

            // For http (localhost/dev), return as-is
            return url;
        }

        // If it has a protocol, ensure it's HTTPS
        if (url.startsWith('http://')) {
            console.warn('[MiniWindow] Converting HTTP to HTTPS:', url);
            return url.replace('http://', 'https://');
        }

        // If it's a protocol-relative URL (//domain.com/path)
        if (url.startsWith('//')) {
            return 'https:' + url; // Force HTTPS
        }

        return url;
    }

    /**
     * Show the mini-window
     */
    show() {
        this.container.style.visibility = "visible";
        this.container.style.opacity = "1";
        document.addEventListener('click', this.handleClickOutside);
    }

    /**
     * Hide the mini-window
     */
    hide() {
        this.container.style.opacity = "0";
        this.container.style.visibility = "hidden";
        this.page.setAttribute("src", "")
        document.removeEventListener('click', this.handleClickOutside);
        this.navigationHistory = [];
    }

    /**
     * If navigated away from the original route, go back to previous page
     * @returns {Boolean} - whether the back operation was performed
     */
    goBack() {
        if (!this.isVisible() || this.navigationHistory.length <= 1) {
            return false;
        }

        this.navigationHistory.pop();
        const previousUrl = this.navigationHistory[this.navigationHistory.length - 1];
        this.page.setAttribute("src", previousUrl);
        this.updateBackButtonState();
        return true;
    }

    /**
     * Update back button visibility based on navigation history
     */
    updateBackButtonState() {
        if (this.navigationHistory.length <= 1) {
            this.backButton.style.visibility = 'hidden';
        } else {
            this.backButton.style.visibility = 'visible';
        }
    }

    /**
     * Checks to see whether or not the mini-window is visible
     * @returns {Boolean}
     */
    isVisible() {
        return this.container.style.visibility === "visible" &&
               this.container.style.opacity === "1";
    }

    /**
     * Sets up event listeners for the following events:
     *  Clicking the x button to close
     *  Clicking the back button to go back
     *  Clicking off the mini-window to close
     */
    setEvents() {
        this.handleClickOutside = (event) => {
            if (!this.container.contains(event.target)) {
                this.hide();
            }
        };

        this.closeButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.hide();
        });

        this.backButton.addEventListener('click', (e) => {
            e.stopPropagation();
            this.goBack();
        });
    }

    /**
     * Navigate to a new route within the same mini-window
     * @param {String} route - the route to navigate to
     */
    navigateTo(route) {
        const normalizedRoute = this.normalizeUrl(route);
        this.navigationHistory.push(normalizedRoute);
        this.page.setAttribute("src", normalizedRoute);
        this.updateBackButtonState();
    }
}

// Expose openPage and navigateToPage to HTML so it can use them
document.addEventListener("DOMContentLoaded", () => {
    const miniWindow = new MiniWindow();
    window.openPage = (route) => miniWindow.open(route);
    window.navigateToPage = (route) => miniWindow.navigateTo(route);
});
