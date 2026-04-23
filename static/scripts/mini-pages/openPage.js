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
        this.backButton  = document.querySelector(".back-button");
        this.navigationHistory = [];
        this.resizeObserver = null;

        if (this.backButton) this.backButton.style.display = 'none';
        this.setEvents();
        this._installScrollParallax();
    }

    // ---------------------- open / close ----------------------

    open(route) {
        this.initialRoute = route;
        this.navigationHistory = [route];

        const normalized = this.normalizeUrl(route);
        this._loadInto(normalized);

        // Start at the top of the document so the paper enters from above.
        window.scrollTo(0, 0);
        this.container.classList.remove('closing');
        this.container.classList.add('open');
        document.body.classList.add('page-open');

        this.updateBackButtonState();
    }

    navigateTo(route) {
        const normalized = this.normalizeUrl(route);
        this.navigationHistory.push(normalized);
        this._loadInto(normalized);
        this.updateBackButtonState();
        window.scrollTo(0, 0);
    }

    goBack() {
        if (!this.isVisible() || this.navigationHistory.length <= 1) return false;
        this.navigationHistory.pop();
        const previousUrl = this.navigationHistory[this.navigationHistory.length - 1];
        this._loadInto(previousUrl);
        this.updateBackButtonState();
        window.scrollTo(0, 0);
        return true;
    }

    _loadInto(url) {
        this._showLoadingScrap();
        this.page.setAttribute('src', url);
        this.page.onload = () => this._onIframeLoad();
    }

    _onIframeLoad() {
        let doc = null;
        try { doc = this.page.contentDocument; } catch (_) {}

        if (!doc || !doc.body) {
            this.page.style.height = (window.innerHeight * 0.9) + 'px';
            this._hideLoadingScrap();
            return;
        }

        // Inject styles inside the iframe: disable its own scroll (the
        // outer body scrolls instead), apply the paper theme.
        const style = doc.createElement('style');
        style.setAttribute('data-paper-table', '');
        style.textContent = `
            html, body {
                overflow: hidden !important;
                height: auto !important;
                background: transparent !important;
                font-family: 'Kalam', 'Caveat', cursive !important;
                color: #1b1b1b !important;
                margin: 0 !important;
                padding: 0 !important;
            }
            #topBtn { display: none !important; }
            .section { background-color: rgba(255,255,255,0.55) !important; border-color: rgba(0,0,0,0.3) !important; }
            header { background-color: rgba(26, 58, 110, 0.85) !important; }
        `;
        doc.head.appendChild(style);

        requestAnimationFrame(() => this._measureAndSize(doc));

        if (this.resizeObserver) this.resizeObserver.disconnect();
        this.resizeObserver = new ResizeObserver(() => this._measureAndSize(doc));
        this.resizeObserver.observe(doc.body);
        Array.from(doc.images || []).forEach(img => {
            if (!img.complete) img.addEventListener('load', () => this._measureAndSize(doc));
        });

        this._hideLoadingScrap();
    }

    _measureAndSize(doc) {
        // Measure actual content bottom by finding the lowest-bottomed
        // visible child of body. body.scrollHeight can over-report for
        // pages with trailing margins, flex gaps, or inline whitespace
        // after the last element — we were seeing that as "extra length
        // for no reason" on some pages. Iterating top-level children
        // and taking max(offsetTop + offsetHeight) trims this cleanly.
        let contentBottom = 0;
        const children = doc.body.children;
        for (let i = 0; i < children.length; i++) {
            const el = children[i];
            if (el.offsetParent === null) continue;       // display: none
            if (el.id === 'topBtn') continue;             // fixed-position helper
            const bottom = el.offsetTop + el.offsetHeight;
            if (bottom > contentBottom) contentBottom = bottom;
        }
        // Also consult body/document scrollHeight as a safety floor in
        // case offsetTop/Height is unreliable (e.g. transformed
        // descendants). Take the min of our measurement and scrollHeight
        // so we bound extra whitespace.
        const bodyScroll = doc.body.scrollHeight;
        const docScroll  = doc.documentElement ? doc.documentElement.scrollHeight : 0;
        const scrollMax  = Math.max(bodyScroll, docScroll);

        // Start with contentBottom + small pad; if it's wildly less than
        // scrollMax, trust scrollMax (some layouts confuse offsetParent).
        let h = contentBottom + 24;
        if (h < scrollMax * 0.5) h = scrollMax;
        h = Math.max(240, h);

        this.page.style.height = h + 'px';
    }

    // ---------------------- show / hide ----------------------

    hide() {
        document.body.classList.remove('page-open');
        this.container.classList.remove('open');
        this.container.classList.add('closing');

        // After the fade-out completes, tear down: clear the iframe,
        // hide the container entirely so body goes back to short.
        const EXIT_MS = 320;
        setTimeout(() => {
            this.container.classList.remove('closing');
            if (this.backButton) this.backButton.style.display = '';
            this.page.setAttribute('src', '');
            this.page.style.height = '';
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
                this.resizeObserver = null;
            }
            this.navigationHistory = [];
            window.scrollTo(0, 0);
        }, EXIT_MS);
    }

    // ---------------------- helpers ----------------------

    isVisible() {
        return this.container.classList.contains('open');
    }

    updateBackButtonState() {
        if (!this.backButton) return;
        this.backButton.style.display =
            this.navigationHistory.length > 1 ? 'flex' : 'none';
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
        if (this.closeButton) {
            this.closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.hide();
            });
        }
        if (this.backButton) {
            this.backButton.addEventListener('click', (e) => {
                e.stopPropagation();
                this.goBack();
            });
        }
    }

    /**
     * Wall parallax — on scroll, update a CSS var on .map that the wall
     * underlay (::before) reads. The wall translates at 0.5× the scroll
     * speed so it drifts slowly behind the paper as the user scrolls.
     * Passive listener + RAF-coalesced writes = essentially free.
     */
    _installScrollParallax() {
        let pending = false;
        const map = document.querySelector('.map');
        if (!map) return;
        window.addEventListener('scroll', () => {
            if (pending) return;
            pending = true;
            requestAnimationFrame(() => {
                pending = false;
                map.style.setProperty('--scroll-parallax', (window.scrollY * 0.5) + 'px');
            });
        }, { passive: true });
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const miniWindow = new MiniWindow();
    window.openPage = (route) => miniWindow.open(route);
    window.navigateToPage = (route) => miniWindow.navigateTo(route);
});
