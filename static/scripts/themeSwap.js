/** Opaque physical exchange: unfold, extract, change depth while clear, place.
 * One reversible progress value drives every part and its attached writing.
 * All artwork, closed poses, carrier and extraction distance come from data. */
(function () {
    'use strict';
    const states = new WeakMap();
    const reduced = matchMedia('(prefers-reduced-motion: reduce)');
    const clamp = x => Math.max(0, Math.min(1, x));
    const ease = x => x*x*(3-2*x);

    function render(state) {
        if (!state.geometry) return;
        const p = state.progress;
        const fold = ease(clamp(p/.2));
        const extract = ease(clamp((p-.2)/.35));
        const place = ease(clamp((p-.55)/.45));
        const {scale, left, top} = state.geometry;
        state.tile.dataset.swapProgress = String(p);
        for (const [name, layer] of state.layers) {
            const pose = state.parts[name];
            const moving = name === state.swap.movingPart;
            const x = pose.x * (1-place);
            const y = (pose.y + (moving ? state.swap.liftY * extract : 0)) * (1-place);
            const size = pose.scale + (1-pose.scale)*place;
            const flip = pose.flipY + (1-pose.flipY)*fold;
            layer.style.transformOrigin = `${left+pose.originX*scale}px ${top+pose.originY*scale}px`;
            layer.style.transform = `translate(${x*scale}px, ${y*scale}px) scale(${size}, ${size*flip})`;
            // Depth changes only after the item has fully cleared its carrier.
            layer.style.zIndex = moving ? (p >= .55 ? '10' : '2')
                : pose.flipY === -1 ? (p < .2 ? '5' : '1')
                : pose.foreground ? '4' : '0';
        }
        for (const {node, pose} of state.details) {
            const amount = ease(clamp((p - pose.start) / (1 - pose.start)));
            node.setAttribute('transform', `translate(${pose.x * amount} ${pose.y * amount})`);
        }
    }

    function drive(state) {
        const target = state.tile.classList.contains('expanded') ? 1 : 0;
        if (state.target === target) return;
        state.target = target;
        if (state.frame) return;
        let previous;
        const tick = now => {
            const elapsed = previous === undefined ? 0 : now-previous;
            previous = now;
            if (reduced.matches) state.progress = state.target;
            else state.progress += Math.sign(state.target-state.progress)
                * Math.min(Math.abs(state.target-state.progress), elapsed/state.duration);
            render(state);
            state.frame = state.progress === state.target ? 0 : requestAnimationFrame(tick);
        };
        state.frame = requestAnimationFrame(tick);
    }

    function install(tile, assignment, svg) {
        const body = svg.parentElement;
        const state = {tile, body, svg, swap:assignment.swap, parts:assignment.reveal.parts,
            layers:new Map(), details:[], nodes:[...body.querySelectorAll('.expanded-title,.expanded-text,.expanded-open,.home-theme-selector')],
            progress:tile.classList.contains('expanded') ? 1 : 0, frame:0};
        // Optional printed title zone: same moving surface, separate from the
        // body copy (e.g. either side of a record's physical spindle hole).
        state.titleMarker = svg.querySelector('[data-theme-title-area]');
        state.title = body.querySelector('.expanded-title');
        if (state.titleMarker) state.title.dataset.swapTitle = 'true';
        state.target = state.progress;
        const duration = getComputedStyle(tile).getPropertyValue('--theme-pack-cover-enter-duration').trim();
        const milliseconds = parseFloat(duration)*(duration.endsWith('ms') ? 1 : 1000);
        state.duration = Number.isFinite(milliseconds)
            ? Math.min(3000, Math.max(200, milliseconds)) : 650;
        for (const name of Object.keys(state.parts)) {
            const layer = document.createElement('div');
            layer.className = 'theme-swap-layer';
            layer.dataset.swapPart = name;
            const art = svg.cloneNode(true);
            ['data-theme-object','data-theme-size','data-theme-identity'].forEach(a => art.removeAttribute(a));
            [...art.children].forEach(n => {if (n.localName !== 'defs' && n.dataset.themePart !== name) n.remove();});
            // Local SVG references stay local and unique in each plane.
            const ids = [...art.querySelectorAll('[id]')].map(n => n.id);
            for (const n of art.querySelectorAll('*')) {
                for (const attr of [...n.attributes]) {
                    let value=attr.value;
                    for (const id of ids) {
                        if (value === `#${id}`) value=`#${id}-swap-${name}`;
                        value=value.replaceAll(`url(#${id})`,`url(#${id}-swap-${name})`);
                    }
                    n.setAttribute(attr.name,value);
                }
                if (n.id) n.id += `-swap-${name}`;
            }
            layer.append(art); body.append(layer); state.layers.set(name,layer);
        }
        state.details = (state.swap.details || []).map(pose => ({pose,
            node: state.layers.get(pose.part).querySelector(`[data-theme-swap-detail="${pose.element}"]`),
        }));
        const writing = document.createElement('div');
        writing.className = 'swap-carrier-title';
        writing.setAttribute('aria-hidden','true');
        writing.textContent = tile.dataset.title;
        state.writing = writing;
        state.layers.get(state.swap.carrierPart).append(writing);
        state.nodes.forEach(n => state.layers.get(state.swap.movingPart).append(n));
        svg.style.visibility = 'hidden';
        tile.dataset.themeSwap = 'true';
        states.set(tile,state);
        state.observer = new MutationObserver(() => drive(state));
        state.observer.observe(tile,{attributes:true,attributeFilter:['class']});
        // Establish closed poses before the first paint, not two fit frames later.
        layout(tile);
    }

    function layout(tile) {
        const s = states.get(tile);
        if (!s) return true;
        const vb=s.svg.viewBox.baseVal, css=getComputedStyle(s.svg);
        const scale=Math.min(s.svg.clientWidth/vb.width,s.svg.clientHeight/vb.height);
        const left=parseFloat(css.left)+(s.svg.clientWidth-vb.width*scale)/2-vb.x*scale;
        const top=parseFloat(css.top)+(s.svg.clientHeight-vb.height*scale)/2-vb.y*scale;
        s.geometry={scale,left,top};
        let titleFits = true;
        if (s.titleMarker) {
            const m=s.titleMarker;
            Object.assign(s.title.style, {left:`${left+Number(m.getAttribute('x'))*scale}px`,
                top:`${top+Number(m.getAttribute('y'))*scale}px`,
                width:`${Number(m.getAttribute('width'))*scale}px`,
                height:`${Number(m.getAttribute('height'))*scale}px`});
            s.title.style.removeProperty('font-size');
            while ((s.title.scrollWidth>s.title.clientWidth+1 || s.title.scrollHeight>s.title.clientHeight+1)
                    && parseFloat(getComputedStyle(s.title).fontSize)>20) {
                s.title.style.fontSize=`${Math.max(20,parseFloat(getComputedStyle(s.title).fontSize)-.5)}px`;
            }
            titleFits=s.title.scrollWidth<=s.title.clientWidth+1 && s.title.scrollHeight<=s.title.clientHeight+1;
        }
        const marker=s.svg.querySelector('[data-theme-carrier-title-area]');
        Object.assign(s.writing.style, {left:`${left+Number(marker.getAttribute('x'))*scale}px`,
            top:`${top+Number(marker.getAttribute('y'))*scale}px`,
            width:`${Number(marker.getAttribute('width'))*scale}px`,
            height:`${Number(marker.getAttribute('height'))*scale}px`});
        s.writing.style.fontSize='36px';
        while ((s.writing.scrollWidth>s.writing.clientWidth+1 || s.writing.scrollHeight>s.writing.clientHeight+1)
                && parseFloat(s.writing.style.fontSize)>28) {
            s.writing.style.fontSize=`${parseFloat(s.writing.style.fontSize)-.5}px`;
        }
        render(s);
        return titleFits && s.writing.scrollWidth <= s.writing.clientWidth+1 && s.writing.scrollHeight <= s.writing.clientHeight+1;
    }

    function clean(tile) {
        const s=states.get(tile);
        if (!s) return;
        s.observer.disconnect(); cancelAnimationFrame(s.frame);
        s.nodes.forEach(n => s.body.append(n));
        if (s.titleMarker) {
            delete s.title.dataset.swapTitle;
            for (const key of ['left','top','width','height','font-size']) s.title.style.removeProperty(key);
        }
        s.layers.forEach(n => n.remove());
        s.svg.style.removeProperty('visibility');
        delete tile.dataset.themeSwap; delete tile.dataset.swapProgress;
        states.delete(tile);
    }
    window.themeSwap={install,layout,clean};
}());
