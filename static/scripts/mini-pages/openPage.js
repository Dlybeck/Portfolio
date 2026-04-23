/**
 * openPage.js — Paper-table theme
 *
 * A mini-page is NOT a scrollable overlay anymore. Instead we:
 *   1. Size the iframe to its content's natural scrollHeight (same-origin,
 *      so we can read contentDocument safely).
 *   2. Disable internal scrolling inside the iframe.
 *   3. Install mapPan (wheel/touch/keyboard) so scrolling pans the tabletop
 *      itself — the background, tiles, and the paper all move together.
 *   4. On close, animate mapPan back to 0, remove the paper, and leave the
 *      centered tile exactly where it was.
 *
 * Nothing morphs text or size in place — open/close are two elements
 * entering/leaving the stage.
 */

class MiniWindow {
    constructor() {
        this.container  = document.querySelector(".mini-window-container");
        this.page       = document.querySelector(".mini-window");
        this.closeButton = document.querySelector(".close-button");
        this.backButton  = document.querySelector(".back-button");
        this.navigationHistory = [];
        this.resizeObserver = null;

        // Hide close/back initially (the CSS .page-open rules reveal them)
        if (this.backButton) this.backButton.style.display = 'none';

        this.setEvents();
    }

    // ---------------------- open / close ----------------------

    open(route) {
        this.initialRoute = route;
        this.navigationHistory = [route];

        const normalized = this.normalizeUrl(route);
        this._loadInto(normalized);
        this.show();
        this.updateBackButtonState();
    }

    navigateTo(route) {
        const normalized = this.normalizeUrl(route);
        this.navigationHistory.push(normalized);
        this._loadInto(normalized);
        this.updateBackButtonState();
    }

    goBack() {
        if (!this.isVisible() || this.navigationHistory.length <= 1) return false;
        this.navigationHistory.pop();
        const previousUrl = this.navigationHistory[this.navigationHistory.length - 1];
        this._loadInto(previousUrl);
        this.updateBackButtonState();
        return true;
    }

    _loadInto(url) {
        // Reset pan bounds for the new page (height unknown until load)
        if (window.mapPan && window.mapPan.isActive()) {
            window.mapPan.setBounds(0);
        }
        // Show a temporary "Loading..." scrap overlay (separate element; no
        // textContent mutation on content elements).
        this._showLoadingScrap();

        this.page.setAttribute('src', url);
        this.page.onload = () => this._onIframeLoad();
    }

