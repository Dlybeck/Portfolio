/**
 * PROTOTYPE — throwaway visual comparison.
 *
 * Five illustrated worlds on the real portfolio Board: the three currently
 * approved directions plus rebuilt Islands and Rain Puddles experiments.
 * Rejected experiments stay captured in the throwaway CSS but are removed
 * from the live comparison.
 * State intentionally lives only in the URL and the current page.
 */
(function () {
    const variants = [
        { key: 'lily', name: 'Lily Pond' },
        { key: 'constellation', name: 'Planets / Constellation' },
        { key: 'clouds', name: 'Cloudscape' },
        { key: 'islands2', name: 'Island Chain' },
        { key: 'rain', name: 'Rain Puddles — V2' },
    ];
    const keys = new Set(variants.map(({ key }) => key));

    function variantFromUrl() {
        const requested = new URLSearchParams(window.location.search).get('variant');
        return keys.has(requested) ? requested : variants[0].key;
    }

    let current = variantFromUrl();
    document.documentElement.dataset.prototypeTheme = current;

    function decoratedUrl(route) {
        const url = new URL(route, window.location.origin);
        url.searchParams.set('variant', current);
        return `${url.pathname}${url.search}${url.hash}`;
    }

    function applyToDocumentFrame(frame) {
        let frameDocument = null;
        try {
            frameDocument = frame && frame.contentDocument;
        } catch (_) {
            return;
        }
        if (frameDocument && frameDocument.documentElement) {
            frameDocument.documentElement.dataset.prototypeTheme = current;
        }
    }

    function updateSwitcher() {
        const label = document.querySelector('[data-prototype-variant-label]');
        const active = variants.find(({ key }) => key === current);
        if (label && active) label.textContent = active.name;
    }

    function updateWorldDecoration() {
        const map = document.querySelector('.map');
        if (!map) return;

        let decor = map.querySelector('.prototype-world-decor');
        if (!decor) {
            decor = document.createElement('div');
            decor.className = 'prototype-world-decor';
            decor.setAttribute('aria-hidden', 'true');
            map.insertBefore(decor, map.firstChild);
        }

        decor.innerHTML = Array.from({ length: 9 }, (_, index) => (
            `<i class="world-mark world-mark-${index + 1}"></i>`
        )).join('');
    }

    function decoratePuddles() {
        const paths = [
            'M8 120 C14 91 50 76 92 80 C123 51 181 52 214 75 C251 67 300 83 313 112 C309 139 273 151 231 145 C192 165 132 163 99 145 C57 154 17 144 8 120 Z',
            'M7 112 C21 81 64 77 101 86 C142 55 205 62 226 82 C269 76 304 92 314 121 C294 148 254 148 219 142 C178 166 116 154 91 143 C48 151 15 140 7 112 Z',
            'M6 124 C19 94 50 83 88 84 C117 59 169 55 207 77 C247 67 295 82 314 105 C318 132 280 149 240 147 C208 161 153 164 119 146 C73 157 23 149 6 124 Z',
        ];

        document.querySelectorAll('.paper-body').forEach((paper, index) => {
            if (paper.querySelector('.prototype-puddle')) return;
            const path = paths[index % paths.length];
            const clipId = `prototype-puddle-${index}`;
            paper.insertAdjacentHTML('afterbegin', `
                <svg class="prototype-puddle" viewBox="0 0 320 200" preserveAspectRatio="none" aria-hidden="true">
                    <defs>
                        <clipPath id="${clipId}"><path d="${path}"></path></clipPath>
                    </defs>
                    <path class="puddle-water" d="${path}"></path>
                    <g clip-path="url(#${clipId})">
                        <path class="puddle-sky" d="M-8 93 C73 68 139 77 211 63 C263 53 309 59 337 49"></path>
                        <path class="puddle-dark-reflection" d="M-11 140 C71 121 136 132 205 112 C255 98 307 105 336 92"></path>
                        <ellipse class="puddle-ripple" cx="76" cy="119" rx="31" ry="11"></ellipse>
                        <ellipse class="puddle-ripple puddle-ripple-small" cx="245" cy="95" rx="20" ry="7"></ellipse>
                        <ellipse class="puddle-ripple puddle-ripple-faint" cx="177" cy="142" rx="15" ry="5"></ellipse>
                    </g>
                </svg>
            `);
        });
    }

    function chooseVariant(nextKey) {
        if (!keys.has(nextKey)) nextKey = variants[0].key;
        current = nextKey;
        document.documentElement.dataset.prototypeTheme = current;
        updateWorldDecoration();

        const url = new URL(window.location.href);
        url.searchParams.set('variant', current);
        window.history.replaceState(window.history.state, '', url);

        applyToDocumentFrame(document.querySelector('.mini-window'));
        updateSwitcher();
    }

    function cycleVariant(direction) {
        const currentIndex = variants.findIndex(({ key }) => key === current);
        const nextIndex = (currentIndex + direction + variants.length) % variants.length;
        chooseVariant(variants[nextIndex].key);
    }

    function buildSwitcher() {
        const switcher = document.createElement('aside');
        switcher.className = 'prototype-theme-switcher';
        switcher.setAttribute('aria-label', 'Theme prototype switcher');
        switcher.innerHTML = `
            <span class="prototype-badge">prototype</span>
            <button type="button" data-prototype-previous aria-label="Previous world">←</button>
            <span class="prototype-variant" data-prototype-variant-label></span>
            <button type="button" data-prototype-next aria-label="Next world">→</button>
        `;
        document.body.appendChild(switcher);

        switcher.querySelector('[data-prototype-previous]').addEventListener(
            'click', () => cycleVariant(-1)
        );
        switcher.querySelector('[data-prototype-next]').addEventListener(
            'click', () => cycleVariant(1)
        );
        updateSwitcher();
    }

    function keepVariantInNavigation() {
        window.setDestinationUrl = function (route, { replace = false } = {}) {
            const method = replace ? 'replaceState' : 'pushState';
            window.history[method]({ documentRoute: route }, '', decoratedUrl(route));
        };

        window.setBoardUrl = function (title, { replace = false } = {}) {
            const method = replace ? 'replaceState' : 'pushState';
            const route = title && title !== 'Home'
                ? `/#${encodeURIComponent(title)}`
                : '/';
            window.history[method](
                { boardTitle: title || 'Home' },
                '',
                decoratedUrl(route),
            );
        };
    }

    document.addEventListener('DOMContentLoaded', () => {
        updateWorldDecoration();
        buildSwitcher();
        keepVariantInNavigation();
        window.setTimeout(decoratePuddles, 0);

        const frame = document.querySelector('.mini-window');
        if (frame) {
            frame.addEventListener('load', () => applyToDocumentFrame(frame));
            applyToDocumentFrame(frame);
        }

        document.addEventListener('keydown', (event) => {
            const target = event.target;
            if (
                target instanceof HTMLElement
                && (target.matches('input, textarea, select') || target.isContentEditable)
            ) return;

            if (event.key === 'ArrowLeft') {
                event.preventDefault();
                cycleVariant(-1);
            } else if (event.key === 'ArrowRight') {
                event.preventDefault();
                cycleVariant(1);
            }
        });
    });

    window.addEventListener('popstate', () => chooseVariant(variantFromUrl()));
    window.prototypeThemeWorlds = { applyToDocumentFrame, chooseVariant };
})();
