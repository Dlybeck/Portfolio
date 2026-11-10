// A first visit to "/" opens the notebook on its last page, spins the wheel back through every page and swings the
// cover shut, then a tooltip points at the wheel. It plays once per visitor (remembered in localStorage), never for a
// deep link, and not at all with reduced motion (the cover just shows the tooltip). A touch, scroll or key takes over
// at once. The address stays "/" throughout and the spin adds nothing to the history.

const SEEN = "nb-opening-seen";
const PAUSE_MS = 900; // the last page sits still first, so the visitor sees an open notebook
const SPIN_MS = 2600; // how long the spin takes, whatever the number of pages
const SETTLE_MS = 900; // the cover finishing its swing before the tooltip appears
const MODIFIERS = ["Shift", "Control", "Alt", "Meta", "AltGraph", "CapsLock"];
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
    document.removeEventListener("visibilitychange", start);
    finish();
    if (showTip) tip.show(); // (it only appears if the cover is shut by then)
  };
  // a visitor who has taken over by touching the wheel itself needs no tip about it
  const take = (e) => {
    // a bare modifier or a browser shortcut (Shift, Cmd+L, Ctrl+T) is not a deliberate touch of the book
    if (e.type === "keydown" && (e.ctrlKey || e.metaKey || e.altKey || MODIFIERS.includes(e.key))) return;
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
  return () => { over = true; clearTimeout(timer); for (const type of TAKEOVER) removeEventListener(type, take, true); document.removeEventListener("visibilitychange", start); };
}

/**
 * Once, on a first visit: the first time the cover has opened and settled, the next-page corner lifts a little and
 * settles (CSS .nb--lift). It says the corner is there without becoming a second tooltip.
 */
export function liftCornerOnce(root) {
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
