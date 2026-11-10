// The wheel's tooltip: a small handwritten bubble that says what the wheel is for while the cover is still shut.
// It goes away for good when the visitor touches the wheel or the cover opens.

const WORDS = "spin the wheel to open";

/**
 * @param {HTMLElement} root  the #notebook element
 * @param {{ delay?: number }} [o]
 * @returns {{ show(): void, hide(): void }}
 */
export function createWheelTip(root, { delay = 500 } = {}) {
  const wheel = root.querySelector(".wheel");
  let tip = null;
  let timer = 0;
  let wanted = false; // asked for and not yet put away: it survives the book being rebuilt
  const gestures = ["pointerdown", "wheel", "keydown"];
  const classes = new MutationObserver(() => { if (!root.classList.contains("is-closed")) hide(); });

  function hide() {
    wanted = false;
    clearTimeout(timer);
    classes.disconnect();
    for (const type of gestures) wheel?.removeEventListener(type, hide, true);
    if (!tip) return;
    const gone = tip;
    tip = null;
    gone.classList.add("is-gone");
    setTimeout(() => gone.remove(), 400);
  }

  return {
    hide,
    get wanted() { return wanted; },
    /** Show it after a short pause, and only while the cover is shut. */
    show() {
      if (!wheel || tip) return;
      wanted = true;
      timer = setTimeout(() => {
        if (!root.classList.contains("is-closed")) return;
        tip = document.createElement("div");
        tip.className = "wheel-tip";
        tip.setAttribute("aria-hidden", "true"); // the wheel is already labelled "Turn the pages"
        tip.textContent = WORDS;
        wheel.append(tip);
        classes.observe(root, { attributes: true, attributeFilter: ["class"] });
        for (const type of gestures) wheel.addEventListener(type, hide, { capture: true, passive: true });
      }, delay);
    },
  };
}
