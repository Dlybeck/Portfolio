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

    // ONE chalk roughness filter, applied identically to every arrow —
    // consistent texture across the diagram, like the same piece of
    // chalk drew everything. Variety comes from path geometry instead.

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

        // Chalk via diffuse lighting on a turbulence height map.
        //
        // Recipe picked from the test bench (G5):
        //   feTurbulence generates a fine-grain "bumpy surface."
        //   feDiffuseLighting renders that surface with a directional
        //     light, producing light/shadow patches that look like a
        //     dimensional chalk dust catching light.
        //   feComposite "in" clips the lit texture to the stroke shape.
        //   feMerge layers the original solid stroke + the lit grain.
        //
        // surfaceScale is the bump height in user-space units. The test
        // bench used pixel-space at 5; this filter runs in viewBox 0–100
        // stretched to the layer (~1000×600px on desktop), so the
        // equivalent physical bump height is ~0.5 viewBox units.
        const defs = document.createElementNS('http://www.w3.org/2000/svg', 'defs');
        defs.innerHTML = `
            <filter id="chalk-rough"
                    filterUnits="userSpaceOnUse"
                    primitiveUnits="userSpaceOnUse"
                    x="-100" y="-100" width="300" height="300">
                <feTurbulence type="fractalNoise" baseFrequency="3.5" numOctaves="3" seed="2" result="t"/>
                <feDiffuseLighting in="t" surfaceScale="0.28" diffuseConstant="1.2" lighting-color="#f3efe2" result="light">
                    <feDistantLight azimuth="45" elevation="55"/>
                </feDiffuseLighting>
                <feComposite in="light" in2="SourceGraphic" operator="in" result="lit"/>
                <feMerge>
                    <feMergeNode in="SourceGraphic"/>
                    <feMergeNode in="lit"/>
                </feMerge>
            </filter>
        `;
        svg.appendChild(defs);

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

    function makeStrokePath(d, color, width, opacity, dasharray) {
        const path = document.createElementNS('http://www.w3.org/2000/svg', 'path');
        path.setAttribute('d', d);
        path.setAttribute('stroke', color);
        path.setAttribute('stroke-width', width);
        path.setAttribute('fill', 'none');
        path.setAttribute('stroke-linecap', 'round');
        path.setAttribute('vector-effect', 'non-scaling-stroke');
        path.setAttribute('opacity', opacity);
        if (dasharray) path.setAttribute('stroke-dasharray', dasharray);
        return path;
    }

    /**
     * Two-pass chalk stroke. The parent <g>'s displacement filter adds
     * the fine chalk grain — both passes share it identically.
     *   1. Halo — soft chalk-dust haze around the main stroke
     *   2. Main — primary chalk body
     */
    function appendChalkLine(g, d) {
        const c = cfg();
        const mainWidth = c.strokeWidth;
        g.appendChild(makeStrokePath(d, c.color, mainWidth * 1.55, c.opacity * 0.16));
        g.appendChild(makeStrokePath(d, c.color, mainWidth, c.opacity));
    }

    /**
     * Build a path d-string from `from` to `to` with per-seed shape
     * variety. Same connection always gets the same shape (deterministic
     * from seed) so the diagram is stable across reloads, but different
     * connections get visibly different curves — single bump, S-curve,
     * double-bump, big sweep, gentle squiggle. Reads as "different lines
     * drawn by hand," not "machine-stamped identical curves."
     */
    function buildLineD(fromX, fromY, toX, toY, ux, uy, seed) {
        const c = cfg();
        const px = -uy;
        const py = ux;
        const dx = toX - fromX;
        const dy = toY - fromY;

        // Two independent perpendicular offsets pulled from different
        // bits of the seed.
        const w = c.wobble;
        const off1 = (((seed % 100) / 100) - 0.5) * w;
        const off2 = (((seed >> 7) % 100) / 100 - 0.5) * w;

        const styleIdx = seed % 5;

        // Complex paths visually amplify the wobble (S-curves bend
        // BOTH directions, two-bump cubics carry control points twice,
        // squiggles have three bumps). Tone them down so they look
        // similar in magnitude to the simple Q curve at the same wobble
        // setting.
        if (styleIdx === 0) {
            // Single quadratic bump — the simplest curve.
            const mx = fromX + dx * 0.5 + px * off1;
            const my = fromY + dy * 0.5 + py * off1;
            return `M${fromX},${fromY} Q${mx},${my} ${toX},${toY}`;
        }
        if (styleIdx === 1) {
            // S-curve — opposing controls. Scaled to 0.45 so the
            // double-deflection isn't twice as curvy as a Q.
            const k = 0.45;
            const c1x = fromX + dx * 0.33 + px * off1 * k;
            const c1y = fromY + dy * 0.33 + py * off1 * k;
            const c2x = fromX + dx * 0.67 - px * off1 * k;
            const c2y = fromY + dy * 0.67 - py * off1 * k;
            return `M${fromX},${fromY} C${c1x},${c1y} ${c2x},${c2y} ${toX},${toY}`;
        }
        if (styleIdx === 2) {
            // Double-bump — same-side controls. Scaled to 0.5.
            const k = 0.5;
            const c1x = fromX + dx * 0.3 + px * off1 * k;
            const c1y = fromY + dy * 0.3 + py * off1 * k;
            const c2x = fromX + dx * 0.7 + px * off2 * k;
            const c2y = fromY + dy * 0.7 + py * off2 * k;
            return `M${fromX},${fromY} C${c1x},${c1y} ${c2x},${c2y} ${toX},${toY}`;
        }
        if (styleIdx === 3) {
            // Slightly bigger single sweep — exaggerated 1.15× rather
            // than the previous 1.7× (which made these stand out too
            // strongly from the rest).
            const mx = fromX + dx * 0.5 + px * off1 * 1.15;
            const my = fromY + dy * 0.5 + py * off1 * 1.15;
            return `M${fromX},${fromY} Q${mx},${my} ${toX},${toY}`;
        }
        // styleIdx === 4: Gentle squiggle — three tiny bumps. All offsets
        // scaled to 0.32 so it reads as "slightly wavy" instead of
        // "deeply zig-zagged."
        const k = 0.32;
        const halfX = fromX + dx * 0.5;
        const halfY = fromY + dy * 0.5;
        const c1x = fromX + dx * 0.25 + px * off1 * k;
        const c1y = fromY + dy * 0.25 + py * off1 * k;
        const c2x = fromX + dx * 0.5  - px * off1 * k * 0.6;
        const c2y = fromY + dy * 0.5  - py * off1 * k * 0.6;
        const c3x = halfX             + px * off2 * k * 0.6;
        const c3y = halfY             + py * off2 * k * 0.6;
        const c4x = fromX + dx * 0.75 - px * off2 * k;
        const c4y = fromY + dy * 0.75 - py * off2 * k;
        return (
            `M${fromX},${fromY} ` +
            `C${c1x},${c1y} ${c2x},${c2y} ${halfX},${halfY} ` +
            `C${c3x},${c3y} ${c4x},${c4y} ${toX},${toY}`
        );
    }

    function makeArrow(fromCx, fromCy, toCx, toCy, seed) {
        const c = cfg();
        const e = computeEndpoints(fromCx, fromCy, toCx, toCy);
        if (e.len === 0) return null;

        const g = document.createElementNS('http://www.w3.org/2000/svg', 'g');
        // Shared chalk-grain filter on the whole group — both halo
        // and main stroke get the same fine displacement, so they
        // stay perfectly aligned (no "double line" drift).
        g.setAttribute('filter', 'url(#chalk-rough)');

        const lineD = buildLineD(e.fromX, e.fromY, e.toX, e.toY, e.ux, e.uy, seed);
        appendChalkLine(g, lineD);

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
