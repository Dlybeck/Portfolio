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
        this.page.setAttribute("src", route);
        this.show();
        this.setupNavigationHandling();
        this.updateBackButtonState();
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
        this.page.removeAttribute("src")
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
        if (this.navigationHistory.length <= 2) {
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
     * Keeps track of routes used in current mini-window.
     * So back functionality works properly
     */
    setupNavigationHandling() {
        this.page.addEventListener('load', () => {
            const newUrl = this.page.contentWindow.location.href;
            if (newUrl !== this.navigationHistory[this.navigationHistory.length - 1]) {
                this.navigationHistory.push(newUrl);
                this.updateBackButtonState();
            }
        });

        window.addEventListener('popstate', (event) => {
            const url = event.state?.url || this.initialRoute;
            if (!this.navigationHistory.includes(url)) {
                this.navigationHistory.push(url);
            }
            this.page.setAttribute("src", url);
            this.updateBackButtonState();
        });
    }
}

//Expose openPage to html can use it
document.addEventListener("DOMContentLoaded", () => {
    const miniWindow = new MiniWindow();
    window.openPage = (route) => miniWindow.open(route);
});
