/**
 * chalkArrowsTweaks.js — live tweak panel for the chalk arrows.
 * Activated by `?tweak=1` (same flag as the chalkboard texture panel).
 *
 * Lets you live-edit:
 *   - Arrow style: open V / closed triangle / no head
 *   - Head position: end / start / both / none
 *   - Inset on each end (visual gap from each tile)
 *   - Head size, stroke width, opacity, color, wobble
 *
 * Each control mutates window.chalkArrowsConfig and triggers
 * window.redrawChalkArrows().
 */

(function () {
    if (!new URLSearchParams(window.location.search).has('tweak')) return;

    function row(label, hint, type, key, opts) {
        opts = opts || {};
        const wrap = document.createElement('label');
        wrap.style.cssText = 'display:grid;grid-template-columns:120px 1fr 50px;gap:8px;align-items:center;font:11px/1.3 system-ui,sans-serif;color:#eee;';

        const labelBlock = document.createElement('span');
        labelBlock.style.cssText = 'display:flex;flex-direction:column;line-height:1.15';
        const main = document.createElement('span');
        main.textContent = label;
        main.style.cssText = 'font-weight:500';
        labelBlock.appendChild(main);
        if (hint) {
            const sub = document.createElement('span');
            sub.textContent = hint;
            sub.style.cssText = 'font-size:9.5px;color:#9aa;font-style:italic';
            labelBlock.appendChild(sub);
        }
        wrap.appendChild(labelBlock);

        let input;
        const cfg = window.chalkArrowsConfig;

        if (type === 'range') {
            input = document.createElement('input');
            input.type = 'range';
            input.min = opts.min;
            input.max = opts.max;
            input.step = opts.step;
            input.value = cfg[key];
            input.style.cssText = 'width:100%';
            wrap.appendChild(input);
            const out = document.createElement('span');
            out.style.cssText = 'text-align:right;font-variant-numeric:tabular-nums;color:#ccc';
            out.textContent = cfg[key];
            wrap.appendChild(out);
            input.addEventListener('input', () => {
                const v = parseFloat(input.value);
                cfg[key] = v;
                out.textContent = v;
                window.redrawChalkArrows();
            });
        } else if (type === 'select') {
            input = document.createElement('select');
            input.style.cssText = 'width:100%;background:#1a2926;color:#eee;border:1px solid #354540;padding:3px;border-radius:3px';
            (opts.options || []).forEach((o) => {
                const opt = document.createElement('option');
                opt.value = o;
                opt.textContent = o;
                if (cfg[key] === o) opt.selected = true;
                input.appendChild(opt);
            });
            wrap.appendChild(input);
            wrap.appendChild(document.createElement('span'));
            input.addEventListener('change', () => {
                cfg[key] = input.value;
                window.redrawChalkArrows();
            });
        } else if (type === 'color') {
            input = document.createElement('input');
            input.type = 'color';
            input.value = cfg[key];
            input.style.cssText = 'width:36px;height:22px;border:none;background:transparent;padding:0;justify-self:start';
            wrap.appendChild(input);
            wrap.appendChild(document.createElement('span'));
            input.addEventListener('input', () => {
                cfg[key] = input.value;
                window.redrawChalkArrows();
            });
        }
        return wrap;
    }

    function sectionHeader(text) {
        const h = document.createElement('div');
        h.textContent = text;
        h.style.cssText = 'font:bold 11px system-ui;color:#bcd;margin:8px 0 2px;border-top:1px solid #354540;padding-top:6px;letter-spacing:0.4px;text-transform:uppercase';
        return h;
    }

    function makePanel() {
        const panel = document.createElement('div');
        panel.id = 'chalk-arrows-tweak-panel';
        panel.style.cssText = `
            position:fixed; top:380px; right:14px; z-index:10000;
            background:rgba(20,30,28,0.92); color:#eee;
            border:1px solid #4a5a55; border-radius:6px;
            padding:10px 12px; width:320px;
            box-shadow:0 8px 20px rgba(0,0,0,0.5);
            font-family:system-ui,sans-serif;
        `;

        const title = document.createElement('div');
        title.style.cssText = 'font:bold 12px system-ui;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center';
        title.innerHTML = '<span>arrow tweaks</span>';

        const toggleBtn = document.createElement('button');
        toggleBtn.textContent = '–';
        toggleBtn.style.cssText = 'background:#444;color:#eee;border:none;border-radius:3px;width:22px;height:22px;cursor:pointer;font:bold 14px monospace';
        title.appendChild(toggleBtn);
        panel.appendChild(title);

        const body = document.createElement('div');
        body.style.cssText = 'display:flex;flex-direction:column;gap:6px';

        body.appendChild(sectionHeader('Arrowhead'));
        body.appendChild(row(
            'Style',
            'V (open) / filled triangle / none',
            'select', 'headStyle',
            { options: ['open', 'closed', 'none'] }
        ));
        body.appendChild(row(
            'Position',
            'where the arrowhead(s) appear',
            'select', 'headPosition',
            { options: ['end', 'start', 'both', 'none'] }
        ));
        body.appendChild(row(
            'Length',
            'depth of the arrowhead',
            'range', 'headLen', { min: 1, max: 12, step: 0.1 }
        ));
        body.appendChild(row(
            'Half-width',
            'spread of the V / triangle',
            'range', 'headHalf', { min: 0.5, max: 8, step: 0.1 }
        ));

        body.appendChild(sectionHeader('Length'));
        body.appendChild(row(
            'Length',
            '0 = dot at midpoint · 1 = full center-to-center',
            'range', 'length', { min: 0, max: 1, step: 0.01 }
        ));

        body.appendChild(sectionHeader('Line style'));
        body.appendChild(row(
            'Color',
            'chalk hue',
            'color', 'color'
        ));
        body.appendChild(row(
            'Stroke width',
            'line thickness (device px)',
            'range', 'strokeWidth', { min: 0.5, max: 8, step: 0.1 }
        ));
        body.appendChild(row(
            'Opacity',
            'invisible → fully solid',
            'range', 'opacity', { min: 0, max: 1, step: 0.02 }
        ));
        body.appendChild(row(
            'Wobble',
            'hand-drawn curve (0 = straight)',
            'range', 'wobble', { min: 0, max: 8, step: 0.1 }
        ));

        panel.appendChild(body);

        toggleBtn.addEventListener('click', () => {
            const collapsed = body.style.display === 'none';
            body.style.display = collapsed ? 'flex' : 'none';
            toggleBtn.textContent = collapsed ? '–' : '+';
        });

        return panel;
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.body.appendChild(makePanel());
    });
})();
