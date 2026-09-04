/**
 * openPage.js — native-scroll version
 *
 * The mini-window paper is a normal-flow element in body. When opened,
 * body becomes tall (paper adds height); the browser's native scroll
 * handles wheel, touch, momentum, inertia — everything, for free, on
 * every platform. No custom touch handlers, no touch-action hacks, no
 * mapPan integration.
 *
 * We still control:
 *   - iframe height sizing to content scrollHeight (so the iframe shows
 *     all its content without internal scroll)
 *   - in-iframe CSS injection (paper theme, overflow: hidden)
 *   - close button, back button, nav history
 *   - wall parallax via scroll event listener (cheap, passive)
 */

class MiniWindow {
    constructor() {
        this.container   = document.querySelector(".mini-window-container");
        this.page        = document.querySelector(".mini-window");
        this.closeButton = document.querySelector(".close-button");
        this.closeLabel  = this.closeButton ? this.closeButton.querySelector('.tab') : null;
        this.navigationHistory = [];
        this.teardownTimer = null;
        this.outsideHandlerTimer = null;

        this.setEvents();
    }

    motionDuration(defaultDuration) {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 0
            : defaultDuration;
    }

    // ---------------------- open / close ----------------------

    open(route, options = {}) {
        if (this.teardownTimer !== null) {
            clearTimeout(this.teardownTimer);
            this.teardownTimer = null;
        }
        if (this.outsideHandlerTimer !== null) {
            clearTimeout(this.outsideHandlerTimer);
            this.outsideHandlerTimer = null;
        }
        document.removeEventListener('click', this._outsideHandler, true);

        const normalized = this.normalizeUrl(route);
        this.initialRoute = normalized;
        this.navigationHistory = [normalized];
        this._displayRoute(normalized, options);

        this.container.classList.remove('closing');
        this.container.classList.add('open');
        document.body.classList.add('page-open');

        // Tap/click anywhere outside the paper closes. Installed with a
        // small delay so the click that opened the page doesn't instantly
        // close it. Registered in capture phase so we see the event before
        // any child handler can stop it.
        this.outsideHandlerTimer = setTimeout(() => {
            this.outsideHandlerTimer = null;
            if (this.isVisible()) {
                document.addEventListener('click', this._outsideHandler, true);
            }
        }, this.motionDuration(100));

    }

    navigateTo(route) {
        const normalized = this.normalizeUrl(route);
        this.navigationHistory.push(normalized);
        this._displayRoute(normalized);
    }

    goBack() {
        if (!this.isVisible() || this.navigationHistory.length <= 1) return false;
        this.navigationHistory.pop();
        const previousUrl = this.navigationHistory[this.navigationHistory.length - 1];
        this._displayRoute(previousUrl);
        return true;
    }

    _displayRoute(route, options = {}) {
        window.centerOnDestination(route);
        const routePath = new URL(route, window.location.origin).pathname;
        const documentTitle = window.portfolioState.documentTitles[routePath]
            || 'Portfolio';
        this.page.setAttribute('title', `${documentTitle} portfolio document`);
        this._loadInto(window.documentUrlForRoute(route));
        if (options.syncUrl !== false) window.setDestinationUrl(route);
        this.updateCloseButtonLabel();
    }

    _loadInto(url) {
        this._showLoadingScrap();
        this.page.onload = () => this._onIframeLoad();
        this.page.setAttribute('src', url);
    }

    _onIframeLoad() {
        let doc = null;
        try { doc = this.page.contentDocument; } catch (_) {}
        if (!doc || !doc.body) { this._hideLoadingScrap(); return; }

        // Install only invariant iframe behavior here. Visual treatment is
        // exclusively supplied by the active Theme Pack.
        const style = doc.createElement('style');
        style.setAttribute('data-paper-table', '');
        style.textContent = `
            html, body {
                margin: 0 !important;
                padding: 0 !important;
                touch-action: pan-y !important;
            }
            body { overflow-y: auto !important; overflow-x: hidden !important; }
            #topBtn { display: none !important; }
        `;
        doc.head.appendChild(style);
        if (window.themeEngine) window.themeEngine.styleDocument(doc);

        doc.addEventListener('keydown', (event) => {
            if (event.key !== 'Escape') return;
            event.preventDefault();
            window.handlePortfolioEscape();
        });

        this._hideLoadingScrap();
    }

