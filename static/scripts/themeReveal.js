/** Persistent physical parts. Focus changes their poses; it never replaces
 * the visible object. CSS transitions reverse from the current rendered pose.
 * All drawings, part identities and closed poses come from validated packs. */
(function () {
    'use strict';
    const configurations = new WeakMap();

    function closedTransform(part, scale = 1) {
        return `translate(${part.x * scale}px, ${part.y * scale}px) scale(${part.scale}, ${part.scale * part.flipY})`;
    }

    function install(tile, assignment, svg) {
        if (!assignment.reveal) return;
        const reveal = assignment.reveal;
        configurations.set(tile, reveal);
        tile.dataset.themeReveal = 'true';
        svg.querySelectorAll(':scope > [data-theme-part]').forEach(group => {
            const part = reveal.parts[group.dataset.themePart];
            group.classList.add('theme-reveal-part');
            group.style.setProperty('--reveal-closed', closedTransform(part));
            group.style.setProperty('--reveal-open-opacity', part.openOpacity);
            group.style.transformOrigin = `${part.originX}px ${part.originY}px`;
        });

        // A foreground SVG is an occlusion plane above semantic HTML text.
        // It is pointer-inert and contains no duplicate visible background.
        const front = svg.cloneNode(true);
        front.removeAttribute('data-theme-object');
        front.removeAttribute('data-theme-size');
        front.removeAttribute('data-theme-identity');
        front.classList.add('theme-reveal-foreground');
        [...front.children].forEach(group => {
            if (group.tagName === 'defs') return;
            if (!reveal.parts[group.dataset.themePart]?.foreground) group.remove();
        });
        svg.querySelectorAll(':scope > [data-theme-part]').forEach(group => {
            if (reveal.parts[group.dataset.themePart].foreground) group.style.visibility = 'hidden';
        });
        if (front.querySelector('[data-theme-part]')) {
            // IDs were already namespaced per location. Give the extra plane
            // its own namespace as well (including local reference rewrites).
            const ids = [...front.querySelectorAll('[id]')].map(node => node.id);
            front.querySelectorAll('*').forEach(node => {
                for (const attribute of [...node.attributes]) {
                    let value = attribute.value;
                    for (const id of ids) {
                        if (value === `#${id}`) value = `#${id}-front`;
                        value = value.replaceAll(`url(#${id})`, `url(#${id}-front)`);
                    }
                    node.setAttribute(attribute.name, value);
                }
                if (node.id) node.id += '-front';
            });
            svg.after(front);
        }
        if (reveal.titlePart) tile.querySelector('.expanded-title').dataset.revealTitle = 'true';
    }

    function geometry(svg) {
        const box = svg.viewBox.baseVal;
        const scale = Math.min(svg.clientWidth / box.width, svg.clientHeight / box.height);
        const style = getComputedStyle(svg);
        return {
            scale,
            left: parseFloat(style.left) + (svg.clientWidth - box.width * scale) / 2 - box.x * scale,
            top: parseFloat(style.top) + (svg.clientHeight - box.height * scale) / 2 - box.y * scale,
        };
    }

    function layout(tile) {
        const reveal = configurations.get(tile);
        if (!reveal) return true;
        const body = tile.querySelector('.tile-expanded .paper-body');
        const svg = body.querySelector('[data-theme-size="expanded"]');
        const {scale, left, top} = geometry(svg);
        const title = body.querySelector('.expanded-title');
        let titleFits = true;
        if (reveal.titlePart) {
            const marker = svg.querySelector('[data-theme-title-area]');
            Object.assign(title.style, {
                left: `${left + Number(marker.getAttribute('x')) * scale}px`,
                top: `${top + Number(marker.getAttribute('y')) * scale}px`,
                width: `${Number(marker.getAttribute('width')) * scale}px`,
                height: `${Number(marker.getAttribute('height')) * scale}px`,
            });
            title.style.removeProperty('font-size');
            let size = parseFloat(getComputedStyle(title).fontSize);
            while ((title.scrollWidth > title.clientWidth + 1 || title.scrollHeight > title.clientHeight + 1) && size > 20) {
                size = Math.max(20, size - .5);
                title.style.fontSize = `${size}px`;
            }
            titleFits = title.scrollWidth <= title.clientWidth + 1 && title.scrollHeight <= title.clientHeight + 1;
        }
        body.querySelectorAll('.expanded-title,.expanded-text,.expanded-open,.home-theme-selector').forEach(node => {
            const part = reveal.parts[node === title && reveal.titlePart ? reveal.titlePart : reveal.contentPart];
            node.style.setProperty('--reveal-content-closed', closedTransform(part, scale));
            node.style.transformOrigin = `${left + part.originX * scale - node.offsetLeft}px ${top + part.originY * scale - node.offsetTop}px`;
        });
        return titleFits;
    }

    function clean(tile) {
        if (!configurations.has(tile)) return;
        configurations.delete(tile);
        delete tile.dataset.themeReveal;
        tile.querySelectorAll('.theme-reveal-foreground').forEach(node => node.remove());
        tile.querySelectorAll('.expanded-title,.expanded-text,.expanded-open,.home-theme-selector').forEach(node => {
            node.style.removeProperty('--reveal-content-closed');
            node.style.removeProperty('transform-origin');
            if (node.dataset.revealTitle) {
                delete node.dataset.revealTitle;
                for (const key of ['left', 'top', 'width', 'height']) node.style.removeProperty(key);
            }
        });
    }
    window.themeReveal = {install, layout, clean};
}());
