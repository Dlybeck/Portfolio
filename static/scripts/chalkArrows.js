/**
 * chalkArrows.js — persistent chalk arrows on the chalkboard wall.
 *
 * One <path> per parent-child connection in tilesData. Arrows are
 * positioned in viewBox units (% of layer) and tracked to tile motion
 * via a transform on the parent <g>. Always visible; never fade.
 *
 * Config is exposed on window.chalkArrowsConfig so a tweak panel can
 * live-edit it. Call window.redrawChalkArrows() after config changes
 * to rebuild the SVG.
 */

(function () {
    let svg = null;
    let arrowsGroup = null;

    // ---- Config ----------------------------------------------------
    // Defaults match what we had hard-coded. The tweak panel mutates
    // this and calls redraw.
    window.chalkArrowsConfig = window.chalkArrowsConfig || {
        // Length of the arrow as a fraction of the center-to-center
        // distance: 0 = a dot at the midpoint, 1 = full line all the
        // way to each tile's center. Symmetric — the line is always
        // centered on the midpoint between the two tiles.
        length: 0.42,
        // Arrowhead style: 'open' (V), 'closed' (filled triangle), 'none'.
        headStyle: 'open',
        // Where to draw arrowheads: 'end', 'start', 'both', 'none'.
        headPosition: 'both',
        headLen: 1.5,
        headHalf: 1.2,
        // Line style.
        strokeWidth: 5.2,
        opacity: 1,
        color: '#f3efe2',
        // Subtle hand-drawn perpendicular wobble (viewBox units).
        wobble: 4.2,
    };
    const cfg = () => window.chalkArrowsConfig;

    function hash(s) {
        let h = 2166136261;
        for (let i = 0; i < s.length; i++) {
            h ^= s.charCodeAt(i);
            h = Math.imul(h, 16777619);
        }
        return h >>> 0;
    }

    function ensureSvg() {
        if (svg && svg.isConnected) return svg;
        const layer = document.querySelector('.tile-layer');
        if (!layer) return null;
        svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
        svg.setAttribute('class', 'chalk-arrows');
        svg.setAttribute('viewBox', '0 0 100 100');
        svg.setAttribute('preserveAspectRatio', 'none');
        svg.style.cssText = [
            'position: absolute',
            'inset: 0',
            'width: 100%',
            'height: 100%',
            'pointer-events: none',
            'overflow: visible',
            'z-index: 0',
        ].join(';');

        arrowsGroup = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        arrowsGroup.setAttribute('class', 'arrows-group');
        arrowsGroup.style.transition = 'transform 0.45s cubic-bezier(.2,.7,.2,1)';
        svg.appendChild(arrowsGroup);

        layer.appendChild(svg);
        return svg;
    }

    /**
     * Symmetric length-based endpoints. The arrow is always centered on
     * the midpoint between the two tile centers; `length` (0..1) sets
     * how far in each direction it reaches from that midpoint.
     *   length = 0 → both ends at the midpoint (a dot)
     *   length = 1 → from-end at fromCenter, to-end at toCenter
     */
    function computeEndpoints(fromX, fromY, toX, toY) {
        const dx = toX - fromX;
        const dy = toY - fromY;
        const len = Math.sqrt(dx * dx + dy * dy);
        if (len < 0.01) return { len: 0, fromX, fromY, toX, toY, ux: 0, uy: 0 };

        const ux = dx / len;
        const uy = dy / len;
        const t = Math.max(0, Math.min(1, cfg().length));
        const eachSide = (len / 2) * t;
        const midX = (fromX + toX) / 2;
        const midY = (fromY + toY) / 2;

        return {
            len,
            fromX: midX - ux * eachSide,
            fromY: midY - uy * eachSide,
            toX:   midX + ux * eachSide,
            toY:   midY + uy * eachSide,
            ux,
            uy,
        };
    }

    /**
     * <path> for an arrowhead at (tipX, tipY) pointing in (dirX, dirY).
     * style: 'open' = stroked V, 'closed' = filled triangle.
     */
    function makeHeadPath(tipX, tipY, dirX, dirY, style) {
        const c = cfg();
        const apx = -dirY;
        const apy = dirX;
        const baseX = tipX - dirX * c.headLen;
        const baseY = tipY - dirY * c.headLen;
        const leftX = baseX + apx * c.headHalf;
        const leftY = baseY + apy * c.headHalf;
        const rightX = baseX - apx * c.headHalf;
        const rightY = baseY - apy * c.headHalf;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('vector-effect', 'non-scaling-stroke');
        path.setAttribute('opacity', c.opacity);
        if (style === 'closed') {
            path.setAttribute('d',
                `M${leftX},${leftY} L${tipX},${tipY} L${rightX},${rightY} Z`);
            path.setAttribute('fill', c.color);
            path.setAttribute('stroke', c.color);
            path.setAttribute('stroke-width', c.strokeWidth * 0.6);
            path.setAttribute('stroke-linejoin', 'round');
        } else {
            path.setAttribute('d',
                `M${leftX},${leftY} L${tipX},${tipY} L${rightX},${rightY}`);
            path.setAttribute('fill', 'none');
            path.setAttribute('stroke', c.color);
            path.setAttribute('stroke-width', c.strokeWidth);
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
        }
        return path;
    }

    function makeLinePath(fromX, fromY, toX, toY, ux, uy, seed) {
        const c = cfg();
        // Subtle perpendicular wobble for hand-drawn feel.
        const px = -uy;
        const py = ux;
        const wob = (((seed % 100) / 100) - 0.5) * c.wobble;
        const mx = (fromX + toX) / 2 + px * wob;
        const my = (fromY + toY) / 2 + py * wob;

        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', `M${fromX},${fromY} Q${mx},${my} ${toX},${toY}`);
        path.setAttribute('stroke', c.color);
        path.setAttribute('stroke-width', c.strokeWidth);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('vector-effect', 'non-scaling-stroke');
        path.setAttribute('opacity', c.opacity);
        return path;
    }

    function makeArrow(fromCx, fromCy, toCx, toCy, seed) {
        const c = cfg();
        const e = computeEndpoints(fromCx, fromCy, toCx, toCy);
        if (e.len === 0) return null;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        g.appendChild(makeLinePath(e.fromX, e.fromY, e.toX, e.toY, e.ux, e.uy, seed));

        const showStart =
            c.headStyle !== 'none' &&
            (c.headPosition === 'start' || c.headPosition === 'both');
        const showEnd =
            c.headStyle !== 'none' &&
            (c.headPosition === 'end' || c.headPosition === 'both');

        if (showEnd) {
            g.appendChild(makeHeadPath(e.toX, e.toY, e.ux, e.uy, c.headStyle));
        }
        if (showStart) {
            // Arrow at start points toward FROM (back along the line) —
            // i.e. the V opens toward the parent (away from start).
            g.appendChild(makeHeadPath(e.fromX, e.fromY, -e.ux, -e.uy, c.headStyle));
        }
        return g;
    }

    function clearArrows() {
        if (!arrowsGroup) return;
        while (arrowsGroup.firstChild) arrowsGroup.removeChild(arrowsGroup.firstChild);
    }

    function drawAllArrows() {
        if (!ensureSvg()) return;
        if (!window.tilesData || !window.positions) return;
        clearArrows();

        Object.entries(window.tilesData).forEach(([parent, children]) => {
            const pPos = window.positions[parent];
            if (!pPos) return;
            children.forEach((child) => {
                const cPos = window.positions[child];
                if (!cPos) return;
                const seed = hash(parent + '|' + child);
                const arrow = makeArrow(
                    cPos.left, cPos.top,
                    pPos.left, pPos.top,
                    seed
                );
                if (arrow) arrowsGroup.appendChild(arrow);
            });
        });
    }

    function updateOffset(centerTitle) {
        if (!arrowsGroup || !window.positions) return;
        const centerPos = window.positions[centerTitle];
        if (!centerPos) return;
        const offsetX = 50 - centerPos.left;
        const offsetY = 52 - centerPos.top;
        arrowsGroup.setAttribute('transform', `translate(${offsetX}, ${offsetY})`);
    }

    /**
     * Public API used by tileCreation.js after each centerOnTile.
     * Draws once (lazily on first call), then just updates the pan
     * offset on subsequent calls.
     */
    let drawn = false;
    window.updateChalkArrows = function (centerTitle) {
        ensureSvg();
        if (!drawn) {
            drawAllArrows();
            // Note: arrows only DRAWN if extents were measurable.
            drawn = arrowsGroup && arrowsGroup.children.length > 0;
        }
        if (centerTitle) updateOffset(centerTitle);
    };

    /**
     * Force a full redraw with the current config. Called by the tweak
     * panel after any config change.
     */
    window.redrawChalkArrows = function () {
        ensureSvg();
        drawAllArrows();
        // Re-apply the offset for whatever tile is centered.
        const hash = decodeURIComponent(window.location.hash.slice(1));
        const center = (hash && window.positions && window.positions[hash])
            ? hash
            : 'Home';
        updateOffset(center);
    };
})();