    // ---------------------- show / hide ----------------------

    hide(options = {}) {
        if (this.outsideHandlerTimer !== null) {
            clearTimeout(this.outsideHandlerTimer);
            this.outsideHandlerTimer = null;
        }
        document.removeEventListener('click', this._outsideHandler, true);
        document.body.classList.remove('page-open');
        this.container.classList.remove('open');
        this.container.classList.add('closing');

        if (options.syncUrl !== false) {
            window.setBoardUrl(window.currentTileTitle || 'Home');
        }
        if (window.focusCenteredTile) {
            window.focusCenteredTile(window.currentTileTitle || 'Home');
        }

        // Wait for the slide-out animation to finish, then tear down.
        const EXIT_MS = this.motionDuration(420);
        if (this.teardownTimer !== null) clearTimeout(this.teardownTimer);
        this.teardownTimer = setTimeout(() => {
            this.teardownTimer = null;
            if (this.isVisible()) return;
            this.container.classList.remove('closing');
            this.page.setAttribute('src', '');
            this.navigationHistory = [];
        }, EXIT_MS);
    }

    // ---------------------- helpers ----------------------

    isVisible() {
        return this.container.classList.contains('open');
    }

    /**
     * Update the single button's label based on navigation state:
     *   - history length > 1  → "← back" (clicking goes back one step)
     *   - history length === 1 → "✕ close" (clicking closes the paper)
     */
    updateCloseButtonLabel() {
        if (!this.closeLabel) return;
        if (this.navigationHistory.length > 1) {
            this.closeLabel.textContent = '← back';
            this.closeButton.setAttribute('aria-label', 'Go back to previous document');
        } else {
            this.closeLabel.textContent = '✕ close';
            this.closeButton.setAttribute('aria-label', 'Close document');
        }
    }

    _showLoadingScrap() {
        if (this._loadingEl) return;
        const el = document.createElement('div');
        el.className = 'loading-scrap';
        el.textContent = 'loading…';
        this.container.appendChild(el);
        this._loadingEl = el;
    }

    _hideLoadingScrap() {
        if (!this._loadingEl) return;
        const el = this._loadingEl;
        this._loadingEl = null;
        if (el.parentNode) el.parentNode.removeChild(el);
    }

    normalizeUrl(url) {
        if (url.startsWith('/')) {
            const parsed = new URL(url, window.location.origin);
            return parsed.pathname + parsed.search;
        }
        if (url.startsWith('http://')) return url.replace('http://', 'https://');
        if (url.startsWith('//'))      return 'https:' + url;
        return url;
    }

    setEvents() {
        // Single button — contextual action.
        if (this.closeButton) {
            this.closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.navigationHistory.length > 1) this.goBack();
                else this.hide();
            });
        }

        // Tap/click outside the paper area closes. Registered in capture
        // phase so we see the click before child handlers can stop it.
        // The handler is stored on the instance so it can be removed on
        // hide.
        this._outsideHandler = (event) => {
            const t = event.target;
            if (!t) return;
            // Ignore clicks inside the paper container itself.
            if (this.container.contains(t)) return;
            // Ignore clicks on the close/back button.
            if (this.closeButton && this.closeButton.contains(t)) return;
            // Ignore clicks on the navbar (home icon etc).
            const navbar = document.querySelector('.navbar');
            if (navbar && navbar.contains(t)) return;
            // Controls that operate on an open Viewer may live outside its
            // physical frame. The outside-click capture handler sees them
            // before their own click handlers, so recognize the stable
            // control boundary here rather than relying on propagation.
            if (t.closest?.('[data-viewer-control]')) return;
            this.hide();
        };
    }

}

document.addEventListener("DOMContentLoaded", () => {
    const miniWindow = new MiniWindow();
    window.openPage = (route, options) => miniWindow.open(route, options);
    window.navigateToPage = (route) => miniWindow.navigateTo(route);
    window.closePage = (options) => miniWindow.hide(options);
    window.handlePortfolioEscape = () => {
        if (miniWindow.isVisible()) {
            if (!miniWindow.goBack()) miniWindow.hide();
            return true;
        }
        return window.returnToParent ? window.returnToParent() : false;
    };
    document.addEventListener('keydown', (event) => {
        if (event.key !== 'Escape') return;
        if (window.handlePortfolioEscape()) event.preventDefault();
    });
});
