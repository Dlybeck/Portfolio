/**
 * Theme Laboratory
 *
 * One small public interface owns theme selection, URL continuity, cleanup,
 * and document styling. Individual worlds only supply deterministic SVG
 * renderers and ambient decoration; they never own navigation behavior.
 */
(function () {
    "use strict";

    const SVG_NS = "http://www.w3.org/2000/svg";
    const THEME_KEYS = ["canonical", "lily", "planets", "clouds", "islands"];
    const NON_CANONICAL = new Set(THEME_KEYS.slice(1));

    const palettes = {
        lily: [
            ["#4d8f61", "#7fbd73", "#d6efab"],
            ["#39795a", "#65aa69", "#bce28d"],
            ["#5a9857", "#8fc778", "#e2f3b4"],
            ["#387e69", "#69b179", "#c3e99e"],
            ["#54894c", "#94c66e", "#d9ec9e"],
        ],
        planets: [
            ["#cf6c58", "#f3b06f", "#ffd8a1"],
            ["#5976bd", "#8fb7e8", "#d4e9ff"],
            ["#946bb3", "#c49ed5", "#ead6ef"],
            ["#5e9b8a", "#8bcab1", "#d4efcf"],
            ["#c38b45", "#e6bd63", "#ffe7a2"],
        ],
        clouds: [
            ["#eaf5fb", "#bfd9e8", "#779bb3"],
            ["#fff8df", "#d9dfdf", "#8ba4b3"],
            ["#e8eef9", "#bbc9df", "#7185a5"],
            ["#f9fbfb", "#cadce3", "#7c9aa8"],
            ["#f5ebf3", "#d5c8dc", "#8f86a6"],
        ],
        islands: [
            ["#54a96b", "#e9d595", "#267c9b"],
            ["#3e9561", "#e8c982", "#3187a4"],
            ["#65aa58", "#f0dca0", "#256f91"],
            ["#478b57", "#dfc17b", "#2b7897"],
            ["#6d9f54", "#eed08c", "#2e83a0"],
        ],
    };

    const shapes = {
        lily: [
            "M24 82C24 35 69 17 112 31C154 45 176 81 153 119C129 157 69 151 37 119C26 108 22 96 24 82Z",
            "M30 69C46 27 98 20 139 42C178 64 174 111 141 136C107 160 54 140 31 104C23 92 24 80 30 69Z",
            "M19 91C16 48 49 23 91 24C139 25 178 55 174 98C170 140 116 153 71 140C39 131 22 115 19 91Z",
            "M35 46C68 19 123 24 157 58C187 88 165 131 124 145C80 160 32 131 23 91C19 72 24 56 35 46Z",
            "M20 76C32 35 75 15 118 33C162 51 184 92 155 126C127 160 70 147 37 119C21 105 15 91 20 76Z",
            "M33 55C62 20 116 20 151 50C188 81 170 127 129 145C87 163 35 137 22 99C16 82 20 68 33 55Z",
            "M21 101C11 59 43 27 84 21C127 15 174 38 180 80C187 123 143 153 98 151C57 149 29 132 21 101Z",
            "M37 42C73 17 127 27 158 64C187 99 157 139 115 148C72 158 29 126 23 84C20 66 25 51 37 42Z",
        ],
        planets: ["round", "moon", "oblate", "ringed", "cratered", "banded", "binary", "halo"],
        clouds: [
            "M24 112C5 91 23 64 49 69C48 43 80 27 101 48C119 20 164 39 159 72C191 75 194 118 165 126H50C39 126 30 121 24 112Z",
            "M18 102C8 79 31 59 53 66C61 37 100 33 116 55C138 35 172 55 166 82C191 91 182 126 155 128H45C31 127 23 117 18 102Z",
            "M28 119C2 103 13 70 42 70C46 43 79 29 100 48C122 23 164 37 162 72C188 77 195 111 171 127H52C42 127 34 124 28 119Z",
            "M21 108C4 83 27 58 53 67C58 35 100 27 121 53C145 40 174 61 165 87C188 101 174 130 151 130H46C34 129 27 121 21 108Z",
            "M17 110C0 88 18 62 45 65C55 39 91 38 107 58C128 28 171 43 169 78C192 86 187 120 161 127H43C31 126 23 120 17 110Z",
            "M30 126C4 114 8 81 35 75C35 48 70 31 94 49C112 22 154 34 158 66C186 68 198 104 176 122C170 127 162 130 153 130H49C42 130 35 129 30 126Z",
            "M23 116C4 97 17 68 44 68C51 42 85 35 105 54C127 28 168 45 166 79C192 85 190 122 161 129H48C38 128 29 124 23 116Z",
            "M19 100C14 77 37 58 59 68C72 38 111 38 128 63C150 49 180 69 170 95C190 112 173 137 149 134H47C31 132 21 120 19 100Z",
        ],
        islands: [
            "M18 90C28 53 62 39 89 45C112 24 160 39 174 76C185 108 150 135 119 132C89 151 38 132 18 102C15 98 15 94 18 90Z",
            "M25 68C45 35 82 39 102 51C127 36 164 53 177 83C188 110 155 136 125 130C96 151 51 137 25 105C16 93 17 80 25 68Z",
            "M20 95C19 65 48 43 77 47C98 27 140 34 158 61C184 70 188 107 163 122C140 146 101 137 82 133C51 144 22 124 20 95Z",
            "M30 52C55 31 88 41 102 55C129 37 168 55 176 88C182 116 148 137 121 128C95 150 47 135 24 106C10 89 16 65 30 52Z",
            "M18 82C34 52 67 39 91 51C109 30 150 36 168 63C191 88 174 120 146 128C124 147 86 137 70 132C37 139 15 113 18 82Z",
            "M27 63C51 39 79 46 97 55C121 31 159 44 174 73C194 101 164 132 137 131C109 151 70 133 55 132C30 126 12 91 27 63Z",
            "M19 102C9 73 36 49 64 50C84 28 125 33 142 52C173 50 190 82 178 108C165 136 128 136 106 130C76 151 33 133 19 102Z",
            "M34 47C60 31 89 44 104 57C128 39 165 54 174 82C188 112 153 140 123 130C96 148 51 134 27 105C9 84 17 58 34 47Z",
        ],
    };

    function hash(text) {
        return window.stableHash ? window.stableHash(text) : 0;
    }

    function channel(title, theme, salt, modulo) {
        return hash(`${theme}|${salt}|${title}`) % modulo;
    }

    function allTitles() {
        return Object.keys(window.tileInfo || {});
    }

    function adjacency() {
        const graph = new Map(allTitles().map((title) => [title, new Set()]));
        Object.entries(window.tilesData || {}).forEach(([parent, children]) => {
            children.forEach((child) => {
                graph.get(parent)?.add(child);
                graph.get(child)?.add(parent);
            });
            // A centered hub shows all of its children together. Treat that
            // visible neighborhood as a clique so its primary silhouettes
            // do not repeat even though the siblings are not graph edges.
            children.forEach((child, index) => {
                children.slice(index + 1).forEach((sibling) => {
                    graph.get(child)?.add(sibling);
                    graph.get(sibling)?.add(child);
                });
            });
        });
        return graph;
    }

    function profilesFor(theme) {
        const graph = adjacency();
        const assigned = new Map();
        allTitles().forEach((title) => {
            const grammar = themeAdapters[theme].grammar;
            const pool = grammar.silhouettes;
            const start = channel(title, theme, "shape", pool.length);
            const used = new Set(
                [...(graph.get(title) || [])]
                    .map((neighbor) => assigned.get(neighbor)?.shape)
                    .filter(Number.isInteger)
            );
            let shape = start;
            for (let offset = 0; offset < pool.length; offset += 1) {
                const candidate = (start + offset) % pool.length;
                if (!used.has(candidate)) { shape = candidate; break; }
            }
            assigned.set(title, {
                identity: `${theme}-${title.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`,
                shape,
                palette: channel(title, theme, "palette", grammar.palettes.length),
                detail: channel(title, theme, "detail", 6),
                accent: channel(title, theme, "accent", 5),
                rotation: channel(title, theme, "rotation", 17) - 8,
            });
        });
        return assigned;
    }

    function svgElement(theme, profile, expanded) {
        const svg = document.createElementNS(SVG_NS, "svg");
        svg.setAttribute("viewBox", "0 0 200 160");
        svg.setAttribute("preserveAspectRatio", "xMidYMid meet");
        svg.setAttribute("aria-hidden", "true");
        svg.setAttribute("focusable", "false");
        svg.classList.add("theme-object", `theme-object-${theme}`);
        svg.dataset.themeObject = theme;
        svg.dataset.themeIdentity = profile.identity;
        svg.dataset.themeShape = String(profile.shape);
        svg.dataset.themeDetail = String(profile.detail);
        svg.dataset.themeSize = expanded ? "expanded" : "base";
        svg.style.setProperty("--object-rotation", `${profile.rotation}deg`);
        svg.innerHTML = themeAdapters[theme].render(profile, expanded);
        return svg;
    }

    const renderers = {
        lily(profile, expanded) {
            const grammar = themeAdapters.lily.grammar;
            const [dark, mid, light] = grammar.palettes[profile.palette];
            const padPath = grammar.silhouettes[profile.shape];
            const maskId = `${profile.identity}-${expanded ? "expanded" : "base"}-mask`;
            const flower = profile.accent < 2
                ? `<g class="theme-detail theme-detail-accent" transform="translate(${128 + profile.detail * 3} ${62 + profile.accent * 8})"><circle r="13" fill="#f5d7df"/><circle r="8" fill="#fff2f3"/><circle r="3.5" fill="#e6ad57"/></g>`
                : "";
            const veins = expanded
                ? `<path class="theme-detail" d="M95 88L45 53M95 88L48 116M95 88L126 40M95 88L151 101" stroke="${light}" stroke-width="3" fill="none" stroke-linecap="round"/>`
                : `<path class="theme-detail" d="M95 88L47 55M95 88L145 100" stroke="${light}" stroke-width="2.4" fill="none" stroke-linecap="round"/>`;
            const notchAngle = profile.shape * 45 + profile.detail * 7;
            return `<defs><mask id="${maskId}" maskUnits="userSpaceOnUse" x="0" y="0" width="200" height="160"><rect width="200" height="160" fill="white"/><path d="M92 88L194 65L194 92Z" fill="black" transform="rotate(${notchAngle} 95 88)"/></mask></defs><g mask="url(#${maskId})"><path d="${padPath}" fill="${mid}" stroke="${dark}" stroke-width="5"/>${veins}</g>${flower}`;
        },
        planets(profile, expanded) {
            const [dark, mid, light] = themeAdapters.planets.grammar.palettes[profile.palette];
            const radiusX = 52 + (profile.shape % 3) * 5;
            const radiusY = 51 - (profile.shape % 2) * 4;
            const ring = profile.shape % 3 === 0
                ? `<ellipse cx="100" cy="83" rx="82" ry="23" fill="none" stroke="${light}" stroke-width="8" transform="rotate(${profile.rotation} 100 83)"/>`
                : "";
            const satellite = profile.accent < 3
                ? `<circle cx="${155 + profile.accent * 5}" cy="${38 + profile.detail * 3}" r="${6 + profile.accent}" fill="${light}" stroke="${dark}" stroke-width="3"/>`
                : "";
            const detail = expanded
                ? `<path class="theme-detail" d="M58 67C78 77 115 78 144 62M52 96C78 88 122 105 148 94" fill="none" stroke="${light}" stroke-width="8" stroke-linecap="round"/><circle class="theme-detail" cx="78" cy="57" r="8" fill="${dark}" opacity=".3"/><circle class="theme-detail" cx="121" cy="111" r="10" fill="${dark}" opacity=".24"/>`
                : `<path class="theme-detail" d="M55 86C83 74 121 98 148 80" fill="none" stroke="${light}" stroke-width="7" stroke-linecap="round"/>`;
            const halo = profile.shape > 5
                ? `<ellipse cx="100" cy="83" rx="${radiusX + 10}" ry="${radiusY + 10}" fill="none" stroke="${light}" stroke-width="5" opacity=".42"/>`
                : "";
            return `${halo}${ring}<ellipse cx="100" cy="83" rx="${radiusX}" ry="${radiusY}" fill="${mid}" stroke="${dark}" stroke-width="5"/>${detail}${satellite}`;
        },
        clouds(profile, expanded) {
            const grammar = themeAdapters.clouds.grammar;
            const [light, shade, dark] = grammar.palettes[profile.palette];
            const density = profile.detail % 3;
            const underside = profile.detail;
            const wisp = profile.accent;
            const undersideLift = underside % 3;
            const undersideOpacity = 0.7 + (underside % 2) * 0.16;
            const densityPuffs = [
                "",
                `<circle class="theme-detail" cx="${54 + profile.accent * 4}" cy="${73 - undersideLift * 3}" r="${15 + undersideLift}" fill="${light}"/>`,
                `<circle class="theme-detail" cx="${50 + profile.accent * 3}" cy="${73 - undersideLift * 2}" r="${14 + undersideLift}" fill="${light}"/><circle class="theme-detail" cx="${139 - profile.accent * 2}" cy="${69 + undersideLift}" r="${17 - undersideLift}" fill="${light}"/>`,
            ][density];
            const wisps = [
                `<path class="theme-detail" d="M157 88C181 84 187 74 175 68" fill="none" stroke="${dark}" stroke-width="3" stroke-linecap="round" opacity=".55"/>`,
                `<path class="theme-detail" d="M43 91C18 88 12 77 24 69" fill="none" stroke="${dark}" stroke-width="3" stroke-linecap="round" opacity=".5"/>`,
                `<path class="theme-detail" d="M158 96C184 99 191 90 182 82M153 107C172 112 181 108 181 100" fill="none" stroke="${dark}" stroke-width="3" stroke-linecap="round" opacity=".48"/>`,
                `<path class="theme-detail" d="M45 100C20 105 11 96 18 86M49 111C30 119 20 114 20 106" fill="none" stroke="${dark}" stroke-width="3" stroke-linecap="round" opacity=".48"/>`,
                `<path class="theme-detail" d="M158 91C180 85 190 74 181 66M44 104C22 111 13 103 19 94" fill="none" stroke="${dark}" stroke-width="3" stroke-linecap="round" opacity=".5"/>`,
            ][wisp];
            const expandedWisps = expanded
                ? `<path class="theme-detail" d="M63 143C57 149 52 151 45 151M103 144C96 151 89 153 82 152M141 140C136 146 130 148 123 147" fill="none" stroke="${dark}" stroke-width="3" stroke-linecap="round" opacity=".42"/>`
                : "";
            const shadowPath = expanded
                ? `M42 ${110 - undersideLift}C70 ${124 + undersideLift} 128 ${129 - undersideLift} 165 ${104 + undersideLift}C156 130 129 139 88 136C61 135 45 126 42 ${110 - undersideLift}Z`
                : `M43 ${111 - undersideLift}C78 ${124 + undersideLift} 130 ${125 - undersideLift} 164 ${104 + undersideLift}C153 128 111 136 75 130C57 127 46 120 43 ${111 - undersideLift}Z`;
            return `<g data-cloud-grammar="" data-cloud-density="${density}" data-cloud-underside="${underside}" data-cloud-wisp="${wisp}"><path d="${grammar.silhouettes[profile.shape]}" fill="${light}" stroke="${dark}" stroke-width="5"/>${densityPuffs}<path class="theme-detail" d="${shadowPath}" fill="${shade}" opacity="${undersideOpacity}"/>${wisps}${expandedWisps}</g>`;
        },
        islands(profile, expanded) {
            const grammar = themeAdapters.islands.grammar;
            const [land, sand, water] = grammar.palettes[profile.palette];
            const path = grammar.silhouettes[profile.shape];
            const innerScale = 0.82 + (profile.detail % 3) * 0.02;
            const islets = profile.accent < 3
                ? `<ellipse cx="${166 - profile.accent * 8}" cy="${124 + profile.accent * 4}" rx="${8 + profile.accent}" ry="${5 + profile.accent}" fill="${sand}" stroke="${water}" stroke-width="3"/>`
                : "";
            const terrain = expanded
                ? `<path class="theme-detail" d="M72 102L92 69L110 98L126 78L145 108" fill="none" stroke="#2d724d" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/><path class="theme-detail" d="M46 112C73 120 127 124 158 108" fill="none" stroke="#b1c66b" stroke-width="5" stroke-linecap="round"/>`
                : `<path class="theme-detail" d="M66 108C92 91 122 96 145 109" fill="none" stroke="#b1c66b" stroke-width="5" stroke-linecap="round"/>`;
            return `<path d="${path}" fill="${sand}" stroke="${water}" stroke-width="6"/><path d="${path}" fill="${land}" transform="translate(${100 * (1 - innerScale)} ${80 * (1 - innerScale)}) scale(${innerScale})"/>${terrain}${islets}`;
        },
    };

    function cleanWorld() {
        document.querySelectorAll("[data-theme-object], [data-theme-ambient]").forEach((node) => node.remove());
        document.querySelectorAll(".tile-container").forEach((tile) => {
            delete tile.dataset.themeIdentity;
            delete tile.dataset.themeShape;
            delete tile.dataset.themePalette;
        });
    }

    function addAmbient(theme) {
        const map = document.querySelector(".map");
        if (!map || !NON_CANONICAL.has(theme)) return;
        const ambient = document.createElement("div");
        ambient.className = `theme-ambient theme-ambient-${theme}`;
        ambient.dataset.themeAmbient = theme;
        ambient.setAttribute("aria-hidden", "true");
        map.prepend(ambient);
    }

    const canonicalArrowConfig = { ...(window.chalkArrowsConfig || {}) };
    const themeAdapters = {
        canonical: { key: "canonical", render: null, arrows: null },
        lily: {
            key: "lily",
            grammar: { palettes: palettes.lily, silhouettes: shapes.lily },
            render: renderers.lily,
            arrows: { color: "#d7efbd", strokeWidth: 3.6, opacity: 0.78, headStyle: "none", wobble: 0.1 },
        },
        planets: {
            key: "planets",
            grammar: { palettes: palettes.planets, silhouettes: shapes.planets },
            render: renderers.planets,
            arrows: { color: "#b7d9ff", strokeWidth: 2.4, opacity: 0.74, headStyle: "none", wobble: 0.035 },
        },
        clouds: {
            key: "clouds",
            grammar: { palettes: palettes.clouds, silhouettes: shapes.clouds },
            render: renderers.clouds,
            arrows: { color: "#f7fbff", strokeWidth: 3.2, opacity: 0.68, headStyle: "none", wobble: 0.18 },
        },
        islands: {
            key: "islands",
            grammar: { palettes: palettes.islands, silhouettes: shapes.islands },
            render: renderers.islands,
            arrows: { color: "#bce8e2", strokeWidth: 3.5, opacity: 0.72, headStyle: "none", wobble: 0.11 },
        },
    };

    function styleRelationships(theme) {
        if (!window.chalkArrowsConfig) return;
        Object.assign(
            window.chalkArrowsConfig,
            canonicalArrowConfig,
            themeAdapters[theme]?.arrows || {}
        );
        window.redrawChalkArrows?.();
    }

    function decorate(theme) {
        cleanWorld();
        if (!themeAdapters[theme]?.render) return;
        const profiles = profilesFor(theme);
        document.querySelectorAll(".tile-container").forEach((tile) => {
            const profile = profiles.get(tile.dataset.title);
            if (!profile) return;
            tile.dataset.themeIdentity = profile.identity;
            tile.dataset.themeShape = String(profile.shape);
            tile.dataset.themePalette = String(profile.palette);
            const baseBody = tile.querySelector(".tile-base .paper-body");
            const expandedBody = tile.querySelector(".tile-expanded .paper-body");
            baseBody?.prepend(svgElement(theme, profile, false));
            expandedBody?.prepend(svgElement(theme, profile, true));
        });
        addAmbient(theme);
    }

    function normalizedTheme(value) {
        return THEME_KEYS.includes(value) ? value : "canonical";
    }

    function themedUrl(route, theme) {
        const parsed = new URL(route, window.location.origin);
        if (parsed.origin !== window.location.origin) return route;
        if (theme === "canonical") parsed.searchParams.delete("theme");
        else parsed.searchParams.set("theme", theme);
        return `${parsed.pathname}${parsed.search}${parsed.hash}`;
    }

    function installNavigation(themeState) {
        window.portfolioUrlTransform = (route) => themedUrl(route, themeState.current);
    }

    function styleDocument(doc, theme) {
        doc.querySelector("[data-theme-runtime]")?.remove();
        doc.documentElement.dataset.boardTheme = theme;
        if (!NON_CANONICAL.has(theme)) return;
        const style = doc.createElement("style");
        style.dataset.themeRuntime = theme;
        style.textContent = `html,body{background:var(--document-page)!important;color:var(--document-ink)!important} header{background:var(--document-header)!important}.section{background:var(--document-panel)!important;border-color:var(--document-border)!important}`;
        doc.head.appendChild(style);
    }

    const themeState = {
        current: normalizedTheme(document.documentElement.dataset.boardTheme),
    };

    installNavigation(themeState);

    window.themeLab = {
        availableThemes: [...THEME_KEYS],
        activate(value, { syncUrl = true } = {}) {
            const theme = normalizedTheme(value);
            themeState.current = theme;
            document.documentElement.dataset.boardTheme = theme;
            const selector = document.querySelector("[data-theme-selector]");
            if (selector) selector.value = theme;
            decorate(theme);
            styleRelationships(theme);
            if (syncUrl) {
                const current = `${window.location.pathname}${window.location.search}${window.location.hash}`;
                const target = themedUrl(current, theme);
                window.history.replaceState(window.history.state, "", target);
            }
            const iframeDoc = document.querySelector(".mini-window")?.contentDocument;
            if (iframeDoc?.body) styleDocument(iframeDoc, theme);
            return theme;
        },
        styleDocument(doc) { styleDocument(doc, themeState.current); },
    };

    document.addEventListener("DOMContentLoaded", () => {
        const selector = document.querySelector("[data-theme-selector]");
        selector?.addEventListener("change", (event) => {
            window.themeLab.activate(event.target.value);
        });
        document.addEventListener("keydown", (event) => {
            if (!selector || !event.altKey || event.code !== "KeyT") return;
            event.preventDefault();
            selector.focus();
        });
        window.themeLab.activate(themeState.current, { syncUrl: false });
    });
}());
