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
        this.navigationIndex = -1;
        this.teardownTimer = null;
        this.outsideHandlerTimer = null;
        this.transitionRevision = 0;
        this.pendingLoadResolve = null;
        this.motionCleanups = new Set();

        this.setEvents();
    }

    motionDuration(defaultDuration) {
        return window.matchMedia('(prefers-reduced-motion: reduce)').matches
            ? 0
            : defaultDuration;
    }

    // ---------------------- open / close ----------------------

    open(route, options = {}) {
        this._cancelHandoff();
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
        const restoredHistory = this._historyForRoute(
            normalized,
            options.navigationHistory,
        );
        this.navigationHistory = restoredHistory || [normalized];
        this.navigationIndex = this.navigationHistory.length - 1;
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
        this.navigationHistory = this.navigationHistory.slice(
            0,
            this.navigationIndex + 1,
        );
        this.navigationHistory.push(normalized);
        this.navigationIndex = this.navigationHistory.length - 1;
        this._handoffTo(normalized);
    }

    goBack() {
        if (!this.isVisible() || this.navigationIndex <= 0) return false;
        window.history.back();
        return true;
    }

    restore(route, historyState = window.history.state) {
        const normalized = this.normalizeUrl(route);
        const restoredHistory = this._historyForRoute(
            normalized,
            historyState?.documentHistory,
        );

        if (!this.isVisible()) {
            this.open(normalized, {
                syncUrl: false,
                navigationHistory: restoredHistory,
            });
            return;
        }

        if (restoredHistory) {
            this.navigationHistory = restoredHistory;
            this.navigationIndex = restoredHistory.length - 1;
        } else {
            this.navigationHistory = [normalized];
            this.navigationIndex = 0;
        }
        this._handoffTo(normalized, { syncUrl: false });
    }

    _displayRoute(route, options = {}) {
        window.centerOnDestination(route);
        window.themeEngine?.styleReadingMaterial();
        this._setRouteMetadata(route, options);
        this._loadInto(window.documentUrlForRoute(route));
    }

    _setRouteMetadata(route, options = {}) {
        const routePath = new URL(route, window.location.origin).pathname;
        const documentTitle = window.portfolioState.documentTitles[routePath]
            || 'Portfolio';
        this.page.setAttribute('title', `${documentTitle} portfolio document`);
        if (options.syncUrl !== false) {
            window.setDestinationUrl(route, {
                documentHistory: this.navigationHistory,
            });
        }
        this.updateCloseButtonLabel();
    }

    async _handoffTo(route, options = {}) {
        if (this.motionDuration(1) === 0) {
            this._cancelHandoff();
            this._displayRoute(route, options);
            return;
        }

        const revision = ++this.transitionRevision;
        this._setRouteMetadata(route, options);
        this.container.setAttribute('aria-busy', 'true');
        document.body.classList.add('document-transitioning');
        if (this.closeButton) this.closeButton.disabled = true;

        const needsExit = this.container.classList.contains('open');
        if (needsExit) {
            this.container.classList.remove('open', 'handoff-entering');
            this.container.classList.add('handoff-leaving');
            await this._waitForMotion(this.container, {
                eventName: 'animationend',
                animationName: 'viewer-exit',
            });
            if (revision !== this.transitionRevision) return;
        }

        this.container.classList.remove('handoff-leaving', 'closing');
        this.container.classList.add('handoff-moving');

        const movement = this._moveBoardTo(route);
        window.themeEngine?.styleReadingMaterial();
        const loading = this._loadInto(window.documentUrlForRoute(route));
        await Promise.all([movement, loading]);
        if (revision !== this.transitionRevision) return;

        this.container.classList.remove('handoff-moving');
        this.container.classList.add('open', 'handoff-entering');
        await this._waitForMotion(this.container, {
            eventName: 'animationend',
            animationName: 'viewer-enter',
        });
        if (revision !== this.transitionRevision) return;

        this.container.classList.remove('handoff-entering');
        this.container.removeAttribute('aria-busy');
        document.body.classList.remove('document-transitioning');
        if (this.closeButton) this.closeButton.disabled = false;
    }

    _moveBoardTo(route) {
        const layer = document.querySelector('.tile-layer');
        const before = layer?.style.transform || '';
        window.centerOnDestination(route);
        const after = layer?.style.transform || '';
        if (!layer || before === after) return Promise.resolve();
        return this._waitForMotion(layer, {
            eventName: 'transitionend',
            propertyName: 'transform',
        });
    }

    _loadInto(url) {
        this._showLoadingScrap();
        if (this.pendingLoadResolve) this.pendingLoadResolve(false);
        return new Promise((resolve) => {
            this.pendingLoadResolve = resolve;
            this.page.onload = () => {
                this.pendingLoadResolve = null;
                this._onIframeLoad();
                resolve(true);
            };
            // The outer Portfolio URL owns browser history. Replacing the iframe
            // document avoids adding a second joint-session-history entry that
            // would otherwise leave the URL and visible document out of sync when
            // the viewer presses the browser Back button.
            this._replaceIframeLocation(url);
        });
    }

    _replaceIframeLocation(url) {
        if (this.page.contentWindow) {
            this.page.contentWindow.location.replace(url);
        } else {
            this.page.setAttribute('src', url);
        }
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
        // Returning Home while already on the Board must not manufacture a
        // Viewer exit. Adding `closing` here used to flash an empty document
        // over the Board even though no document had been opened.
        if (!this.isVisible()) return false;

        this._cancelHandoff();
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
            this.page.onload = null;
            if (this.pendingLoadResolve) {
                this.pendingLoadResolve(false);
                this.pendingLoadResolve = null;
            }
            this._replaceIframeLocation('about:blank');
            this.navigationHistory = [];
            this.navigationIndex = -1;
        }, EXIT_MS);
        return true;
    }

    // ---------------------- helpers ----------------------

    isVisible() {
        return document.body.classList.contains('page-open');
    }

    _cancelHandoff() {
        this.transitionRevision += 1;
        [...this.motionCleanups].forEach((cleanup) => cleanup());
        this.motionCleanups.clear();
        if (this.pendingLoadResolve) {
            this.pendingLoadResolve(false);
            this.pendingLoadResolve = null;
        }
        this.container.classList.remove(
            'handoff-leaving',
            'handoff-moving',
            'handoff-entering',
        );
        this.container.removeAttribute('aria-busy');
        document.body.classList.remove('document-transitioning');
        if (this.closeButton) this.closeButton.disabled = false;
    }

    _motionMilliseconds(value) {
        const trimmed = value.trim();
        if (trimmed.endsWith('ms')) return Number.parseFloat(trimmed) || 0;
        if (trimmed.endsWith('s')) {
            return (Number.parseFloat(trimmed) || 0) * 1000;
        }
        return 0;
    }

    _motionFallbackMilliseconds(element, eventName) {
        const style = getComputedStyle(element);
        const durationSource = eventName === 'animationend'
            ? style.animationDuration
            : style.transitionDuration;
        const delaySource = eventName === 'animationend'
            ? style.animationDelay
            : style.transitionDelay;
        const durations = durationSource.split(',').map(
            (value) => this._motionMilliseconds(value),
        );
        const delays = delaySource.split(',').map(
            (value) => this._motionMilliseconds(value),
        );
        const count = Math.max(durations.length, delays.length);
        let longest = 0;
        for (let index = 0; index < count; index += 1) {
            longest = Math.max(
                longest,
                durations[index % durations.length] + delays[index % delays.length],
            );
        }
        return longest;
    }

    _waitForMotion(element, {
        eventName,
        animationName = null,
        propertyName = null,
    }) {
        if (this.motionDuration(1) === 0) return Promise.resolve();
        const fallbackMilliseconds = this._motionFallbackMilliseconds(
            element,
            eventName,
        );
        if (fallbackMilliseconds <= 1) return Promise.resolve();

        return new Promise((resolve) => {
            let timeout = null;
            const finish = () => {
                element.removeEventListener(eventName, onMotionEnd);
                if (timeout !== null) clearTimeout(timeout);
                this.motionCleanups.delete(finish);
                resolve();
            };
            const onMotionEnd = (event) => {
                if (event.target !== element) return;
                if (animationName && event.animationName !== animationName) return;
                if (propertyName && event.propertyName !== propertyName) return;
                finish();
            };

            element.addEventListener(eventName, onMotionEnd);
            timeout = setTimeout(finish, fallbackMilliseconds + 150);
            this.motionCleanups.add(finish);
        });
    }

    /**
     * Update the single button's label based on navigation state:
     *   - history length > 1  → "← back" (clicking goes back one step)
     *   - history length === 1 → "✕ close" (clicking closes the paper)
     */
    updateCloseButtonLabel() {
        if (!this.closeLabel) return;
        if (this.navigationIndex > 0) {
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

    _historyForRoute(route, history) {
        if (!Array.isArray(history) || history.length === 0) return null;
        const normalized = history.map((entry) => this.normalizeUrl(entry));
        return normalized.at(-1) === route ? normalized : null;
    }

    setEvents() {
        // Single button — contextual action.
        if (this.closeButton) {
            this.closeButton.addEventListener('click', (e) => {
                e.stopPropagation();
                if (this.navigationIndex > 0) this.goBack();
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
    window.restorePageFromHistory = (route, historyState) => (
        miniWindow.restore(route, historyState)
    );
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
