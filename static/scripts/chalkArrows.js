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
        // Distance in PIXELS from each tile's center to where the arrow
        // ends. With inset ~ expanded-paper half-width (~120px on
        // desktop, ~136px on mobile), arrow ends are HIDDEN beneath the
        // centered tile's expanded paper — visually the arrow looks
        // like it points away from the centered tile, with its near
        // end vanishing under the paper. Same constant px regardless
        // of tile spacing, so it works on every viewport size.
        inset: 100,
        headStyle: 'open',
        headPosition: 'both',
        headLen: 15,
        headHalf: 12,
        strokeWidth: 5.2,
        opacity: 1,
        color: '#f3efe2',
        // Wobble is a FRACTION of line length (not absolute px) so the
        // curvature looks similar regardless of how far apart the two
        // tiles are. 0.14 means each control-point offset can be up to
        // ±7% of line length on each side of the chord.
        wobble: 0.14,
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
        // viewBox is set dynamically to match the layer's pixel
        // dimensions in updateViewBox() so arrows render in 1:1 pixel
        // space — no stretching, no aspect-ratio distortion of curves
        // or arrowheads on narrow viewports.
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
        // Filter parameters recalibrated for pixel-space user coords
        // (was viewBox 0-100):
        //   baseFrequency 3.5 → 0.35 — noise features ~3px instead of
        //     ~0.3px (which was sub-pixel and invisible)
        //   surfaceScale 0.28 → 2.8 — bump height in pixels
        //   filter region now spans -2000 to +5000 in both axes,
        //     comfortably larger than any viewport
        defs.innerHTML = `
            <filter id="chalk-rough"
                    filterUnits="userSpaceOnUse"
                    primitiveUnits="userSpaceOnUse"
                    x="-2000" y="-2000" width="7000" height="7000">
                <feTurbulence type="fractalNoise" baseFrequency="0.35" numOctaves="3" seed="2" result="t"/>
                <feDiffuseLighting in="t" surfaceScale="2.8" diffuseConstant="1.2" lighting-color="#f3efe2" result="light">
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
     * Inset-based endpoints. Arrow ends sit a FIXED pixel distance
     * inset from each tile's center, regardless of how far apart the
     * tiles are. This ensures the arrow's near-tile portion is hidden
     * under the centered tile's expanded paper across all viewport
     * sizes (desktop wide, phone narrow, etc.).
     *
     * For very close tiles (where 2*inset would exceed total distance),
     * the inset is scaled down to leave a small visible arrow.
     */
    function computeEndpoints(fromX, fromY, toX, toY) {
        const dx = toX - fromX;
        const dy = toY - fromY;
        const len = Math.sqrt(dx * dx + dy * dy);
        if (len < 0.01) return { len: 0, fromX, fromY, toX, toY, ux: 0, uy: 0 };

        const ux = dx / len;
        const uy = dy / len;

        let inset = Math.max(0, cfg().inset);
        // For close tiles (small viewports especially), cap inset at
        // 30% of total distance so at least 40% of the line stays
        // visible. Without this, on iPhone-SE-width screens the entire
        // arrow gets eaten by the inset on each side.
        const maxInset = len * 0.3;
        if (inset > maxInset) inset = maxInset;

        return {
            len,
            fromX: fromX + ux * inset,
            fromY: fromY + uy * inset,
            toX:   toX   - ux * inset,
            toY:   toY   - uy * inset,
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
        const lineLen = Math.sqrt(dx * dx + dy * dy);

        // Wobble is a FRACTION of line length, so curvature stays
        // visually consistent across short and long arrows.
        const w = c.wobble * lineLen;
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

    /**
     * Sets the SVG's viewBox to match the layer's pixel dimensions.
     * After this, 1 viewBox unit = 1 device pixel, so arrow geometry
     * (curves, arrowheads, wobble) is NOT distorted by aspect-ratio
     * stretching. Returns the layer rect for callers that need the
     * pixel dimensions to convert tile positions.
     */
    function updateViewBox() {
        const layer = document.querySelector('.tile-layer');
        if (!layer || !svg) return null;
        const r = layer.getBoundingClientRect();
        if (r.width === 0 || r.height === 0) return null;
        svg.setAttribute('viewBox', `0 0 ${r.width} ${r.height}`);
        return r;
    }

    function drawAllArrows() {
        if (!ensureSvg()) return;
        if (!window.tilesData || !window.positions) return;
        const layerRect = updateViewBox();
        if (!layerRect) return;
        clearArrows();

        // Convert tile percentage positions to pixel coords.
        const toPx = (pos) => ({
            x: (pos.left / 100) * layerRect.width,
            y: (pos.top  / 100) * layerRect.height,
        });

        Object.entries(window.tilesData).forEach(([parent, children]) => {
            const pPos = window.positions[parent];
            if (!pPos) return;
            const pPx = toPx(pPos);
            children.forEach((child) => {
                const cPos = window.positions[child];
                if (!cPos) return;
                const cPx = toPx(cPos);
                const seed = hash(parent + '|' + child);
                const arrow = makeArrow(cPx.x, cPx.y, pPx.x, pPx.y, seed);
                if (arrow) arrowsGroup.appendChild(arrow);
            });
        });
    }

    function updateOffset(centerTitle) {
        if (!arrowsGroup || !window.positions) return;
        const centerPos = window.positions[centerTitle];
        if (!centerPos) return;
        const layer = document.querySelector('.tile-layer');
        if (!layer) return;
        const layerRect = layer.getBoundingClientRect();
        // Tile centering uses (50% - centerLeft%, 52% - centerTop%) of
        // layer. Same offset in pixels.
        const offsetX = ((50 - centerPos.left) / 100) * layerRect.width;
        const offsetY = ((52 - centerPos.top)  / 100) * layerRect.height;
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
        const hash = decodeURIComponent(window.location.hash.slice(1));
        const center = (hash && window.positions && window.positions[hash])
            ? hash
            : 'Home';
        updateOffset(center);
    };

    // Recompute on viewport resize. Arrow positions are in pixel
    // coords matching the layer's current dimensions, so a resize
    // requires re-running the whole pipeline. Debounced so we don't
    // recompute on every resize tick during a continuous drag.
    let resizeTimer = null;
    window.addEventListener('resize', () => {
        if (resizeTimer) clearTimeout(resizeTimer);
        resizeTimer = setTimeout(() => {
            if (window.redrawChalkArrows) window.redrawChalkArrows();
        }, 120);
    });
})();
