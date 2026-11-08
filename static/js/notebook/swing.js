// One driver for the desktop cover and everything behind it.
//
// The cover swings on a rotateY with perspective, so its free edge does not travel along the easing curve: it moves with
// cos(angle) and the perspective divide. Anything that has to stay under that edge (the brown back board) or move with
// the swing (the book's slide) therefore cannot be given its own CSS transition. Instead one requestAnimationFrame loop
// turns the clock into eased progress, derives the cover's angle from it, and in the same frame writes the cover's
// transform, the book's slide and the back board's clip from that one angle. Nothing else animates these.

/** cubic-bezier(x1, y1, x2, y2) as a function of time (0..1) returning progress (0..1), like a CSS easing. */
export function bezier(x1, y1, x2, y2) {
  const axis = (a, b, t) => 3 * a * (1 - t) ** 2 * t + 3 * b * (1 - t) * t * t + t ** 3;
  return (x) => {
    if (x <= 0) return 0;
    if (x >= 1) return 1;
    let lo = 0;
    let hi = 1;
    let t = x;
    for (let i = 0; i < 24; i++) {
      const at = axis(x1, x2, t);
      if (Math.abs(at - x) < 1e-5) break;
      if (at < x) lo = t; else hi = t;
      t = (lo + hi) / 2;
    }
    return axis(y1, y2, t);
  };
}

/** Parse a CSS `cubic-bezier(a, b, c, d)` string; falls back to the notebook's ease-in-out. */
export function easeFrom(text) {
  const n = /cubic-bezier\(([^)]+)\)/.exec(text || "")?.[1].split(",").map(parseFloat);
  return n && n.length === 4 && n.every(Number.isFinite) ? bezier(...n) : bezier(0.65, 0, 0.35, 1);
}

// The back board is a hair bigger than the pages (see .nb-back); these are its margins in px.
const BOARD = { top: 10, right: 12, bottom: 12, left: 12 };
const RIM_SHUT = 2; // how far the board shows left of the spine while the book is shut
const RIM_OPEN = BOARD.left; // and how far past the left page once it is open

/**
 * The cover's visible free edge, as a distance from the spine in px (positive to the right, negative to the left).
 * `half` is the cover's width, `open` its progress 0 (shut) to 1 (flat on the left), `perspective` the book's.
 * A point at the free edge sits at x = half·cos(a) and, nearer the viewer, z = half·sin(a); the projection scales x by P / (P - z).
 */
export function edgeOffset(half, open, perspective) {
  const a = Math.PI * open;
  return (half * Math.cos(a) * perspective) / (perspective - half * Math.sin(a));
}

/**
 * The left edge of the brown board's visible part, from the spine: it pokes a little past the cover's edge so it reads
 * as the board under it, with that rim growing from 2px when shut to 12px (the board's own margin) when open.
 */
export function boardEdge(half, open, perspective) {
  const e = edgeOffset(half, open, perspective);
  if (e >= 0) return -RIM_SHUT;
  return e - RIM_SHUT - (RIM_OPEN - RIM_SHUT) * Math.min(1, -e / half);
}

/**
 * @param {object} o
 * @param {HTMLElement} o.book  the .nb-book (perspective, slide)
 * @param {HTMLElement} o.back  the .nb-back board
 * @param {(x: number) => number} o.ease
 * @param {number} o.ms  the duration of a whole opening or shutting
 */
export function createSwing({ book, back, ease, ms }) {
  let frame = 0;
  let open = 1; // where the last frame put the cover: 0 shut .. 1 open

  const perspective = () => parseFloat(getComputedStyle(book).perspective) || 2400;

  function paint(leaf, p, geo) {
    const edge = geo.half + boardEdge(geo.half, p, geo.perspective); // from the book's left edge
    open = p;
    leaf.style.transform = p >= 1 ? "rotateY(-180deg)" : p <= 0 ? "" : `rotateY(${-180 * p}deg)`;
    book.style.transform = `translateX(${(-0.25 * geo.bw * (1 - p)).toFixed(3)}px)`;
    // the board is full size; clipping its left side keeps its edge where the cover's is
    const shadow = RIM_OPEN * Math.min(1, Math.max(0, -edgeOffset(geo.half, p, geo.perspective) / geo.half));
    back.style.clipPath = `inset(${-BOARD.top}px ${-BOARD.right}px ${-BOARD.bottom}px ${(edge + BOARD.left - shadow).toFixed(3)}px)`;
  }

  function stop() {
    cancelAnimationFrame(frame);
    frame = 0;
  }

  function release(leaf) {
    book.style.removeProperty("transform");
    back.style.removeProperty("clip-path");
    if (leaf) leaf.style.removeProperty("transform");
  }

  return {
    /** The progress the cover is at now (1 when nothing is moving and it is open, 0 when it is shut). */
    get moving() { return frame !== 0; },
    get progress() { return open; },
    /**
     * Run the cover from `from` to `to` (0 shut, 1 open). A move cut short by another starts the next from where it stopped.
     * Every frame sets the cover's transform, the book's slide and the board's clip from the same angle.
     */
    run(leaf, from, to, onDone) {
      const start = frame !== 0 ? open : from;
      stop();
      const geo = { bw: book.offsetWidth, half: book.offsetWidth / 2, perspective: perspective() };
      const span = Math.abs(to - start) || 1; // a move cut short takes the same pace, not the whole time
      const duration = ms * span;
      let t0 = null;
      paint(leaf, start, geo);
      const tick = (now) => {
        t0 ??= now;
        const t = Math.min(1, (now - t0) / duration);
        const eased = ease(t);
        paint(leaf, start + (to - start) * eased, geo);
        if (t < 1) { frame = requestAnimationFrame(tick); return; }
        frame = 0;
        release(leaf);
        onDone?.();
      };
      frame = requestAnimationFrame(tick);
    },
    /** Stop moving and hand the geometry back to the stylesheet's resting state. */
    cancel(leaf) {
      stop();
      release(leaf);
    },
  };
}
