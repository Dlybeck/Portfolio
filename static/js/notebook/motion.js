// Motion helpers shared by the book, the wheel and the cover.

const query = window.matchMedia("(prefers-reduced-motion: reduce)");

/** True when the visitor asked for less motion. Checked at the moment of use. */
export const reducedMotion = () => query.matches;

/** Tiny DOM helper: el("div", "nb-leaf is-flying", {style...}). */
export function el(tag, className = "", attrs = {}) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  for (const [key, value] of Object.entries(attrs)) node.setAttribute(key, value);
  return node;
}

const TUCK_KEYS = [[-90, 1], [-100, 0.34], [-120, 0.12], [-150, 0.07], [-180, 0.055]];

function tuckScale(angle) {
  const a = Math.max(-180, Math.min(0, angle));
  if (a >= -90) return 1;
  for (let i = 1; i < TUCK_KEYS.length; i++) {
    if (a >= TUCK_KEYS[i][0]) {
      const [a0, s0] = TUCK_KEYS[i - 1];
      const [a1, s1] = TUCK_KEYS[i];
      return s0 + ((s1 - s0) * (a - a0)) / (a1 - a0);
    }
  }
  return TUCK_KEYS[TUCK_KEYS.length - 1][1];
}

/**
 * Swing a leaf from one angle to another. On a phone the book fills the screen, so a page
 * that swung past the spine would leave it. Instead the page tucks behind the left edge:
 * past 90 degrees it narrows to a thin page edge in the gutter.
 */
export function tuck(node, from, to, duration, easing) {
  const frames = [];
  const steps = 30;
  for (let i = 0; i <= steps; i++) {
    const angle = from + ((to - from) * i) / steps;
    frames.push({ transform: `rotateY(${angle}deg) scaleX(${tuckScale(angle)})` });
  }
  node.style.transition = "none";
  return node.animate(frames, { duration, easing, fill: "forwards" });
}
