// The cover: a leaf that lies over page 1 until the notebook is opened, and swings back over it
// when you spin the wheel past page 1.

import { el, reducedMotion, tuck } from "./motion.js";

const OPEN_MS = 950;
const SWING = "cubic-bezier(0.45, 0.05, 0.25, 1)";

/**
 * @param {object} o
 * @param {HTMLElement} o.root
 * @param {HTMLElement} o.book  the .nb-book element
 * @param {boolean} o.phone
 * @param {() => void} o.onTap   the visitor tapped, clicked or swiped the cover
 */
export function createCover({ root, book, phone, onTap }) {
  let leaf = null;
  let timer = 0;
  let closed = false;

  function build({ swingShut }) {
    leaf = el("div", "nb-leaf cover");
    const front = el("div", "face front cover-front");
    front.innerHTML = `<i class="cover-stitch"></i><i class="cover-band"></i><span class="cover-label">David Lybeck</span><button type="button" class="cover-open">open</button>`;
    const back = el("div", "face back");
    if (!phone) {
      // on desktop the cover's inside is the left page, so it lands on the left as the book opens
      const left = book.querySelector(".nb-page.l .nb-in");
      const inside = el("div", "nb-in");
      inside.append(...[...left.childNodes].map((n) => n.cloneNode(true)));
      back.append(inside);
    }
    leaf.append(front, back);
    book.append(leaf);

    let startX = null;
    leaf.addEventListener("pointerdown", (e) => { e.stopPropagation(); startX = e.clientX; });
    leaf.addEventListener("pointerup", (e) => {
      e.stopPropagation();
      const swiped = startX !== null && e.clientX - startX < -30;
      startX = null;
      if (swiped) onTap();
    });
    leaf.addEventListener("click", (e) => { e.stopPropagation(); onTap(); });

    if (swingShut && !reducedMotion()) {
      if (phone) tuck(leaf, -180, 0, OPEN_MS - 50, SWING).onfinish = (e) => e.target.cancel();
      else {
        leaf.style.transform = "rotateY(-180deg)";
        void leaf.offsetWidth;
        leaf.style.transition = `transform ${OPEN_MS - 50}ms ${SWING}`;
        leaf.style.transform = "";
      }
    }
  }

  return {
    get closed() { return closed; },
    /** Lay the cover over the book (when it first loads, or when the wheel goes back past page 1). */
    close({ animate = false } = {}) {
      clearTimeout(timer);
      book.querySelectorAll(":scope > .cover").forEach((n) => n.remove());
      closed = true;
      root.classList.add("is-closed");
      build({ swingShut: animate });
    },
    /** Swing the cover open to the left. */
    open() {
      closed = false;
      clearTimeout(timer);
      root.classList.remove("is-closed");
      const gone = leaf;
      leaf = null;
      if (!gone) return;
      if (reducedMotion()) { gone.remove(); return; }
      if (phone) tuck(gone, 0, -180, OPEN_MS, SWING);
      else {
        gone.style.transition = `transform ${OPEN_MS}ms ${SWING}`;
        gone.style.transform = "rotateY(-180deg)";
      }
      timer = setTimeout(() => gone.remove(), OPEN_MS + 30);
    },
    destroy() {
      clearTimeout(timer);
      book.querySelectorAll(":scope > .cover").forEach((n) => n.remove());
    },
  };
}
