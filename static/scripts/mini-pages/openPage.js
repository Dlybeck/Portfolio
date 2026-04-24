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

        this.setEvents();
    }

    // ---------------------- open / close ----------------------

    open(route) {
        this.initialRoute = route;
        this.navigationHistory = [route];

        const normalized = this.normalizeUrl(route);
        this._loadInto(normalized);

        this.container.classList.remove('closing');
        this.container.classList.add('open');
        document.body.classList.add('page-open');

        // Tap/click anywhere outside the paper closes. Installed with a
        // small delay so the click that opened the page doesn't instantly
        // close it. Registered in capture phase so we see the event before
        // any child handler can stop it.
        setTimeout(() => {
            document.addEventListener('click', this._outsideHandler, true);
        }, 100);

        this.updateCloseButtonLabel();
    }

    navigateTo(route) {
        const normalized = this.normalizeUrl(route);
        this.navigationHistory.push(normalized);
        this._loadInto(normalized);
        this.updateCloseButtonLabel();
    }

    goBack() {
        if (!this.isVisible() || this.navigationHistory.length <= 1) return false;
        this.navigationHistory.pop();
        const previousUrl = this.navigationHistory[this.navigationHistory.length - 1];
        this._loadInto(previousUrl);
        this.updateCloseButtonLabel();
        return true;
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

        // Inject paper theme. Keep scroll ENABLED inside the iframe —
        // the iframe scrolls its own content internally; outer viewport
        // stays fixed. `touch-action: pan-y` opts into native vertical
        // touch panning so mobile feels smooth without any JS
        // forwarding / custom momentum fighting the browser.
        const style = doc.createElement('style');
        style.setAttribute('data-paper-table', '');
        style.textContent = `
            html, body {
                background: transparent !important;
                font-family: Georgia, 'Times New Roman', Times, serif !important;
                color: #1b1b1b !important;
                margin: 0 !important;
                padding: 0 !important;
                touch-action: pan-y !important;
            }
            body { overflow-y: auto !important; overflow-x: hidden !important; }
            #topBtn { display: none !important; }
            .section { background-color: rgba(255,255,255,0.55) !important; border-color: rgba(0,0,0,0.3) !important; }
            header { background-color: rgba(26, 58, 110, 0.85) !important; }
        `;
        doc.head.appendChild(style);

        this._hideLoadingScrap();
    }

    // ---------------------- show / hide ----------------------

    hide() {
        document.removeEventListener('click', this._outsideHandler, true);
        document.body.classList.remove('page-open');
        this.container.classList.remove('open');
        this.container.classList.add('closing');

        // Wait for the slide-out animation to finish, then tear down.
        const EXIT_MS = 420;
        setTimeout(() => {
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
        } else {
            this.closeLabel.textContent = '✕ close';
        }
    }

    _showLoadingScrap() {
        if (this._loadingEl) return;
        const el = document.createElement('div');
        el.className = 'loading-scrap';
        el.textContent = 'loading…';
        el.style.cssText = `
            position: absolute; top: 40px; left: 50%;
            transform: translateX(-50%) rotate(-3deg);
            font-family: var(--font-hand-casual, 'Caveat', cursive);
            font-size: 1.2rem; color: var(--ink-pencil, #3a3a3a);
            background: var(--paper-white, #fafaf3);
            padding: 6px 14px; border-radius: 2px;
            box-shadow: 2px 3px 5px rgba(0,0,0,0.25);
            z-index: 10; pointer-events: none;
        `;
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
            const protocol = window.location.protocol;
            const hostname = window.location.hostname;
            if (protocol === 'https:') return `https://${hostname}${url}`;
            return url;
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
            this.hide();
        };
    }

}

document.addEventListener("DOMContentLoaded", () => {
    const miniWindow = new MiniWindow();
    window.openPage = (route) => miniWindow.open(route);
    window.navigateToPage = (route) => miniWindow.navigateTo(route);
});
