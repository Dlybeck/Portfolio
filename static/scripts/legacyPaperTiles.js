/** Compatibility presenter for the pre-pack paper world. Not loaded by Theme Engine. */
(function () {
    "use strict";

    window.chalkArrowsConfig = {
        inset: null,
        insetTileUFactor: 9,
        insetFactor: 9,
        headStyle: "open",
        headPosition: "both",
        headLen: 15,
        headHalf: 12,
        strokeWidth: 5.2,
        opacity: 1,
        color: "#f3efe2",
        wobble: .14,
        lineCap: "round",
        dashPattern: "none",
        curveStyle: "varied",
        texture: "rough",
        textureColor: "#f3efe2",
        haloWidth: 1.55,
        haloOpacity: .16,
        variation: {
            strokeWidth: 0,
            wobble: 0,
            dash: 0,
            opacity: 0,
            markerScale: 0,
        },
    };

    const STICKY_COLORS = [
        "sticky-yellow", "sticky-pink", "sticky-blue", "sticky-green", "sticky-orange",
    ];
    const STICKY_FOLDS = [
        "sticky-fold-br", "sticky-fold-tr", "sticky-fold-bl", "sticky-fold-tl",
        "sticky-fold-big-br", "sticky-fold-big-bl", "sticky-fold-big-tl",
        "sticky-fold-flat",
    ];
    const SCRAP_VARIANTS = [
        "scrap-ruled", "scrap-graph", "scrap-plain", "scrap-kraft", "scrap-index",
        "scrap-legal", "scrap-dotgrid", "scrap-manila", "scrap-receipt", "scrap-napkin",
    ];
    const SCRAP_SHAPES = [
        "shape-rect", "shape-rect", "shape-rect", "shape-rect",
        "shape-torn-bottom", "shape-torn-top", "shape-torn-both",
        "shape-corner-bite", "shape-ripped-side",
    ];
    const TILE_FONTS = [
        "var(--font-hand-casual)", "var(--font-hand-neat)", "var(--font-hand-thin)",
    ];
    const SCRAP_INKS = ["var(--ink-blue)", "var(--ink-black)", "var(--ink-pencil)"];
    const STICKY_INKS = ["var(--ink-black)", "var(--ink-blue)", "var(--ink-red)"];
    const UNDERLINE_MASKS = [
        "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7'><path d='M2,4 Q15,1 28,4 Q40,7 55,3 Q70,1 98,3' stroke='white' stroke-width='2.2' fill='none'/></svg>\")",
        "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7'><path d='M3,3 Q30,2 50,3.5 T96,3 M5,5.2 Q35,4 94,5' stroke='white' stroke-width='1.6' fill='none'/></svg>\")",
        "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7'><path d='M1,4 C12,1 22,6 32,4 S52,1 64,4 S84,7 99,3.5' stroke='white' stroke-width='2.1' fill='none'/></svg>\")",
        "url(\"data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 7'><path d='M2,4.5 Q35,2 70,4 Q85,5 99,2' stroke='white' stroke-width='2.2' fill='none'/></svg>\")",
    ];

    function pick(values, value) {
        return values[value % values.length];
    }

    function rehash(value) {
        let mixed = (value ^ (value >>> 16)) * 0x85ebca6b >>> 0;
        mixed = (mixed ^ (mixed >>> 13)) * 0xc2b2ae35 >>> 0;
        return (mixed ^ (mixed >>> 16)) >>> 0;
    }

    function stableHash(value) {
        let hash = 2166136261;
        for (let index = 0; index < value.length; index += 1) {
            hash ^= value.charCodeAt(index);
            hash = Math.imul(hash, 16777619);
        }
        return Math.abs(hash | 0);
    }

    function paperType(title) {
        return title === "Home" || window.tilesData.hasOwnProperty(title)
            ? "sticky"
            : "scrap";
    }

    function styleSeed(title) {
        const hash = stableHash(title);
        return {
            rot: `${((hash % 1000) / 100 - 5).toFixed(2)}deg`,
            rotExpanded: `${((((hash / 7) | 0) % 1000) / 125 - 4).toFixed(2)}deg`,
            jitterX: `${((((hash / 53) | 0) % 1000) / 125 - 4).toFixed(2)}px`,
            jitterY: `${((((hash / 211) | 0) % 1000) / 125 - 4).toFixed(2)}px`,
            tapeAngle: `${((((hash / 1031) | 0) % 1000) / 62.5 - 8).toFixed(2)}deg`,
            colorIdx: hash,
            variantIdx: (hash / 7) | 0,
            fontIdx: (hash / 53) | 0,
            inkIdx: (hash / 211) | 0,
            expandedVariantIdx: (hash / 3779) | 0,
            shapeIdx: (hash / 19937) | 0,
            expandedShapeIdx: (hash / 39119) | 0,
        };
    }

    function decorateContainer(tile, title) {
        const type = paperType(title);
        const seed = styleSeed(title);
        tile.classList.add(type);
        if (type === "sticky") {
            tile.classList.add(pick(STICKY_COLORS, seed.colorIdx));
            tile.classList.add(pick(STICKY_FOLDS, rehash(stableHash(`${title}|fold`))));
            const lineSeed = rehash(stableHash(title));
            tile.style.setProperty("--title-underline-mask", pick(UNDERLINE_MASKS, lineSeed));
            tile.style.setProperty("--title-underline-rot", `${(lineSeed % 401) / 100 - 2}deg`);
            tile.style.setProperty("--title-underline-flip", lineSeed % 2 ? -1 : 1);
        } else {
            tile.classList.add(pick(SCRAP_VARIANTS, seed.variantIdx));
            tile.classList.add(pick(SCRAP_SHAPES, seed.shapeIdx));
            tile.classList.add("has-tape");
        }
        const inks = type === "sticky" ? STICKY_INKS : SCRAP_INKS;
        tile.style.setProperty("--rot", seed.rot);
        tile.style.setProperty("--rot-expanded", seed.rotExpanded);
        tile.style.setProperty("--jitter-x", seed.jitterX);
        tile.style.setProperty("--jitter-y", seed.jitterY);
        tile.style.setProperty("--tape-angle", seed.tapeAngle);
        tile.style.setProperty("--tile-font", pick(TILE_FONTS, seed.fontIdx));
        tile.style.setProperty("--ink-color", pick(inks, seed.inkIdx));
        return { seed, type };
    }

    function decorateExpanded(expanded, state) {
        const { seed, type } = state;
        if (type === "sticky") {
            const base = seed.colorIdx % STICKY_COLORS.length;
            let cover = (seed.expandedVariantIdx + 2) % STICKY_COLORS.length;
            if (cover === base) cover = (cover + 1) % STICKY_COLORS.length;
            expanded.classList.add(STICKY_COLORS[cover]);
            return;
        }
        const base = seed.variantIdx % SCRAP_VARIANTS.length;
        let cover = (seed.expandedVariantIdx + 2) % SCRAP_VARIANTS.length;
        if (cover === base) cover = (cover + 1) % SCRAP_VARIANTS.length;
        expanded.classList.add(SCRAP_VARIANTS[cover]);
        expanded.classList.add(pick(SCRAP_SHAPES, seed.expandedShapeIdx));
        expanded.classList.add("has-tape");
    }

    function decorateAction(link, title) {
        const hash = stableHash(title);
        const labels = ["open →", "→ open", "see ▸", "open it", "go →", "open this"];
        const inks = ["#a82828", "#1a3a6e", "#1b1b1b", "#5a3818", "#234a3e"];
        const fonts = [
            "'Architects Daughter', sans-serif", "'Patrick Hand', sans-serif",
            "'Gochi Hand', sans-serif", "'Kalam', sans-serif",
        ];
        const decorations = ["underline", "circled", "boxed"];
        link.textContent = pick(labels, (hash / 89) | 0);
        link.style.setProperty("--open-ink", pick(inks, (hash / 211) | 0));
        link.style.setProperty("--open-font", pick(fonts, (hash / 547) | 0));
        link.style.setProperty(
            "--open-rot",
            `${(((((hash / 4099) | 0) % 1000) / 1000) * 6 - 3).toFixed(2)}deg`,
        );
        link.classList.add(`deco-${pick(decorations, (hash / 1361) | 0)}`);
    }

    function addTape(parent, state) {
        if (state?.type === "sticky") return;
        const tape = document.createElement("div");
        tape.className = "tape";
        parent.appendChild(tape);
    }

    window.legacyPaperTiles = {
        addTape,
        decorateAction,
        decorateContainer,
        decorateExpanded,
    };
}());
