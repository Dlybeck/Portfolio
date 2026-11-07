// A gentle hint that the stickers do something: one at a time, every few seconds, a sticker plays a small, quiet
// version of its own tap animation (pure CSS classes: it never runs the sticker's real action, makes no sound and
// goes nowhere). It stops for good once the visitor touches any sticker, waits while things are moving, and is off
// with reduced motion.

import { reducedMotion } from "./common.js";

/** [selector, how long its hint plays in ms], in the order they take turns. */
export const HINTED = [
  [".wd-name", 1100], [".wd-ball", 700], [".wd-now", 500], [".wd-p12", 1500], [".wd-hike", 1300],
  [".wd-pal-raccoon", 1000], [".wd-puzzle", 900], [".wd-mine", 800],
];
const FIRST_MS = 3200;
const EVERY_MS = [4000, 6000]; // between hints
const SCROLL_QUIET_MS = 900;

let touched = false; // the visitor has used a sticker: no more hints this visit

/**
 * Start the cycle on a cover. Returns a function that stops it.
 * @param {HTMLElement} cover  the cover's front, holding the stickers
 * @param {() => boolean} alive  false once the cover has left the page
 */
export function startHints(cover, alive) {
  if (touched || reducedMotion()) return () => {};
  const root = cover.closest(".nb");
  let timer = 0;
  let playing = null;
  let next = 0;
  let lastScroll = -Infinity;
  let done = false;

  const clear = () => { clearTimeout(timer); timer = 0; };
  const stop = () => {
    done = true;
    clear();
    if (playing) playing.classList.remove("hint");
    cover.removeEventListener("pointerdown", onTouch, true);
    cover.removeEventListener("keydown", onKey, true);
    removeEventListener("scroll", onScroll, true);
    document.removeEventListener("visibilitychange", onVisibility);
  };
  const onTouch = (e) => { if (e.target.closest?.(".wd")) { touched = true; stop(); } };
  const onKey = (e) => { if ((e.key === "Enter" || e.key === " ") && e.target.closest?.(".wd")) { touched = true; stop(); } };
  const onScroll = () => { lastScroll = performance.now(); };
  const onVisibility = () => {
    if (done) return;
    clear();
    if (!document.hidden) schedule(EVERY_MS[0]); // come back to it quietly
  };
  cover.addEventListener("pointerdown", onTouch, true);
  cover.addEventListener("keydown", onKey, true);
  addEventListener("scroll", onScroll, true);
  document.addEventListener("visibilitychange", onVisibility);

  function schedule(ms) {
    clear();
    timer = setTimeout(tick, ms);
  }
  const later = () => schedule(EVERY_MS[0] + Math.random() * (EVERY_MS[1] - EVERY_MS[0]));

  function tick() {
    if (done) return;
    if (!alive() || !root || (!root.classList.contains("is-closed"))) { stop(); return; } // the cover is open (or gone)
    const busy = document.hidden || root.classList.contains("is-opening") || performance.now() - lastScroll < SCROLL_QUIET_MS || reducedMotion();
    if (busy) { later(); return; }
    // the next sticker that is there and not being held
    for (let tries = 0; tries < HINTED.length; tries++) {
      const [selector, ms] = HINTED[next++ % HINTED.length];
      const el = cover.querySelector(selector);
      if (!el || el.matches(":active, .held")) continue;
      playing = el;
      el.classList.remove("hint");
      void el.offsetWidth;
      el.classList.add("hint");
      setTimeout(() => { el.classList.remove("hint"); if (playing === el) playing = null; }, ms + 60);
      break;
    }
    later();
  }
  schedule(FIRST_MS);
  return stop;
}
