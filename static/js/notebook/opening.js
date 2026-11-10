// A first visit to "/" opens the notebook on its last page, spins the wheel back through every page and swings the
// cover shut, then a tooltip points at the wheel. It plays once per visitor (remembered in localStorage), never for a
// deep link, and not at all with reduced motion (the cover just shows the tooltip). A touch, scroll or key takes over
// at once. The address stays "/" throughout and the spin adds nothing to the history.

import { reducedMotion } from "./motion.js";

const SEEN = "nb-opening-seen";
const PAUSE_MS = 900; // the last page sits still first, so the visitor sees an open notebook
const SPIN_MS = 2600; // how long the spin takes, whatever the number of pages
const SETTLE_MS = 900; // the cover finishing its swing before the tooltip appears
const MODIFIERS = ["Shift", "Control", "Alt", "Meta", "AltGraph", "CapsLock"];
const DRAG_PX = 12; // a press on a link that moves further than this is a swipe, not a click
const TAKEOVER = ["pointerdown", "wheel", "keydown", "touchstart"];

export function hasSeenOpening() {
  try { return localStorage.getItem(SEEN) === "1"; } catch { return false; } // storage can be blocked: then it plays every time
}
export function rememberOpening() {
  try { localStorage.setItem(SEEN, "1"); } catch { /* blocked */ }
}

/**
 * Run the spin. Returns `stop()`, which ends it silently (the book is rebuilt, or another navigation took over).
 * @param {{ wheel: { glideTo(id: string, ms: number, done: (arrived: boolean) => void): void, cancelGlide(): void },
 *           tip: { show(): void }, finish: () => void }} o
 */
export function playOpening({ wheel, tip, finish }) {
  let over = false;
  let timer = 0;
  const end = (showTip) => {
    if (over) return;
    over = true;
    clearTimeout(timer);
    for (const type of TAKEOVER) removeEventListener(type, take, true);
    unwatch();
    document.removeEventListener("visibilitychange", start);
    finish();
    if (showTip) tip.show(); // (it only appears if the cover is shut by then)
  };
  let drag = null;
  const watchDrag = (e) => {
    const at = e.touches?.[0] ?? e;
    drag = { x: at.clientX, y: at.clientY };
    addEventListener("pointermove", moved, { capture: true, passive: true });
    addEventListener("pointerup", unwatch, { capture: true, once: true });
    addEventListener("pointercancel", unwatch, { capture: true, once: true });
  };
  const unwatch = () => { drag = null; removeEventListener("pointermove", moved, true); };
  const moved = (e) => {
    if (drag && Math.hypot(e.clientX - drag.x, e.clientY - drag.y) > DRAG_PX) { unwatch(); take(e); } // the press became a swipe
  };
  // a visitor who has taken over by touching the wheel itself needs no tip about it
  const take = (e) => {
    // a bare modifier or a browser shortcut (Shift, Cmd+L, Ctrl+T) is not a deliberate touch of the book
    if (e.type === "keydown" && (e.ctrlKey || e.metaKey || e.altKey || MODIFIERS.includes(e.key))) return;
    // Pressing a link is the link's own navigation: its click (go() or home() in main.js) ends the opening and writes the one
    // entry. Only Enter and Space activate a focused link; any other key, or a press that turns into a drag, is the visitor's.
    const link = e.target?.closest?.("[data-open], [data-home]");
    if (link && e.type === "keydown" && (e.key === "Enter" || e.key === " ")) return;
    if (link && (e.type === "pointerdown" || e.type === "touchstart")) { watchDrag(e); return; }
    wheel.cancelGlide();
    end(!e.target?.closest?.(".wheel"));
  };
  for (const type of TAKEOVER) addEventListener(type, take, { capture: true, passive: true });

  function start() {
    if (over) return;
    if (document.hidden) { document.addEventListener("visibilitychange", start, { once: true }); return; } // wait until it can be seen
    timer = setTimeout(() => {
      wheel.glideTo("cover", SPIN_MS, (arrived) => {
        if (!arrived) return; // a takeover: `take` below decides about the tip and ends the opening
        timer = setTimeout(() => end(true), SETTLE_MS);
      });
    }, PAUSE_MS);
  }
  start();
  return () => { over = true; clearTimeout(timer); unwatch(); for (const type of TAKEOVER) removeEventListener(type, take, true); document.removeEventListener("visibilitychange", start); };
}

/**
 * Once, on a first visit: the first time the cover has opened and settled, the next-page corner lifts a little and
 * settles (CSS .nb--lift). It says the corner is there without becoming a second tooltip.
 */
export function liftCornerOnce(root) {
  if (reducedMotion()) return; // the corner does not move with reduced motion, so there is nothing to wait for
  let sawShut = false;
  const watch = new MutationObserver(() => {
    const shut = root.classList.contains("is-closed");
    if (shut) sawShut = true;
    if (!sawShut || shut || root.classList.contains("is-opening")) return;
    watch.disconnect();
    root.classList.add("nb--lift");
    const done = (e) => {
      if (e.animationName !== "ear-lift") return;
      root.classList.remove("nb--lift");
      root.removeEventListener("animationend", done, true);
    };
    root.addEventListener("animationend", done, true);
  });
  watch.observe(root, { attributes: true, attributeFilter: ["class"] });
  sawShut = root.classList.contains("is-closed");
}