    _onIframeLoad() {
        let doc = null;
        try { doc = this.page.contentDocument; } catch (_) {}

        // Without content access we can't auto-size. Fall back to viewport height.
        if (!doc || !doc.body) {
            this.page.style.height = (window.innerHeight * 0.9) + 'px';
            if (window.mapPan) window.mapPan.setBounds(window.innerHeight * 0.9);
            this._hideLoadingScrap();
            return;
        }

        // Inject CSS that disables in-iframe scroll AND makes the body blend
        // into the paper theme (transparent background + ink colors).
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
                /* Disable iOS Safari's native touch panning/rubber-banding
                   inside the iframe so it doesn't fight mapPan for the
                   same gesture (that was the source of the "two
                   conflicting actions" feel on touch). */
                touch-action: none !important;
                -webkit-user-select: none;
                user-select: none;
            }
            /* Hide the legacy back-to-top button — the tabletop is the scroll surface */
            #topBtn { display: none !important; }
            /* Reduce solid panel look; keep content readable on paper */
            .section { background-color: rgba(255,255,255,0.55) !important; border-color: rgba(0,0,0,0.3) !important; }
            header { background-color: rgba(26, 58, 110, 0.85) !important; }
        `;
        doc.head.appendChild(style);

        // Measure once a tick later so layout has settled
        requestAnimationFrame(() => this._measureAndSize(doc));

        // Keep height in sync with dynamic content (images, model-viewer)
        if (this.resizeObserver) this.resizeObserver.disconnect();
        this.resizeObserver = new ResizeObserver(() => this._measureAndSize(doc));
        this.resizeObserver.observe(doc.body);
        // Also re-measure after images load (ResizeObserver misses some cases)
        const imgs = doc.images || [];
        Array.from(imgs).forEach(img => {
            if (!img.complete) img.addEventListener('load', () => this._measureAndSize(doc));
        });

        // Forward scroll/touch input FROM INSIDE the iframe to the parent
        // mapPan. Browsers don't let iframe events bubble to the parent
        // window, so without this, mouse-wheel/touch-drag over the paper
        // wouldn't pan the tabletop — exactly the bug the user hit.
        this._installInnerInputForwarding(doc);

        this._hideLoadingScrap();
    }

    _installInnerInputForwarding(doc) {
        // Events from inside the iframe don't bubble out to the parent window,
        // so we attach listeners to the iframe's own window AND document AND
        // documentElement (all three, because different browsers route wheel
        // events to different targets when body has overflow: hidden).
        const parent = window;
        const iframeWin = doc.defaultView;
        const targets = [iframeWin, doc, doc.documentElement, doc.body].filter(Boolean);

        const onWheel = (e) => {
            if (!parent.mapPan || !parent.mapPan.isActive()) return;
            e.preventDefault();
            e.stopPropagation();
            // Normalize multiple wheel event sources to pixels:
            //   - 'wheel' with deltaMode 0 (px), 1 (lines), 2 (pages)
            //   - legacy 'mousewheel' (uses wheelDelta, inverse sign)
            //   - legacy 'DOMMouseScroll' (uses detail)
            let dy = 0;
            if (typeof e.deltaY === 'number') {
                dy = e.deltaY;
                if (e.deltaMode === 1)      dy *= 16;                    // line → px
                else if (e.deltaMode === 2) dy *= window.innerHeight;    // page → px
            } else if (typeof e.wheelDelta === 'number') {
                dy = -e.wheelDelta;
            } else if (typeof e.detail === 'number') {
                dy = e.detail * 40;
            }
            if (window.__panDebug) console.log('[iframe wheel]', { deltaY: e.deltaY, deltaMode: e.deltaMode, dy });
            parent.mapPan.pan(dy);
        };

        const onTouchStart = (e) => {
            if (!parent.mapPan || !parent.mapPan.isActive()) return;
            // stopPropagation prevents the same event from firing on the
            // three additional targets we attach to (doc/docEl/body).
            // Without this, every touchmove triggered mapPan.touchMove 4×
            // per frame, which confuses velocity tracking and thrashes
            // state on mobile where compute is limited.
            e.stopPropagation();
            if (e.touches && e.touches.length === 1) {
                parent.mapPan.touchStart(e.touches[0].clientY);
            }
        };
        const onTouchMove = (e) => {
            if (!parent.mapPan || !parent.mapPan.isActive()) return;
            e.stopPropagation();
            if (e.touches && e.touches.length === 1) {
                if (e.cancelable) e.preventDefault();
                parent.mapPan.touchMove(e.touches[0].clientY);
            }
        };
        const onTouchEnd = (e) => {
            if (e) e.stopPropagation();
            if (parent.mapPan) parent.mapPan.touchEnd();
        };

        const onKey = (e) => {
            if (!parent.mapPan || !parent.mapPan.isActive()) return;
            const step = 80, big = window.innerHeight * 0.85;
            let dy = 0;
            switch (e.key) {
                case 'ArrowDown':  dy = step;  break;
                case 'ArrowUp':    dy = -step; break;
                case 'PageDown':
                case ' ':          dy = big;   break;
                case 'PageUp':     dy = -big;  break;
                default: return;
            }
            e.preventDefault();
            parent.mapPan.pan(dy);
        };

        targets.forEach(t => {
            if (!t || !t.addEventListener) return;
            t.addEventListener('wheel',        onWheel,      { passive: false, capture: true });
            t.addEventListener('mousewheel',   onWheel,      { passive: false, capture: true });
            t.addEventListener('DOMMouseScroll', onWheel,    { passive: false, capture: true });
            t.addEventListener('touchstart',   onTouchStart, { passive: true,  capture: true });
            t.addEventListener('touchmove',    onTouchMove,  { passive: false, capture: true });
            t.addEventListener('touchend',     onTouchEnd,   { capture: true });
            t.addEventListener('touchcancel',  onTouchEnd,   { capture: true });
            t.addEventListener('keydown',      onKey,        { capture: true });
        });
    }

    _measureAndSize(doc) {
        const h = Math.max(
            doc.body.scrollHeight,
            doc.documentElement ? doc.documentElement.scrollHeight : 0,
            240
        );
        this.page.style.height = h + 'px';
        this.container.style.height = 'auto';
        if (window.mapPan && window.mapPan.isActive()) {
            window.mapPan.setBounds(h + 120);
        }
    }

    // ---------------------- show / hide ----------------------

    show() {
        // Position the paper vertically based on where the centered tile sits.
        // A small delay so the container class change can be picked up by CSS.
        this.container.classList.add('open');
        // Install map-pan listeners; bounds updated once content loads.
        if (window.mapPan) window.mapPan.start(window.innerHeight);
        // Outside-click closes; register AFTER this click has fully resolved
        // (otherwise the very click that opened the page would close it).
        setTimeout(() => {
            document.addEventListener('click', this.handleClickOutside);
        }, 50);
    }

    hide() {
        // Paper exit = swap .open for .closing. The CSS paper-exit keyframe
        // slides the whole paper DOWN past the viewport bottom (translateY
        // 120vh), which clears it regardless of how tall the iframe content
        // is. After the animation ends we remove .closing and tear down.
        const EXIT_MS = 520; // slightly longer than the 0.5s CSS animation
        const finishClose = () => {
            this.container.classList.remove('open');
            this.container.classList.remove('closing');
            // Reset back-button inline display so CSS `body.page-open` rule
            // governs it cleanly next time a page opens.
            if (this.backButton) this.backButton.style.display = '';
            this.page.setAttribute('src', '');
            this.page.style.height = '';
            if (this.resizeObserver) {
                this.resizeObserver.disconnect();
                this.resizeObserver = null;
            }
            this.navigationHistory = [];
        };

        document.removeEventListener('click', this.handleClickOutside);

        // Start the exit animation: replace .open with .closing.
        this.container.classList.remove('open');
        this.container.classList.add('closing');

        // Animate the tabletop back to offset 0 in parallel with the paper
        // slide-off. Both finish in ~500ms and then we clean up.
        if (window.mapPan && window.mapPan.isActive()) {
            window.mapPan.stop();
        }
        setTimeout(finishClose, EXIT_MS);
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
        this.handleClickOutside = (event) => {
            // The close/back buttons are OUTSIDE the container in the new
            // layout (fixed-to-viewport tabs), so clicks there must not count
            // as outside clicks.
            if (this.container.contains(event.target)) return;
            if (this.closeButton && this.closeButton.contains(event.target)) return;
            if (this.backButton  && this.backButton.contains(event.target))  return;
            this.hide();
        };

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
}

// Expose openPage / navigateToPage
document.addEventListener("DOMContentLoaded", () => {
    const miniWindow = new MiniWindow();
    window.openPage = (route) => miniWindow.open(route);
    window.navigateToPage = (route) => miniWindow.navigateTo(route);
});
