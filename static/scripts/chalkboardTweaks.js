/**
 * chalkboardTweaks.js — live tweak panel for the chalkboard texture.
 *
 * Activated only when the URL has `?tweak=1`. Injects a small floating
 * panel with sliders + color picker; on every change it overrides the
 * .map::before background by writing into a dynamic <style> tag.
 *
 * Sliders also drive a "Copy CSS" button so once you find values you
 * like, you can paste the snippet straight into map.css.
 */

(function () {
    if (!new URLSearchParams(window.location.search).has('tweak')) return;

    const defaults = {
        baseColor: '#233b35',
        l1Size: 1600,
        l1Freq: 0.55,
        l1Alpha: 0.05,
        l1Seed: 5,
        l2Size: 2400,
        l2Freq: 0.04,
        l2Alpha: 0.10,
        l2Seed: 11,
    };
    const state = { ...defaults };

    function buildSvgUrl(size, freq, alpha, seed) {
        const svg =
            `<svg xmlns='http://www.w3.org/2000/svg' width='${size}' height='${size}'>` +
            `<filter id='n'>` +
            `<feTurbulence type='fractalNoise' baseFrequency='${freq}' numOctaves='2' stitchTiles='stitch' seed='${seed}'/>` +
            `<feColorMatrix values='0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  ${alpha} 0 0 0 -${alpha / 2}'/>` +
            `</filter>` +
            `<rect width='100%' height='100%' filter='url(%23n)'/></svg>`;
        return `url("data:image/svg+xml;utf8,${svg}")`;
    }

    function buildCss() {
        const l1 = buildSvgUrl(state.l1Size, state.l1Freq, state.l1Alpha, state.l1Seed);
        const l2 = buildSvgUrl(state.l2Size, state.l2Freq, state.l2Alpha, state.l2Seed);
        return `.map::before {
  background-color: ${state.baseColor} !important;
  background-image:
    ${l1},
    ${l2} !important;
  background-size: ${state.l1Size}px ${state.l1Size}px, ${state.l2Size}px ${state.l2Size}px !important;
  background-repeat: repeat, repeat !important;
}`;
    }

    let styleEl;
    function applyStyle() {
        if (!styleEl) {
            styleEl = document.createElement('style');
            styleEl.id = 'chalkboard-tweaks';
            document.head.appendChild(styleEl);
        }
        styleEl.textContent = buildCss();
    }

    function row(label, hint, type, key, min, max, step) {
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

        const input = document.createElement('input');
        input.type = type;
        if (type === 'range') {
            input.min = min;
            input.max = max;
            input.step = step;
            input.value = state[key];
            input.style.cssText = 'width:100%';
        } else if (type === 'color') {
            input.value = state[key];
            input.style.cssText = 'width:36px;height:22px;border:none;background:transparent;padding:0;justify-self:start';
        }
        wrap.appendChild(input);

        const out = document.createElement('span');
        out.style.cssText = 'text-align:right;font-variant-numeric:tabular-nums;color:#ccc';
        out.textContent = state[key];
        if (type === 'range') wrap.appendChild(out); else wrap.appendChild(document.createElement('span'));

        input.addEventListener('input', () => {
            const v = type === 'range' ? parseFloat(input.value) : input.value;
            state[key] = v;
            if (type === 'range') out.textContent = v;
            applyStyle();
        });
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
        panel.id = 'chalkboard-tweak-panel';
        panel.style.cssText = `
            position:fixed; top:14px; right:14px; z-index:10000;
            background:rgba(20,30,28,0.92); color:#eee;
            border:1px solid #4a5a55; border-radius:6px;
            padding:10px 12px; width:320px;
            box-shadow:0 8px 20px rgba(0,0,0,0.5);
            font-family:system-ui,sans-serif;
        `;

        const title = document.createElement('div');
        title.style.cssText = 'font:bold 12px system-ui;margin-bottom:8px;display:flex;justify-content:space-between;align-items:center';
        title.innerHTML = '<span>chalkboard tweaks</span>';

        const toggleBtn = document.createElement('button');
        toggleBtn.textContent = '–';
        toggleBtn.style.cssText = 'background:#444;color:#eee;border:none;border-radius:3px;width:22px;height:22px;cursor:pointer;font:bold 14px monospace';
        title.appendChild(toggleBtn);
        panel.appendChild(title);

        const body = document.createElement('div');
        body.style.cssText = 'display:flex;flex-direction:column;gap:6px';

        body.appendChild(row(
            'Board color',
            'base slate green',
            'color', 'baseColor'
        ));

        body.appendChild(sectionHeader('Fine grain (chalk dust)'));
        body.appendChild(row(
            'Tile size',
            'px before texture repeats',
            'range', 'l1Size', 200, 3200, 50
        ));
        body.appendChild(row(
            'Detail',
            'low = chunky · high = fine specks',
            'range', 'l1Freq', 0.01, 2.0, 0.01
        ));
        body.appendChild(row(
            'Visibility',
            'subtle → bold',
            'range', 'l1Alpha', 0, 0.4, 0.005
        ));
        body.appendChild(row(
            'Pattern variant',
            'random shuffle (different look, same feel)',
            'range', 'l1Seed', 0, 30, 1
        ));

        body.appendChild(sectionHeader('Broad patches (wear & lighting)'));
        body.appendChild(row(
            'Tile size',
            'px before texture repeats',
            'range', 'l2Size', 400, 4000, 100
        ));
        body.appendChild(row(
            'Patch size',
            'low = huge clouds · high = small patches',
            'range', 'l2Freq', 0.01, 0.6, 0.005
        ));
        body.appendChild(row(
            'Visibility',
            'subtle → bold',
            'range', 'l2Alpha', 0, 0.4, 0.005
        ));
        body.appendChild(row(
            'Pattern variant',
            'random shuffle (different look, same feel)',
            'range', 'l2Seed', 0, 30, 1
        ));

        const buttons = document.createElement('div');
        buttons.style.cssText = 'display:flex;gap:6px;margin-top:8px';
        const reseedBtn = document.createElement('button');
        reseedBtn.textContent = 'reseed';
        reseedBtn.style.cssText = 'flex:1;background:#3a5;color:#fff;border:none;border-radius:3px;padding:5px;cursor:pointer;font:11px system-ui';
        reseedBtn.addEventListener('click', () => {
            state.l1Seed = Math.floor(Math.random() * 30);
            state.l2Seed = Math.floor(Math.random() * 30);
            applyStyle();
            // Refresh slider displays
            panel.querySelectorAll('input[type=range]').forEach((input) => {
                const evt = new Event('input', { bubbles: true });
                input.dispatchEvent(evt);
            });
            // Easier: just reload the panel
            const replacement = makePanel();
            panel.parentNode.replaceChild(replacement, panel);
        });
        buttons.appendChild(reseedBtn);

        const copyBtn = document.createElement('button');
        copyBtn.textContent = 'show CSS';
        copyBtn.style.cssText = 'flex:1;background:#357;color:#fff;border:none;border-radius:3px;padding:5px;cursor:pointer;font:11px system-ui';
        buttons.appendChild(copyBtn);
        body.appendChild(buttons);

        // Textarea for "show CSS" — read-only, displayed below buttons
        // when toggled. Easier to manually select+copy than relying on
        // clipboard API (which requires HTTPS to work, and we're on
        // plain HTTP via Tailscale).
        const cssOut = document.createElement('textarea');
        cssOut.readOnly = true;
        cssOut.style.cssText = 'width:100%;height:160px;margin-top:8px;font:10px/1.3 monospace;background:#0d1614;color:#cfd;border:1px solid #354540;border-radius:3px;padding:6px;display:none;resize:vertical';
        body.appendChild(cssOut);

        copyBtn.addEventListener('click', () => {
            const showing = cssOut.style.display !== 'none';
            if (showing) {
                cssOut.style.display = 'none';
                copyBtn.textContent = 'show CSS';
                return;
            }
            cssOut.value = buildCss();
            cssOut.style.display = 'block';
            cssOut.focus();
            cssOut.select();
            // Try clipboard too in case browser supports it.
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(cssOut.value).then(
                    () => { copyBtn.textContent = 'copied + shown'; },
                    () => { copyBtn.textContent = 'shown (select to copy)'; }
                );
            } else {
                copyBtn.textContent = 'shown (select to copy)';
            }
        });

        panel.appendChild(body);

        toggleBtn.addEventListener('click', () => {
            const collapsed = body.style.display === 'none';
            body.style.display = collapsed ? 'flex' : 'none';
            toggleBtn.textContent = collapsed ? '–' : '+';
        });

        return panel;
    }

    document.addEventListener('DOMContentLoaded', () => {
        applyStyle();
        document.body.appendChild(makePanel());
    });
})();
