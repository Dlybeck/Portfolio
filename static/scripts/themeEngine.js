/**
 * Declarative Theme Engine.
 *
 * The engine knows stable Portfolio slots and behaviors. It deliberately has
 * no installed-world names or theme-specific drawing functions. Every
 * installed visual comes from a server-validated Theme Pack payload.
 */
(function () {
    "use strict";

    const SVG_NS = "http://www.w3.org/2000/svg";
    const packNode = document.querySelector("#active-theme-pack");
    const catalogNode = document.querySelector("#theme-pack-catalog");
    const selector = document.querySelector("[data-theme-selector]");
    let catalog = [];
    try { catalog = JSON.parse(catalogNode?.textContent || "[]"); } catch (_) {}
    const fallbackId = catalog[0]?.key || "";
    const packCache = new Map();
    let activationSequence = 0;
    let fontsReady = !document.fonts;

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
        catalog.map((pack) => pack.key)
    );
    const relationshipDefaults = { ...(window.chalkArrowsConfig || {}) };
    const state = {
        current: initialPack?.id || fallbackId,
        pack: initialPack,
        pinned: new URLSearchParams(location.search).has("theme"),
    };

    function allTitles() {
        return Object.keys(window.tileInfo || {});
    }

    function packIsComplete(pack) {
        const assignments = pack?.tiles?.assignments;
        if (
            !assignments
            || !pack?.variables?.board
            || !pack?.variables?.document
            || !pack?.connectors
            || !Array.isArray(pack?.backgroundLayers)
        ) return false;
        const titles = allTitles();
        return titles.length > 0
            && titles.every((title) => {
                const assignment = assignments[title];
                return assignment
                    && typeof assignment.baseSvg === "string"
                    && typeof assignment.expandedSvg === "string"
                    && assignment.transforms?.base
                    && assignment.transforms?.expanded
                    && assignment.motion;
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
        if (pack.id !== id || !packIsComplete(pack)) {
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
        const referenceAttributes = [
            "href", "mask", "clip-path", "fill", "stroke", "filter"
        ];
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
        const transform = expanded
            ? assignment.transforms?.expanded
            : assignment.transforms?.base;
        const rotation = Number(transform?.rotationDegrees || 0);
        svg.style.setProperty("--theme-rotation-degrees", `${rotation}deg`);
        return svg;
    }

    function applyContentArea(body, svg) {
        const marker = svg.querySelector("[data-theme-content-area]");
        const viewBox = (svg.getAttribute("viewBox") || "")
            .trim().split(/\s+/).map(Number);
        if (!marker || viewBox.length !== 4 || viewBox.some(Number.isNaN)) {
            throw new Error("Compiled tile SVG is missing a valid content-safe area");
        }
        const [viewX, viewY, viewWidth, viewHeight] = viewBox;
        const x = Number(marker.getAttribute("x"));
        const y = Number(marker.getAttribute("y"));
        const width = Number(marker.getAttribute("width"));
        const height = Number(marker.getAttribute("height"));
        if (![x, y, width, height].every(Number.isFinite) || width <= 0 || height <= 0) {
            throw new Error("Compiled tile content-safe area is invalid");
        }
        body.dataset.themeSafeTop = String((y - viewY) / viewHeight);
        body.dataset.themeSafeRight = String(
            (viewX + viewWidth - x - width) / viewWidth
        );
        body.dataset.themeSafeBottom = String(
            (viewY + viewHeight - y - height) / viewHeight
        );
        body.dataset.themeSafeLeft = String((x - viewX) / viewWidth);
        body.dataset.themeContentArea = marker.dataset.themeContentArea || "content";
    }

    function sizeContentArea(body) {
        body.style.setProperty(
            "--theme-safe-top",
            `${Number(body.dataset.themeSafeTop) * body.clientHeight}px`
        );
        body.style.setProperty(
            "--theme-safe-right",
            `${Number(body.dataset.themeSafeRight) * body.clientWidth}px`
        );
        body.style.setProperty(
            "--theme-safe-bottom",
            `${Number(body.dataset.themeSafeBottom) * body.clientHeight}px`
        );
        body.style.setProperty(
            "--theme-safe-left",
            `${Number(body.dataset.themeSafeLeft) * body.clientWidth}px`
        );
    }

    function fitText(element, minimumPixels) {
        if (!element) return true;
        element.style.removeProperty("font-size");
        let size = Number.parseFloat(getComputedStyle(element).fontSize);
        const body = element.closest(".paper-body");
        const fitsSafeArea = () => {
            if (!body) return true;
            const style = getComputedStyle(body);
            const availableWidth = body.clientWidth
                - Number.parseFloat(style.paddingLeft)
                - Number.parseFloat(style.paddingRight);
            const availableHeight = body.clientHeight
                - Number.parseFloat(style.paddingTop)
                - Number.parseFloat(style.paddingBottom);
            return element.offsetWidth <= availableWidth + 1
                && element.offsetHeight <= availableHeight + 1;
        };
        while (
            size > minimumPixels
            && (!fitsSafeArea()
                || element.scrollWidth > element.clientWidth + 4
                || element.scrollHeight > element.clientHeight + 4)
        ) {
            size -= 0.5;
            element.style.fontSize = `${size}px`;
        }
        return fitsSafeArea()
            && element.scrollWidth <= element.clientWidth + 4
            && element.scrollHeight <= element.clientHeight + 4;
    }

    function fitExpandedContent(body) {
        const nodes = [
            body.querySelector(".expanded-title"),
            body.querySelector(".expanded-text"),
            body.querySelector(".expanded-open"),
        ].filter(Boolean);
        nodes.forEach((node) => node.style.removeProperty("font-size"));
        const initialSizes = nodes.map((node) => Number.parseFloat(
            getComputedStyle(node).fontSize
        ));
        const style = getComputedStyle(body);
        const safe = {
            left: Number.parseFloat(style.paddingLeft),
            top: Number.parseFloat(style.paddingTop),
            right: body.clientWidth - Number.parseFloat(style.paddingRight),
            bottom: body.clientHeight - Number.parseFloat(style.paddingBottom),
        };
        const fits = () => nodes.every((node) => (
            node.offsetLeft >= safe.left - 1
            && node.offsetTop >= safe.top - 1
            && node.offsetLeft + node.offsetWidth <= safe.right + 1
            && node.offsetTop + node.offsetHeight <= safe.bottom + 1
            && (!node.matches(".expanded-text")
                || (node.scrollWidth <= node.clientWidth + 4
                    && node.scrollHeight <= node.clientHeight + 4))
        ));
        for (let scale = 1; scale >= 0.3; scale -= 0.05) {
            nodes.forEach((node, index) => {
                const minimum = node.matches(".expanded-title")
                    ? 20
                    : (node.matches(".expanded-open") ? 14 : 13);
                node.style.fontSize = `${Math.max(minimum, initialSizes[index] * scale)}px`;
            });
            if (fits()) return true;
        }
        return fits();
    }

    function fitTileContent() {
        document.querySelectorAll(".tile-container[data-theme-identity]").forEach((tile) => {
            tile.querySelectorAll(".paper-body[data-theme-content-area]")
                .forEach(sizeContentArea);
            const baseFits = fitText(
                tile.querySelector(".tile-base .scrap-title"),
                11
            );
            const expandedBody = tile.querySelector(
                ".tile-expanded .paper-body[data-theme-content-area]"
            );
            const expandedFits = expandedBody
                ? fitExpandedContent(expandedBody)
                : true;
            tile.dataset.themeContentFit = fontsReady
                ? String(baseFits && expandedFits)
                : "pending";
        });
    }

    let fitFrame = null;
    function scheduleContentFit() {
        if (fitFrame !== null) cancelAnimationFrame(fitFrame);
        fitFrame = requestAnimationFrame(() => {
            fitFrame = requestAnimationFrame(() => {
                fitFrame = null;
                fitTileContent();
            });
        });
    }

    function cleanWorld() {
        document.querySelectorAll(
            "[data-theme-object], [data-theme-ambient], [data-theme-background]"
        )
            .forEach((node) => node.remove());
        document.querySelectorAll(".tile-container").forEach((tile) => {
            delete tile.dataset.themeIdentity;
            delete tile.dataset.themeShape;
            delete tile.dataset.themePalette;
            delete tile.dataset.themeContentFit;
            if (tile.dataset.preThemeRotation !== undefined) {
                tile.style.setProperty("--rot", tile.dataset.preThemeRotation);
                tile.style.setProperty(
                    "--rot-expanded",
                    tile.dataset.preThemeExpandedRotation
                );
            }
            tile.querySelectorAll(".paper-body").forEach((body) => {
                delete body.dataset.themeContentArea;
                delete body.dataset.themeSafeTop;
                delete body.dataset.themeSafeRight;
                delete body.dataset.themeSafeBottom;
                delete body.dataset.themeSafeLeft;
                ["top", "right", "bottom", "left"].forEach((edge) => {
                    body.style.removeProperty(`--theme-safe-${edge}`);
                });
            });
            tile.querySelectorAll(".scrap-title, .expanded-title, .expanded-text, .expanded-open")
                .forEach((element) => element.style.removeProperty("font-size"));
            [
                "--theme-detail-rotation", "--theme-motion-enter-duration",
                "--theme-motion-exit-duration", "--theme-motion-rotation-offset",
                "--theme-motion-offset-x", "--theme-motion-offset-y",
                "--theme-motion-scale-offset", "--theme-location-base-font",
                "--theme-location-expanded-title-font",
                "--theme-location-expanded-text-font", "--theme-location-ink",
                "--theme-location-base-letter-spacing",
                "--theme-location-expanded-width",
                "--theme-location-expanded-min-height",
                "--theme-location-phone-expanded-width",
                "--theme-location-phone-expanded-min-height",
            ].forEach((name) => tile.style.removeProperty(name));
        });
    }

    function positionBackgroundLayer(background, centerPosition) {
        const depth = Number(background.dataset.themeDepth);
        if (!Number.isFinite(depth) || !centerPosition) return;
        background.style.setProperty(
            "--theme-layer-shift-x", `${-centerPosition.left * depth}vw`
        );
        background.style.setProperty(
            "--theme-layer-shift-y", `${-centerPosition.top * depth}vh`
        );
    }

    function positionBackgroundLayers(centerPosition) {
        document.querySelectorAll("[data-theme-background]").forEach((background) => {
            positionBackgroundLayer(background, centerPosition);
        });
    }

    function addBackgrounds(pack) {
        const map = document.querySelector(".map");
        const tileLayer = map?.querySelector(".tile-layer");
        if (!map || !tileLayer) return;
        const currentPosition = window.positions?.[window.currentTileTitle || "Home"];
        (pack.backgroundLayers || []).forEach((layer, index) => {
            const parser = new DOMParser();
            const parsed = parser.parseFromString(layer.svg, "image/svg+xml");
            if (
                parsed.querySelector("parsererror")
                || parsed.documentElement.localName !== "svg"
            ) {
                throw new Error(`Theme Pack ${pack.id} supplied an invalid background SVG`);
            }
            const background = document.importNode(parsed.documentElement, true);
            namespaceSvgIds(background, `${pack.id}-background-${index}`);
            background.classList.add("theme-background");
            background.dataset.themeBackground = pack.id;
            background.dataset.themeLayer = String(index);
            background.dataset.themeDepth = String(layer.depth);
            background.setAttribute("aria-hidden", "true");
            background.setAttribute("focusable", "false");
            positionBackgroundLayer(background, currentPosition);
            map.insertBefore(background, tileLayer);
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
        if (!packIsComplete(pack)) {
            throw new Error(`Theme Pack ${pack.id} does not cover every Board location`);
        }
        document.querySelectorAll(".tile-container").forEach((tile) => {
            const title = tile.dataset.title;
            const assignment = assignments[title];
            const identity = `${pack.id}-${slug(title)}`;
            if (tile.dataset.preThemeRotation === undefined) {
                tile.dataset.preThemeRotation = tile.style.getPropertyValue("--rot");
                tile.dataset.preThemeExpandedRotation = tile.style.getPropertyValue(
                    "--rot-expanded"
                );
            }
            tile.dataset.themeIdentity = identity;
            tile.dataset.themeShape = String(assignment.factors?.silhouette ?? "");
            tile.dataset.themePalette = String(assignment.factors?.palette ?? "");
            const baseBody = tile.querySelector(".tile-base .paper-body");
            const expandedBody = tile.querySelector(".tile-expanded .paper-body");
            const baseSvg = svgElement(pack, title, assignment, false);
            const expandedSvg = svgElement(pack, title, assignment, true);
            const baseTransform = assignment.transforms.base;
            const expandedTransform = assignment.transforms.expanded;
            const motion = assignment.motion;
            tile.style.setProperty(
                "--rot", `${Number(baseTransform.rotationDegrees || 0)}deg`
            );
            tile.style.setProperty(
                "--rot-expanded",
                `${Number(expandedTransform.rotationDegrees || 0)}deg`
            );
            tile.style.setProperty(
                "--jitter-x", `${Number(baseTransform.offsetXPixels || 0)}px`
            );
            tile.style.setProperty(
                "--jitter-y", `${Number(baseTransform.offsetYPixels || 0)}px`
            );
            tile.style.setProperty(
                "--expanded-jitter-x",
                `${Number(expandedTransform.offsetXPixels || 0)}px`
            );
            tile.style.setProperty(
                "--expanded-jitter-y",
                `${Number(expandedTransform.offsetYPixels || 0)}px`
            );
            tile.style.setProperty(
                "--theme-detail-rotation",
                `${Number(assignment.transforms.detailRotationDegrees || 0)}deg`
            );
            const durationOffset = Number(motion.durationOffsetMilliseconds || 0);
            tile.style.setProperty(
                "--theme-motion-enter-duration",
                `calc(var(--theme-pack-cover-enter-duration) + ${durationOffset}ms)`
            );
            tile.style.setProperty(
                "--theme-motion-exit-duration",
                `calc(var(--theme-pack-cover-exit-duration) + ${Math.round(durationOffset * .7)}ms)`
            );
            tile.style.setProperty(
                "--theme-motion-rotation-offset",
                `${Number(motion.rotationOffsetDegrees || 0)}deg`
            );
            tile.style.setProperty(
                "--theme-motion-offset-x", `${Number(motion.offsetXPixels || 0)}px`
            );
            tile.style.setProperty(
                "--theme-motion-offset-y", `${Number(motion.offsetYPixels || 0)}px`
            );
            tile.style.setProperty(
                "--theme-motion-scale-offset", Number(motion.scaleOffset || 0)
            );
            if (assignment.typography) {
                tile.style.setProperty(
                    "--theme-location-base-font", assignment.typography.baseFontFamily
                );
                tile.style.setProperty(
                    "--theme-location-expanded-title-font",
                    assignment.typography.expandedTitleFontFamily
                );
                tile.style.setProperty(
                    "--theme-location-expanded-text-font",
                    assignment.typography.expandedTextFontFamily
                );
                tile.style.setProperty(
                    "--theme-location-ink", assignment.typography.inkColor
                );
                if (assignment.typography.baseLetterSpacing) {
                    tile.style.setProperty(
                        "--theme-location-base-letter-spacing",
                        assignment.typography.baseLetterSpacing
                    );
                }
            }
            if (assignment.layout) {
                tile.style.setProperty(
                    "--theme-location-expanded-width",
                    assignment.layout.expandedWidth
                );
                tile.style.setProperty(
                    "--theme-location-expanded-min-height",
                    assignment.layout.expandedMinHeight
                );
                tile.style.setProperty(
                    "--theme-location-phone-expanded-width",
                    assignment.layout.phoneExpandedWidth
                );
                tile.style.setProperty(
                    "--theme-location-phone-expanded-min-height",
                    assignment.layout.phoneExpandedMinHeight
                );
            }
            if (baseBody) {
                applyContentArea(baseBody, baseSvg);
                baseBody.prepend(baseSvg);
            }
            if (expandedBody) {
                applyContentArea(expandedBody, expandedSvg);
                expandedBody.prepend(expandedSvg);
            }
        });
        addBackgrounds(pack);
        addAmbient(pack);
        scheduleContentFit();
    }

    function styleRelationships(pack) {
        if (!window.chalkArrowsConfig) return;
        Object.assign(
            window.chalkArrowsConfig,
            relationshipDefaults,
            pack.connectors
        );
        window.redrawChalkArrows?.();
    }

    function applyVariables(target, variables) {
        const style = target?.documentElement?.style || target?.style;
        if (!style) return;
        Array.from(style).filter((name) => name.startsWith("--theme-pack-"))
            .forEach((name) => style.removeProperty(name));
        Object.entries(variables || {}).forEach(([name, value]) => {
            style.setProperty(`--theme-pack-${name}`, String(value));
        });
    }

    function styleDocument(doc, pack = state.pack) {
        if (!doc?.documentElement || !pack) return;
        doc.documentElement.dataset.boardTheme = pack.id;
        doc.documentElement.setAttribute("data-theme-pack-visual", "");
        applyVariables(doc, pack.variables.document);
    }

    function themedUrl(route, pack, includeTheme = state.pinned) {
        const parsed = new URL(route, window.location.origin);
        if (parsed.origin !== window.location.origin) return route;
        if (!includeTheme) parsed.searchParams.delete("theme");
        else parsed.searchParams.set("theme", pack.id);
        return `${parsed.pathname}${parsed.search}${parsed.hash}`;
    }

    window.portfolioUrlTransform = (route) => (
        state.pack ? themedUrl(route, state.pack) : route
    );
    window.portfolioDocumentUrlTransform = (route) => (
        state.pack ? themedUrl(route, state.pack, true) : route
    );

    async function activate(value, { syncUrl = true } = {}) {
        const requestedId = availableIds.has(value) ? value : fallbackId;
        const sequence = ++activationSequence;
        let pack;
        try {
            pack = await loadPack(requestedId);
            if (!packIsComplete(pack)) throw new Error("Theme Pack is incomplete");
        } catch (error) {
            console.error(error);
            pack = await loadPack(fallbackId);
        }
        if (sequence !== activationSequence) return state.current;

        if (syncUrl) state.pinned = true;

        cleanWorld();
        applyVariables(document, pack.variables.board);
        document.documentElement.dataset.boardTheme = pack.id;
        document.documentElement.dataset.themeFocusMotion =
            pack.variables.board["focus-motion"];
        document.documentElement.setAttribute("data-theme-pack-visual", "");
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
        positionBackgroundLayers,
        styleDocument,
    };
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
        window.addEventListener("resize", scheduleContentFit, { passive: true });
        document.fonts?.ready.then(() => {
            fontsReady = true;
            scheduleContentFit();
        });
    });
}());
