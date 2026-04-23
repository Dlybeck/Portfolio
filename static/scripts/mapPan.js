/**
 * mapPan.js — Pan the tabletop (.map) vertically while a mini-page is open.
 *
 * Mental model: when a page is "open" its long paper strip lies on the
 * tabletop. The viewport isn't scrolling — the tabletop (wood grain, all
 * tiles, and the paper together) slides underneath the viewport. Wheel,
 * touch-drag, and keyboard events all translate the .map element's Y axis.
 * Closing the page animates .map back to offset 0.
 *
 * This module exposes a single controller on window.mapPan with start/stop/
 * setBounds so openPage.js can own the lifecycle.
 */

(function() {
    const STATE = {
        el: null,          // .map element
        active: false,
        offsetX: 0,        // horizontal offset (tracked but we only pan Y)
        offsetY: 0,
        maxY: 0,           // computed from unfurled paper height
        velocity: 0,       // for touch-release momentum
        lastMoveTime: 0,
        lastMoveY: 0,
        dragging: false,
        dragStartY: 0,
        dragStartOffsetY: 0,
        rafId: null,
        momentumRafId: null,
    };

    function clampY(y) {
        if (y < 0) return 0;
        if (y > STATE.maxY) return STATE.maxY;
        return y;
    }

    function applyTransform() {
        if (!STATE.el) return;
        STATE.el.style.transform =
            `translate3d(${STATE.offsetX}px, ${-STATE.offsetY}px, 0)`;
    }

    function smoothTo(targetY, duration = 420, onDone) {
        cancelMomentum();
        const startY = STATE.offsetY;
        const delta = targetY - startY;
        const startTime = performance.now();
        STATE.el.classList.add('panning');

        function tick(now) {
            const t = Math.min(1, (now - startTime) / duration);
            // ease-out-cubic
            const eased = 1 - Math.pow(1 - t, 3);
            STATE.offsetY = startY + delta * eased;
            applyTransform();
            if (t < 1) {
                STATE.rafId = requestAnimationFrame(tick);
            } else {
                STATE.el.classList.remove('panning');
                if (onDone) onDone();
            }
        }
        if (STATE.rafId) cancelAnimationFrame(STATE.rafId);
        STATE.rafId = requestAnimationFrame(tick);
    }

    function cancelMomentum() {
        if (STATE.momentumRafId) {
            cancelAnimationFrame(STATE.momentumRafId);
            STATE.momentumRafId = null;
        }
        if (STATE.rafId) {
            cancelAnimationFrame(STATE.rafId);
            STATE.rafId = null;
        }
    }

    function runMomentum() {
        // Decay velocity and translate until it settles
        cancelMomentum();
        STATE.el.classList.add('panning');
        const friction = 0.94;
        function step() {
            STATE.velocity *= friction;
            if (Math.abs(STATE.velocity) < 0.25) {
                STATE.el.classList.remove('panning');
                STATE.momentumRafId = null;
                return;
            }
            const next = clampY(STATE.offsetY + STATE.velocity);
            if (next === STATE.offsetY) {
                // hit a bound, stop
                STATE.el.classList.remove('panning');
                STATE.momentumRafId = null;
                return;
            }
            STATE.offsetY = next;
            applyTransform();
            STATE.momentumRafId = requestAnimationFrame(step);
        }
        STATE.momentumRafId = requestAnimationFrame(step);
    }

    // ---------- Event handlers (installed only while active) ----------

    function panBy(dy) {
        // RAF-coalesced pan write — see the public .pan() method comment.
        cancelMomentum();
        STATE.el.classList.add('panning');
        // Track last scroll direction globally so cover exits can animate
        // AWAY from the direction the user is scrolling (keeps the cover
        // from ever stalling mid-viewport during simultaneous pan + exit).
        if (dy !== 0) window._lastScrollDir = dy > 0 ? 1 : -1;
        STATE.pendingDy = (STATE.pendingDy || 0) + dy;
        if (!STATE.panRaf) {
            STATE.panRaf = requestAnimationFrame(() => {
                STATE.panRaf = null;
                const pending = STATE.pendingDy || 0;
                STATE.pendingDy = 0;
                STATE.offsetY = clampY(STATE.offsetY + pending);
                applyTransform();
            });
        }
        clearTimeout(STATE._panClear);
        STATE._panClear = setTimeout(
            () => STATE.el.classList.remove('panning'), 140);
    }

    function onWheel(e) {
        if (!STATE.active) return;
        if (STATE.maxY <= 0) return;
        e.preventDefault();
        let dy = e.deltaY;
        if (e.deltaMode === 1)      dy *= 16;
        else if (e.deltaMode === 2) dy *= window.innerHeight;
        if (window.__panDebug) console.log('[outer wheel]', { deltaY: e.deltaY, deltaMode: e.deltaMode, dy, offsetY: STATE.offsetY, maxY: STATE.maxY });
        panBy(dy);
    }

    function onKey(e) {
        if (!STATE.active) return;
        const step = 80;
        const big = window.innerHeight * 0.85;
        let handled = true;
        let next = STATE.offsetY;
        switch (e.key) {
            case 'ArrowDown':  next += step; break;
            case 'ArrowUp':    next -= step; break;
            case 'PageDown':
            case ' ':          next += big;  break;
            case 'PageUp':     next -= big;  break;
            case 'Home':       next = 0; break;
            case 'End':        next = STATE.maxY; break;
            default:           handled = false;
        }
        if (!handled) return;
        e.preventDefault();
        smoothTo(clampY(next), 260);
    }

    function onTouchStart(e) {
        if (!STATE.active || !e.touches || e.touches.length !== 1) return;
        cancelMomentum();
        STATE.dragging = true;
        STATE.dragStartY = e.touches[0].clientY;
        STATE.dragStartOffsetY = STATE.offsetY;
        STATE.lastMoveTime = performance.now();
        STATE.lastMoveY = STATE.dragStartY;
        STATE.velocity = 0;
        STATE.el.classList.add('panning');
    }

    function onTouchMove(e) {
        if (!STATE.dragging || !e.touches || e.touches.length !== 1) return;
        const y = e.touches[0].clientY;
        const delta = STATE.dragStartY - y;
        STATE.offsetY = clampY(STATE.dragStartOffsetY + delta);
        applyTransform();

        const now = performance.now();
        const dt = now - STATE.lastMoveTime;
        if (dt > 0) {
            // velocity in px/frame (~16ms)
            STATE.velocity = ((STATE.lastMoveY - y) / dt) * 16;
        }
        STATE.lastMoveTime = now;
        STATE.lastMoveY = y;

        if (e.cancelable) e.preventDefault();
    }

    function onTouchEnd() {
        if (!STATE.dragging) return;
        STATE.dragging = false;
        // Apply momentum if the last movement was fast enough
        if (Math.abs(STATE.velocity) > 1.5) {
            runMomentum();
        } else {
            STATE.el.classList.remove('panning');
        }
    }

    // ---------- Public API ----------

    window.mapPan = {
        /**
         * Begin panning mode. Installs listeners and records max pan extent.
         * @param {number} contentHeight - natural pixel height of the open paper
         */
        start(contentHeight) {
            const map = document.querySelector('.map');
            if (!map) return;
            STATE.el = map;
            STATE.active = true;
            STATE.offsetY = 0;
            STATE.offsetX = 0;
            this.setBounds(contentHeight);

            window.addEventListener('wheel',      onWheel,      { passive: false });
            window.addEventListener('keydown',    onKey);
            window.addEventListener('touchstart', onTouchStart, { passive: true });
            window.addEventListener('touchmove',  onTouchMove,  { passive: false });
            window.addEventListener('touchend',   onTouchEnd);
            window.addEventListener('touchcancel',onTouchEnd);

            document.body.classList.add('page-open');
            applyTransform();
        },

        /**
         * Update the max pan extent (e.g. after iframe content resize).
         * @param {number} contentHeight
         */
        setBounds(contentHeight) {
            // Leave a ~20vh breathing room below the paper.
            const vh = window.innerHeight;
            const visibleBuffer = vh * 0.15;
            STATE.maxY = Math.max(0, contentHeight - vh + visibleBuffer + 80);
            // Re-clamp current offset in case content shrank
            STATE.offsetY = clampY(STATE.offsetY);
            applyTransform();
        },

        /**
         * Stop panning, animate back to offset 0, and remove listeners.
         * @param {Function} [onDone]
         */
        stop(onDone) {
            if (!STATE.active) { if (onDone) onDone(); return; }
            STATE.active = false;

            window.removeEventListener('wheel',      onWheel);
            window.removeEventListener('keydown',    onKey);
            window.removeEventListener('touchstart', onTouchStart);
            window.removeEventListener('touchmove',  onTouchMove);
            window.removeEventListener('touchend',   onTouchEnd);
            window.removeEventListener('touchcancel',onTouchEnd);

            document.body.classList.remove('page-open');
            smoothTo(0, 380, () => {
                if (onDone) onDone();
            });
        },

        /** Whether panning mode is active right now. */
        isActive() { return STATE.active; },

        /** Current vertical offset in px. */
        getOffsetY() { return STATE.offsetY; },

        /**
         * Directly push a scroll delta into the tabletop pan.
         * Used by openPage.js to forward wheel events from inside the
         * iframe (which can't bubble out to window). Multiple calls in the
         * same frame are coalesced into a single transform write via RAF —
         * keeps rapid trackpad/smooth-scroll input from flooding the
         * compositor with redundant transform updates.
         */
        pan(dy) {
            if (!STATE.active || STATE.maxY <= 0) return;
            panBy(dy);
        },

        /**
         * Push a touch-drag delta (for touch events forwarded from inside
         * the iframe). Implements a simple drag-with-momentum using the
         * same velocity tracking as native touch.
         */
        touchStart(clientY) {
            if (!STATE.active) return;
            cancelMomentum();
            STATE.dragging = true;
            STATE.dragStartY = clientY;
            STATE.dragStartOffsetY = STATE.offsetY;
            STATE.lastMoveTime = performance.now();
            STATE.lastMoveY = clientY;
            STATE.velocity = 0;
            STATE.el.classList.add('panning');
        },
        touchMove(clientY) {
            if (!STATE.dragging) return;
            const delta = STATE.dragStartY - clientY;
            STATE.offsetY = clampY(STATE.dragStartOffsetY + delta);
            applyTransform();
            const now = performance.now();
            const dt = now - STATE.lastMoveTime;
            if (dt > 0) STATE.velocity = ((STATE.lastMoveY - clientY) / dt) * 16;
            STATE.lastMoveTime = now;
            STATE.lastMoveY = clientY;
        },
        touchEnd() {
            if (!STATE.dragging) return;
            STATE.dragging = false;
            if (Math.abs(STATE.velocity) > 1.5) runMomentum();
            else STATE.el.classList.remove('panning');
        },
    };
})();
