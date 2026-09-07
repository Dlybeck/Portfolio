/* THROWAWAY: Does a cloud/mist reading surface belong better than a notebook?
 * Compare current / mist bank / sky clearing on existing routes with grounding=A/B/C.
 * Lily uses the same comparisons to test surface-current connector treatments.
 * Loaded ONLY by scripts/prototype_theme_refinement.py, never the normal app.
 * No navigation keys intercepted; no pack or content is persisted/rewritten.
 */
(() => {
    const root = document.documentElement;
    const variants = ['A', 'B', 'C'];
    const names = {
        clouds: ['Current notebook + dots', 'Mist bank + cloud filaments', 'Sky clearing + wind strokes'],
        lily: ['Current connections', 'Surface-current ribbons', 'Ripple paths'],
        vinyl: ['Rejected — not a candidate', 'Full inner sleeve + record', 'Record + liner insert'],
    };
    let variant = new URL(location.href).searchParams.get('grounding') || 'A';
    if (!variants.includes(variant)) variant = 'A';
    const vinylPaperEdge = '#b7a991';
    const style = document.createElement('style');
    style.textContent = `
      #grounding-prototype {position:fixed;z-index:99999;bottom:8px;left:50%;transform:translateX(-50%);
        display:flex;align-items:center;gap:8px;padding:6px 10px;width:max-content;max-width:95vw;box-sizing:border-box;
        border:1px solid #71808e;border-radius:8px;background:#182431;color:white;font:12px system-ui;
        box-shadow:0 2px 8px #0004}
      #grounding-prototype button {font:18px system-ui;background:#fff;color:#182431;border:0;
        border-radius:4px;min-width:38px;min-height:38px;cursor:pointer}
      #grounding-prototype span {min-width:0;text-align:center}
      html[data-grounding-theme="vinyl"][data-grounding]:not([data-grounding="A"]) {
        --theme-pack-expanded-width:380px!important;--theme-pack-expanded-min-height:380px!important;
        --theme-pack-phone-expanded-width:min(340px,calc(100vw - 38px))!important;
        --theme-pack-phone-expanded-min-height:min(340px,calc(100vw - 38px))!important;
        --theme-pack-expanded-title-size:1.4rem!important;
        --theme-pack-expanded-text-size:1.125rem!important;
        --theme-pack-phone-expanded-text-size:1rem!important}
      html[data-grounding-theme="vinyl"][data-grounding="B"] {
        --theme-pack-viewer-bg:var(--prototype-vinyl-paper,#f4e8ce)!important;
        --theme-pack-viewer-border:var(--prototype-vinyl-jacket,${vinylPaperEdge})!important;
        --theme-pack-viewer-border-width:8px!important;
        --theme-pack-phone-expanded-width:min(300px,calc(100vw - 70px))!important;
        --theme-pack-phone-expanded-min-height:min(300px,calc(100vw - 70px))!important;
        --theme-pack-expanded-text-line-height:1.35!important}
      html[data-grounding-theme="clouds"][data-grounding]:not([data-grounding="A"]) {
        --theme-pack-viewer-bg:transparent!important;--theme-pack-viewer-bg-image:none!important;
        --theme-pack-viewer-border-width:0!important;--theme-pack-viewer-radius:0!important;
        --theme-pack-viewer-shadow:none!important;--theme-pack-viewer-rotation:0deg!important;
        --theme-pack-viewer-padding:36px 40px 44px!important;
        --theme-pack-phone-viewer-padding:28px 18px 32px!important;
        --theme-pack-viewer-enter-offset:35vw!important;--theme-pack-viewer-enter-rotation:0deg!important;
        --theme-pack-viewer-exit-offset:-45vw!important;--theme-pack-viewer-exit-rotation:0deg!important;
        --theme-pack-viewer-enter-duration:.38s!important;--theme-pack-viewer-exit-duration:.24s!important}
      html[data-grounding-theme="clouds"][data-grounding]:not([data-grounding="A"]) .theme-viewer-decoration {display:none!important}
      #prototype-cloud-surface {position:absolute;inset:-12px -18px;z-index:-1;pointer-events:none;
        width:calc(100% + 36px);height:calc(100% + 24px);overflow:visible}
      html[data-grounding-theme="clouds"][data-grounding="C"] .mini-window-container {background:transparent!important}
      html[data-grounding-theme="clouds"][data-grounding="C"] body:has(.mini-window-container:is(.open,.closing))::after {
        content:'';position:fixed;inset:0;z-index:450;pointer-events:none;
        background:linear-gradient(180deg,#b9dcec,#e4f0f2)}
      html[data-grounding-theme="clouds"][data-grounding="C"] #prototype-cloud-surface {
        position:fixed;inset:0;width:100vw;height:100vh;z-index:451;display:none}
      html[data-grounding-theme="clouds"][data-grounding="C"] body:has(.mini-window-container:is(.open,.closing)) #prototype-cloud-surface {display:block}
      @media (prefers-reduced-motion:reduce) {
        html[data-grounding-theme="clouds"][data-grounding]:not([data-grounding="A"]) .mini-window-container {
          animation-duration:0s!important}}
    `;
    document.head.append(style);
    const bar = document.createElement('div');
    bar.id = 'grounding-prototype';
    bar.setAttribute('role', 'group');
    bar.setAttribute('aria-label', 'Private grounding prototype comparison');
    const previous = document.createElement('button');
    previous.textContent = '‹'; previous.setAttribute('aria-label', 'Previous prototype');
    const label = document.createElement('span');
    const next = document.createElement('button');
    next.textContent = '›'; next.setAttribute('aria-label', 'Next prototype');
    bar.append(previous, label, next);
    document.body.append(bar);
    const svgNS = 'http://www.w3.org/2000/svg';
    const cloudFill = '#f4f8f8';

    // Disposable in-memory art replacement: original runtime, writing nodes,
    // carrier title and reversible Swap trajectory remain responsible for motion.
    // Retain source/cloned artwork for restoration; rejected Vinyl A is not selectable.
    // This nested peek is an experiment, not executable theme-pack behavior.
    const vinylOriginals = new WeakMap();
    const vinylJacketOriginals = new WeakMap();

    // Prototype authoring palette: independent, stable axes; no navigation-time randomness.
    // These choices can become pack factors/SVG assets without changing the Swap itself.
    const vinylInks = ['#34556a','#a65040','#416557','#6a4d68','#9a693c','#394857'];
    const vinylPapers = ['#f5edda','#faf5e9','#eddfc2','#f0ebdc'];
    // Curated current collection avoids identical covers in one neighborhood.
    // New locations fall back to the stable authoring seed below.
    const vinylCoverChoices = {
        'Home':2, 'Hobbies':3, 'Projects':5, 'Work Experience':4, 'Education':1,
        '3D Printing':0, 'Gaming':4, 'Tennis':5, 'Other Models':1, 'Puzzles':2,
        'Programs':0, 'Websites':3, 'Digital Planner':4, 'This website':1,
        'ScribbleScan':2, 'College':4, 'Early Education':5,
    };
    const vinylPressings = [
        {color:'#232425',groove:'#66635d'},
        {color:'#232425',groove:'#66635d'},
        {color:'#733b41',groove:'#ad7778'},
        {color:'#294e61',groove:'#73939e'},
        {color:'#35594b',groove:'#829c87'},
        {color:'#d5b77f',groove:'#8e744f'},
        {color:'#25272a',groove:'#a2a099',split:'#d0b188'},
        {color:'#384d60',groove:'#93a6b2',split:'#9faaa9'},
    ];
    function vinylChoice(title, axis, count) {
        let value = 2166136261;
        for (const char of `${title}/${axis}`) value = Math.imul(value ^ char.charCodeAt(0),16777619);
        // Mix the low bits too: paper/print/pressing use power-of-two catalogs
        // and must not collapse into the same permanently coupled combinations.
        value = Math.imul(value ^ (value >>> 16),0x85ebca6b);
        value = Math.imul(value ^ (value >>> 13),0xc2b2ae35);
        value ^= value >>> 16;
        return (value >>> 0) % count;
    }
    function vinylIdentity(title) {
        return {
            cover:vinylCoverChoices[title] ?? vinylChoice(title,'cover',6),
            ink:vinylInks[vinylChoice(title,'ink',vinylInks.length)],
            paper:vinylPapers[vinylChoice(title,'paper',vinylPapers.length)],
            print:vinylChoice(title,'print',4),
            pressing:vinylPressings[vinylChoice(title,'pressing',vinylPressings.length)],
            tracks:vinylChoice(title,'tracks',3),
        };
    }
    function vinylCover({cover,ink}) {
        const cream = '#f6edda', accent = '#c58d62';
        // All printing stays above the jacket's permanent title, inside its face.
        const pictures = [
            `<path d="M38 88L88 35L133 88Z" fill="${ink}"/><path d="M100 88L151 49L202 88Z" fill="${accent}"/><circle cx="173" cy="39" r="11" fill="${accent}"/>`,
            `<path d="M62 87V68A58 58 0 0 1 178 68V87Z" fill="${ink}"/><path d="M77 87V68A43 43 0 0 1 163 68V87Z" fill="${accent}"/><path d="M93 87V68A27 27 0 0 1 147 68V87Z" fill="${cream}"/>`,
            `<circle cx="157" cy="44" r="17" fill="${accent}"/><path d="M38 72Q64 46 96 70T156 67T202 66V88H38Z" fill="${ink}"/><path d="M38 84Q67 65 104 82T169 78T202 78V88H38Z" fill="${accent}"/>`,
            `<path d="M45 78L99 25H124L70 78Z M103 88L166 25H192L130 88Z" fill="${ink}"/><path d="M72 88L135 25H158L95 88Z" fill="${accent}"/>`,
            `<path d="M120 86C75 87 56 65 63 40C96 37 115 53 120 86Z" fill="${ink}"/><path d="M122 80C119 45 145 29 179 37C180 60 157 81 122 80Z" fill="${accent}"/><path d="M82 52L121 85L158 47" fill="none" stroke="${cream}" stroke-width="2"/>`,
            `<path d="M38 88V66L64 47L80 62L111 31L140 66L164 51L202 78V88Z" fill="${ink}"/><circle cx="62" cy="39" r="9" fill="${accent}"/><path d="M39 84H201V88H39Z" fill="${accent}"/>`,
        ];
        return `<rect x="38" y="25" width="164" height="63" fill="${cream}"/>${pictures[cover]}`;
    }
    function vinylJackets(tile, identity) {
        for (const jacket of tile.querySelectorAll('[data-theme-part="sleeve"]')) {
            if (!vinylJacketOriginals.has(jacket)) vinylJacketOriginals.set(jacket,jacket.innerHTML);
            jacket.innerHTML = vinylJacketOriginals.get(jacket);
            if (variant !== 'B') continue;
            const printing = jacket.querySelector('[data-visual-axis="seam"]');
            // Keep the exact approved jacket edge, seam and opening notch.
            [...printing.children].slice(2).forEach(node => node.remove());
            printing.insertAdjacentHTML('beforeend',vinylCover(identity));
        }
    }
    function vinylSleevePrint({print,ink}) {
        // Quiet printed accents stay outside both safe text rectangles.
        return [
            '',
            `<path d="M30 29H94 M146 29H210 M30 217H210" fill="none" stroke="${ink}" stroke-width="1.3"/>`,
            `<path d="M20 28H23V216H20Z" fill="${ink}"/><path d="M30 217H210" fill="none" stroke="${ink}" stroke-width=".7"/>`,
            `<path d="M30 26H87V30H30Z M153 26H210V30H153Z M30 216H87V219H30Z M153 216H210V219H153Z" fill="${ink}"/>`,
        ][print];
    }
    function vinylDisc(identity) {
        const {pressing,tracks,ink} = identity;
        const radii = [[91,86,81,75,70,65,58,53,48,43],
            [91,87,83,79,70,66,62,53,49,45],
            [91,86,81,76,67,62,57,48,43]];
        // Color is pressed material. Both halves share one circular rim/groove field.
        return `<circle cx="120" cy="120" r="98" fill="${pressing.color}" stroke="#24282a" stroke-width="1.5"/>
            ${pressing.split ? `<path d="M80.14 30.47A98 98 0 0 1 159.86 209.53Z" fill="${pressing.split}"/>` : ''}
            ${radii[tracks].map(r => `<circle cx="120" cy="120" r="${r}" fill="none" stroke="${pressing.groove}" stroke-width=".65"/>`).join('')}
            <circle cx="120" cy="120" r="33" fill="${ink}"/>
            <circle cx="120" cy="120" r="3" fill="#191c1d"/>
            <circle cx="120" cy="120" r="7" fill="none" stroke="#f5edda" stroke-width=".6"/>`;
    }
    const vinylProgress = new MutationObserver(changes => {
        for (const tile of new Set(changes.map(change => change.target))) peekRecord(tile);
    });
    function peekRecord(tile) {
        const record = tile.querySelector('[data-prototype-disc]');
        if (!record) return;
        const p = Math.max(0,Math.min(1,(Number(tile.dataset.swapProgress)-.72)/.28));
        const distance = 66*p*p*(3-2*p);
        record.setAttribute('transform',`translate(0 ${-distance})`);
    }
    function vinyl() {
        vinylProgress.disconnect();
        if (root.dataset.boardTheme !== 'vinyl') return;
        for (const tile of document.querySelectorAll('[data-theme-swap]')) {
            const identity = vinylIdentity(tile.dataset.title);
            vinylJackets(tile,identity);
            const source = tile.querySelector('.tile-expanded [data-theme-size="expanded"]');
            const art = tile.querySelector('[data-swap-part="record"] [data-theme-part="record"]');
            if (!source || !art) continue;
            const title = source.querySelector('[data-theme-title-area]');
            const content = source.querySelector('[data-theme-content-area]');
            if (!vinylOriginals.has(art)) vinylOriginals.set(art, {
                markup:art.innerHTML,
                title:['x','y','width','height'].map(k => title.getAttribute(k)),
                content:['x','y','width','height'].map(k => content.getAttribute(k)),
            });
            const saved = vinylOriginals.get(art);
            let titleBox = saved.title, contentBox = saved.content;
            if (variant === 'A') art.innerHTML = saved.markup;
            else {
                // A 100 mm label on a 12-inch record is about one third of its
                // diameter. Packaging, not a giant imaginary label, carries copy.
                const cx = variant === 'B' ? 120 : 108;
                const cy = variant === 'B' ? 120 : 104;
                const grooves = [91,86,81,76,71,66,61,56,51,46].map(r =>
                    `<circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="#66635d" stroke-width=".65"/>`).join('');
                const disc = `<circle cx="${cx}" cy="${cy}" r="98" fill="#232425" stroke="#111618" stroke-width="1.5"/>
                    ${grooves}<circle cx="${cx}" cy="${cy}" r="33" fill="#bc6545"/>
                    <circle cx="${cx}" cy="${cy}" r="3" fill="#191c1d"/>
                    <circle cx="${cx}" cy="${cy}" r="7" fill="none" stroke="#7e4434" stroke-width=".6"/>`;
                art.innerHTML = variant === 'B' ? `
                    <rect x="12" y="12" width="216" height="216" fill="#e4dac4"/>
                    <g data-prototype-disc>${vinylDisc(identity)}</g>
                    <path data-prototype-inner-sleeve d="M12 12H108 Q108 21 120 21 Q132 21 132 12H228V228H12Z" fill="${identity.paper}" stroke="${vinylPaperEdge}" stroke-width="1"/>
                    <path d="M17 17V223H222" fill="none" stroke="#ded3bd" stroke-width=".7"/>
                    ${vinylSleevePrint(identity)}`
                    : `${disc}<path d="M34 100H232V234H34Z" fill="#f4e8ce" stroke="#baaa90" stroke-width="1.2"/>
                    <path d="M43 105H223" stroke="#9b4537" stroke-width="2"/>`;
                titleBox = variant === 'B' ? [28,40,184,36] : [45,112,176,27];
                contentBox = variant === 'B' ? [28,84,184,125] : [45,143,176,82];
            }
            ['x','y','width','height'].forEach((key,i) => {
                title.setAttribute(key,titleBox[i]); content.setAttribute(key,contentBox[i]);
            });
            peekRecord(tile);
            vinylProgress.observe(tile,{attributes:true,attributeFilter:['data-swap-progress']});
        }
        // Existing responsive fit also lays out the permanent source markers.
        window.dispatchEvent(new Event('resize'));
    }

    function surface() {
        document.querySelector('#prototype-cloud-surface')?.remove();
        if (root.dataset.boardTheme !== 'clouds' || variant === 'A') return;
        const viewer = document.querySelector('.mini-window-container');
        if (!viewer) return;
        const svg = document.createElementNS(svgNS, 'svg');
        svg.id = 'prototype-cloud-surface';
        svg.setAttribute('viewBox', '0 0 1000 1000');
        svg.setAttribute('preserveAspectRatio', 'none');
        svg.setAttribute('aria-hidden', 'true');
        // Broad cloud bank, not overlapping circles or a manufactured frame.
        svg.innerHTML = variant === 'B' ? `
          <path fill="#dcecf1" d="M15 90 Q-18 38 99 29 Q167 -7 287 14 Q439 -16 596 13 Q784 -8 879 28 Q995 16 978 115 L992 867 Q1020 961 884 977 Q739 1015 578 986 Q402 1014 254 983 Q58 1005 25 940 Q-7 840 20 704 Q-10 564 17 400 Q-5 248 15 90Z"/>
          <path fill="${cloudFill}" d="M31 96 Q4 55 112 45 Q178 13 302 31 Q439 7 585 29 Q764 7 869 43 Q975 34 960 116 L975 863 Q993 942 870 956 Q733 991 578 963 Q403 992 268 962 Q78 983 43 929 Q15 845 38 702 Q12 566 35 401 Q13 250 31 96Z"/>` : `
          <path fill="#edf5f7" d="M0 0H1000V45 Q917 72 864 45 Q758 65 695 40 Q567 58 478 31 Q372 52 252 34 Q137 58 0 35Z"/>
          <path fill="#edf5f7" d="M0 1000V949 Q105 923 190 949 Q294 931 379 959 Q500 941 596 968 Q745 946 831 963 Q921 937 1000 950V1000Z"/>`;
        (variant === 'C' ? document.body : viewer).prepend(svg);
    }

    function syncVinylPaper() {
        // Keep the paper distinct from the actual jacket beneath it. This
        // prototype reads its known artwork; pack integration will export both colors.
        const paper = root.dataset.boardTheme === 'vinyl' && variant === 'B'
            ? vinylIdentity(window.currentTileTitle || 'Home').paper : null;
        const jacket = paper && document.querySelector(
            '.tile-container.expanded .tile-base [data-theme-part="sleeve"] [data-visual-axis="silhouette"] rect'
        )?.getAttribute('fill');
        if (paper) root.style.setProperty('--prototype-vinyl-paper',paper);
        else root.style.removeProperty('--prototype-vinyl-paper');
        if (jacket) root.style.setProperty('--prototype-vinyl-jacket',jacket);
        else root.style.removeProperty('--prototype-vinyl-jacket');
        return paper;
    }

    function documentStyle() {
        const paper = syncVinylPaper();
        const doc = document.querySelector('.mini-window')?.contentDocument;
        if (!doc?.head) return;
        doc.querySelector('#prototype-reading-style')?.remove();
        if (paper) {
            const css = doc.createElement('style');
            css.id = 'prototype-reading-style';
            css.textContent = `html[data-theme-pack-visual][data-board-theme="vinyl"] {
                --theme-pack-page-bg:${paper}!important;}`;
            doc.head.append(css);
            return;
        }
        if (root.dataset.boardTheme !== 'clouds' || variant === 'A') return;
        const css = doc.createElement('style');
        css.id = 'prototype-reading-style';
        css.textContent = `html[data-theme-pack-visual] {
          --theme-pack-page-bg:${variant === 'B' ? cloudFill : 'transparent'}!important;
          --theme-pack-page-bg-image:none!important;--theme-pack-ink:#243e51!important;
          --theme-pack-title-ink:#243e51!important;--theme-pack-secondary-ink:#36546a!important;
          --theme-pack-button-bg:#315f79!important;--theme-pack-button-radius:6px!important;
          --theme-pack-font-title:'Patrick Hand',cursive!important;
          --theme-pack-font-heading:'Patrick Hand',cursive!important;
          --theme-pack-title-size:1.65rem!important;--theme-pack-title-margin:16px 0 12px!important;
          --theme-pack-media-bg:#f6fafb!important;--theme-pack-media-border:#f6fafb!important;
          --theme-pack-media-shadow:none!important;--theme-pack-media-border-width:3px!important;
          --theme-pack-body-size:1.125rem!important;--theme-pack-body-line-height:1.5!important}
          html, body {background:${variant === 'B' ? cloudFill : 'transparent'}!important}`;
        doc.head.append(css);
    }

    function ribbon(path, width, offset = 0, phase = 0) {
        const length = path.getTotalLength();
        const reach = Math.min(64, innerWidth*.12);
        const sides = [[], []];
        for (let i = 0; i <= 32; i++) {
            const t = i / 32;
            const distance = t*(length + 2*reach) - reach;
            const clamped = Math.max(0, Math.min(length, distance));
            const p = path.getPointAtLength(clamped);
            const a = path.getPointAtLength(Math.max(0, clamped - 1));
            const b = path.getPointAtLength(Math.min(length, clamped + 1));
            const norm = Math.hypot(b.x-a.x, b.y-a.y) || 1;
            const nx = -(b.y-a.y)/norm, ny = (b.x-a.x)/norm;
            p.x += (b.x-a.x)/norm*(distance-clamped);
            p.y += (b.y-a.y)/norm*(distance-clamped);
            const drift = Math.sin(Math.PI*t)*Math.sin(t*5+phase)*Math.min(34,length*.11);
            const spread = width * Math.pow(Math.sin(Math.PI*t), .7) *
                (1 + .2*Math.sin(t*13 + phase));
            for (let side = 0; side < 2; side++) {
                const d = offset + drift + (side ? -1 : 1) * spread;
                sides[side].push(`${(p.x+nx*d).toFixed(2)},${(p.y+ny*d).toFixed(2)}`);
            }
        }
        return 'M' + sides[0].join(' L') + ' L' + sides[1].reverse().join(' L') + 'Z';
    }

    let relationshipFrame = 0;
    const relationshipObserver = new MutationObserver(() => {
        if (!relationshipFrame) relationshipFrame = requestAnimationFrame(() => {
            relationshipFrame = 0; connectors();
        });
    });
    function connectors() {
        relationshipObserver.disconnect();
        const theme = root.dataset.boardTheme;
        document.querySelectorAll('.prototype-flow').forEach(el => el.remove());
        document.querySelectorAll('[data-prototype-hidden]').forEach(el => {
            el.style.removeProperty('visibility'); delete el.dataset.prototypeHidden;
        });
        if (!['clouds','lily'].includes(theme) || variant === 'A') return;
        document.querySelectorAll('.arrows-group > g').forEach((group, index) => {
            const paths = [...group.querySelectorAll('path')];
            const path = paths.sort((a,b) => b.getTotalLength()-a.getTotalLength())[0];
            if (!path) return;
            for (const original of paths) {
                original.dataset.prototypeHidden = ''; original.style.visibility = 'hidden';
            }
            const flow = document.createElementNS(svgNS, 'g');
            flow.classList.add('prototype-flow'); flow.setAttribute('aria-hidden', 'true');
            const profiles = theme === 'clouds'
                ? (variant === 'B' ? [[4.5,0,.6],[1.8,10,.38]] : [[1.2,0,.72],[.7,7,.42]])
                : (variant === 'B' ? [[1.5,-5,.5],[.8,6,.32]] : [[2.6,0,.46],[.8,11,.26]]);
            for (const [width, offset, opacity] of profiles) {
                const stroke = document.createElementNS(svgNS, 'path');
                stroke.setAttribute('d', ribbon(path, width, offset, index*1.7));
                stroke.setAttribute('fill', theme === 'clouds' ? '#eef7f9' : '#c3e8e4');
                stroke.setAttribute('opacity', opacity);
                flow.append(stroke);
            }
            if (theme === 'lily' && variant === 'C') {
                flow.replaceChildren();
                const length = path.getTotalLength();
                for (const t of [.18,.39,.63,.84]) {
                    const p = path.getPointAtLength(length*t);
                    const a = path.getPointAtLength(Math.max(0,length*t-1));
                    const b = path.getPointAtLength(Math.min(length,length*t+1));
                    const norm = Math.hypot(b.x-a.x,b.y-a.y)||1;
                    const ux=(b.x-a.x)/norm, uy=(b.y-a.y)/norm, nx=-uy, ny=ux;
                    const width = 11 + 7*Math.sin(t*7+index)**2;
                    for (const offset of [0,6]) {
                        const wave=document.createElementNS(svgNS,'path');
                        const x=p.x+ux*offset,y=p.y+uy*offset;
                        wave.setAttribute('d',`M${x-nx*width},${y-ny*width} Q${x+ux*width*.7},${y+uy*width*.7} ${x+nx*width},${y+ny*width}`);
                        wave.setAttribute('fill','none'); wave.setAttribute('stroke','#c3e8e4');
                        wave.setAttribute('stroke-width',offset ? '.8':'1.5');
                        wave.setAttribute('opacity',offset ? '.25':'.42');
                        flow.append(wave);
                    }
                }
            }
            group.append(flow);
        });
        const relationships = document.querySelector('.chalk-arrows');
        if (relationships) relationshipObserver.observe(relationships, {
            childList:true, subtree:true, attributes:true, attributeFilter:['d']
        });
    }

    function apply() {
        if (root.dataset.boardTheme === 'vinyl' && variant === 'A') {
            variant = 'B';
            const url = new URL(location.href); url.searchParams.set('grounding',variant);
            history.replaceState(history.state,'',url);
        }
        root.dataset.grounding = variant;
        root.dataset.groundingTheme = root.dataset.boardTheme;
        const descriptions = names[root.dataset.boardTheme];
        label.textContent = descriptions ? `PROTOTYPE ${variant} · ${descriptions[variants.indexOf(variant)]}`
            : 'PROTOTYPE · This theme is unchanged';
        previous.disabled = next.disabled = !descriptions;
        surface(); documentStyle(); connectors(); vinyl();
    }
    function cycle(delta) {
        const candidates = root.dataset.boardTheme === 'vinyl' ? ['B','C'] : variants;
        variant = candidates[(candidates.indexOf(variant) + delta + candidates.length) % candidates.length];
        const url = new URL(location.href); url.searchParams.set('grounding', variant);
        history.replaceState(history.state, '', url); apply();
    }
    // Keep the app's outside-document handler from closing the page while
    // comparing. Only this visibly separate prototype bar intercepts clicks.
    window.addEventListener('click', event => {
        if (!bar.contains(event.target)) return;
        event.preventDefault(); event.stopImmediatePropagation();
        const button = event.target.closest('button');
        if (button && !button.disabled) cycle(button === next ? 1 : -1);
    }, true);
    const observer = new MutationObserver(() => requestAnimationFrame(apply));
    observer.observe(root, {attributes:true, attributeFilter:['data-board-theme']});
    const readingFrame = document.querySelector('.mini-window');
    if (readingFrame) {
        readingFrame.addEventListener('load', documentStyle);
        // Navigation selects the destination before assigning src. Match the
        // carrier before paint, not only once the new document finishes loading.
        new MutationObserver(syncVinylPaper).observe(readingFrame, {
            attributes:true, attributeFilter:['src']
        });
    }
    // Navigation's existing redraw owns path geometry. Restyle only after its redraw.
    const redraw = window.redrawChalkArrows;
    window.redrawChalkArrows = (...args) => { const result = redraw?.(...args); connectors(); return result; };
    document.fonts.ready.then(apply);
    window.addEventListener('load', apply, {once:true});
})();
