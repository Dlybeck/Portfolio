/**
 * Declarative Theme Engine.
 *
 * The engine knows stable Portfolio slots and behaviors. It deliberately has
 * no theme names, palettes, silhouettes, or theme-specific renderers. Every
 * installed visual comes from a server-validated Theme Pack payload.
 */
(function () {
    "use strict";

    const SVG_NS = "http://www.w3.org/2000/svg";
    const packNode = document.querySelector("#active-theme-pack");
    const selector = document.querySelector("[data-theme-selector]");
    const fallbackId = selector?.options[0]?.value || "";
    const packCache = new Map();
    let activationSequence = 0;

    function parseInitialPack() {
        if (!packNode) return null;
        try {
            const pack = JSON.parse(packNode.textContent);
            if (!pack || typeof pack.id !== "string") return null;
            packCache.set(pack.id, pack);
            return pack;
        } catch (error) {
            console.error("Theme Pack payload could not be parsed", error);
            return null;
        }
    }

    const initialPack = parseInitialPack();
    const availableIds = new Set(
        [...(selector?.options || [])].map((option) => option.value)
    );
    const canonicalArrowConfig = { ...(window.chalkArrowsConfig || {}) };
    const state = {
        current: initialPack?.id || fallbackId,
        pack: initialPack,
    };

    function allTitles() {
        return Object.keys(window.tileInfo || {});
    }

    function packHasCompleteTiles(pack) {
        const assignments = pack?.tiles?.assignments;
        if (!assignments) return true;
        const titles = allTitles();
        return titles.length > 0
            && titles.every((title) => {
                const assignment = assignments[title];
                return assignment
                    && typeof assignment.baseSvg === "string"
                    && typeof assignment.expandedSvg === "string";
            });
    }

    async function loadPack(id) {
        if (!availableIds.has(id)) throw new Error(`Unknown Theme Pack: ${id}`);
        if (packCache.has(id)) return packCache.get(id);
        const response = await fetch(`/_theme-packs/${encodeURIComponent(id)}.json`, {
            headers: { Accept: "application/json" },
            credentials: "same-origin",
        });
        if (!response.ok) throw new Error(`Theme Pack ${id} was rejected`);
        const pack = await response.json();
        if (pack.id !== id || !packHasCompleteTiles(pack)) {
            throw new Error(`Theme Pack ${id} is incomplete`);
        }
        packCache.set(id, pack);
        return pack;
    }

    function namespaceSvgIds(svg, prefix) {
        const renamed = new Map();
        svg.querySelectorAll("[id]").forEach((element) => {
            const oldId = element.id;
            const newId = `${prefix}-${oldId}`;
            renamed.set(oldId, newId);
            element.id = newId;
        });
        const referenceAttributes = ["href", "mask", "clip-path", "fill", "stroke"];
        svg.querySelectorAll("*").forEach((element) => {
            referenceAttributes.forEach((name) => {
                const value = element.getAttribute(name);
                if (!value) return;
                if (value.startsWith("#") && renamed.has(value.slice(1))) {
                    element.setAttribute(name, `#${renamed.get(value.slice(1))}`);
                    return;
                }
                const match = value.match(/^url\(#(.+)\)$/);
                if (match && renamed.has(match[1])) {
                    element.setAttribute(name, `url(#${renamed.get(match[1])})`);
                }
            });
        });
    }

    function slug(value) {
        return value.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
    }

    function svgElement(pack, title, assignment, expanded) {
        const parser = new DOMParser();
        const source = expanded ? assignment.expandedSvg : assignment.baseSvg;
        const parsed = parser.parseFromString(source, "image/svg+xml");
        if (parsed.querySelector("parsererror") || parsed.documentElement.localName !== "svg") {
            throw new Error(`Theme Pack ${pack.id} supplied an invalid SVG for ${title}`);
        }
        const svg = document.importNode(parsed.documentElement, true);
        const identity = `${pack.id}-${slug(title)}`;
        const size = expanded ? "expanded" : "base";
        namespaceSvgIds(svg, `${identity}-${size}`);
        svg.classList.add("theme-object");
        svg.dataset.themeObject = pack.id;
        svg.dataset.themeIdentity = identity;
        svg.dataset.themeSize = size;
        Object.entries(assignment.factors || {}).forEach(([name, value]) => {
            svg.setAttribute(`data-variant-${name}`, String(value));
        });
        svg.dataset.themeVariant = Object.entries(assignment.factors || {})
            .sort(([left], [right]) => left.localeCompare(right))
            .map(([name, value]) => `${name}:${value}`)
            .join("|");
        const rotation = Number(assignment.rotation || 0);
        svg.style.setProperty("--object-rotation", `${rotation}deg`);
        return svg;
    }

    function cleanWorld() {
        document.querySelectorAll("[data-theme-object], [data-theme-ambient]")
            .forEach((node) => node.remove());
        document.querySelectorAll(".tile-container").forEach((tile) => {
            delete tile.dataset.themeIdentity;
            delete tile.dataset.themeShape;
            delete tile.dataset.themePalette;
        });
    }

    function addAmbient(pack) {
        if (!pack.tiles) return;
        const map = document.querySelector(".map");
        if (!map) return;
        const ambient = document.createElement("div");
        ambient.className = "theme-ambient";
        ambient.dataset.themeAmbient = pack.id;
        ambient.setAttribute("aria-hidden", "true");
        map.prepend(ambient);
    }

    function decorate(pack) {
        cleanWorld();
        const assignments = pack.tiles?.assignments;
        if (!assignments) return;
        if (!packHasCompleteTiles(pack)) {
            throw new Error(`Theme Pack ${pack.id} does not cover every Board location`);
        }
        document.querySelectorAll(".tile-container").forEach((tile) => {
            const title = tile.dataset.title;
            const assignment = assignments[title];
            const identity = `${pack.id}-${slug(title)}`;
            tile.dataset.themeIdentity = identity;
            tile.dataset.themeShape = String(assignment.factors?.silhouette ?? "");
            tile.dataset.themePalette = String(assignment.factors?.palette ?? "");
            tile.querySelector(".tile-base .paper-body")
                ?.prepend(svgElement(pack, title, assignment, false));
            tile.querySelector(".tile-expanded .paper-body")
                ?.prepend(svgElement(pack, title, assignment, true));
        });
        addAmbient(pack);
    }

    function styleRelationships(pack) {
        if (!window.chalkArrowsConfig) return;
        Object.assign(
            window.chalkArrowsConfig,
            canonicalArrowConfig,
            pack.connectors || {}
        );
        window.redrawChalkArrows?.();
    }

    function applyVariables(target, variables) {
        const style = target?.documentElement?.style || target?.style;
        if (!style) return;
        [...style].filter((name) => name.startsWith("--theme-pack-"))
            .forEach((name) => style.removeProperty(name));
        Object.entries(variables || {}).forEach(([name, value]) => {
            style.setProperty(`--theme-pack-${name}`, String(value));
        });
    }

    function styleDocument(doc, pack = state.pack) {
        if (!doc?.documentElement || !pack) return;
        doc.documentElement.dataset.boardTheme = pack.id;
        applyVariables(doc, pack.variables?.document);
    }

    function themedUrl(route, pack) {
        const parsed = new URL(route, window.location.origin);
        if (parsed.origin !== window.location.origin) return route;
        if (pack.id === fallbackId) parsed.searchParams.delete("theme");
        else parsed.searchParams.set("theme", pack.id);
        return `${parsed.pathname}${parsed.search}${parsed.hash}`;
    }

    window.portfolioUrlTransform = (route) => (
        state.pack ? themedUrl(route, state.pack) : route
    );

    async function activate(value, { syncUrl = true } = {}) {
        const requestedId = availableIds.has(value) ? value : fallbackId;
        const sequence = ++activationSequence;
        let pack;
        try {
            pack = await loadPack(requestedId);
            if (!packHasCompleteTiles(pack)) throw new Error("Theme Pack is incomplete");
        } catch (error) {
            console.error(error);
            pack = await loadPack(fallbackId);
        }
        if (sequence !== activationSequence) return state.current;

        cleanWorld();
        applyVariables(document, pack.variables?.board);
        document.documentElement.dataset.boardTheme = pack.id;
        decorate(pack);
        styleRelationships(pack);
        state.current = pack.id;
        state.pack = pack;
        if (selector) selector.value = pack.id;
        if (syncUrl) {
            const current = `${location.pathname}${location.search}${location.hash}`;
            history.replaceState(history.state, "", themedUrl(current, pack));
        }
        const iframeDoc = document.querySelector(".mini-window")?.contentDocument;
        if (iframeDoc?.body) styleDocument(iframeDoc, pack);
        return pack.id;
    }

    window.themeEngine = {
        activate,
        availableThemes: [...availableIds],
        currentPack: () => state.pack,
        styleDocument,
    };
    // Compatibility during the migration; application call sites use the
    // stable Theme Engine interface in the next checkpoint.
    window.themeLab = window.themeEngine;

    document.addEventListener("DOMContentLoaded", () => {
        selector?.addEventListener("change", (event) => {
            activate(event.target.value).catch(console.error);
        });
        document.addEventListener("keydown", (event) => {
            if (!selector || !event.altKey || event.code !== "KeyT") return;
            event.preventDefault();
            selector.focus();
        });
        activate(state.current, { syncUrl: false }).catch(console.error);
    });
}());
