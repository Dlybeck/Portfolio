// The cover: a leaf that lies over page 1 until the notebook is opened, and swings back over it
// when you spin the wheel past page 1.

import { el, reducedMotion, tuck } from "./motion.js";
import { stickersHtml, wireStickers } from "./stickers/index.js";

// One timing for the whole opening: the cover swinging on its spine and the book sliding to its open spot.
// The same two values are set on the page as --nb-open-ms and --nb-open-ease, which the book's slide uses.
const OPEN_MS = 800;
const SWING = "cubic-bezier(0.22, 0.7, 0.25, 1)";
const FADE_MS = 260; // with reduced motion the cover fades instead of swinging

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
  let moving = 0;
  let closed = false;
  root.style.setProperty("--nb-open-ms", `${OPEN_MS}ms`);
  root.style.setProperty("--nb-open-ease", SWING);
  // While the cover is shut, what lies under it must not be reachable by keyboard or screen reader.
  const covered = () => book.querySelectorAll(":scope > .nb-page, :scope > .nb-ear");
  const setCovered = (on) => covered().forEach((n) => { n.inert = on; });

  function backFace() {
    const left = book.querySelector(".nb-page.l .nb-in");
    const inside = el("div", "nb-in");
    inside.append(...[...left.childNodes].map((n) => n.cloneNode(true)));
    return inside;
  }

  function build({ swingShut }) {
    leaf = el("div", "nb-leaf cover");
    const front = el("div", "face front cover-front");
    front.innerHTML = `<i class="cover-stitch"></i>${stickersHtml()}<span class="cover-label">David Lybeck</span><i class="cover-band"></i><button type="button" class="cover-open">open</button>`;
    const back = el("div", "face back");
    // on desktop the cover's inside is the left page, so it lands on the left as the book opens
    if (!phone) back.append(backFace());
    leaf.append(front, back);
    book.append(leaf);
    wireStickers(front);

    // A swipe to the left opens the cover wherever it ends; one that starts on a sticker belongs to the sticker.
    let startX = null;
    let onSticker = false;
    leaf.addEventListener("pointerdown", (e) => { onSticker = Boolean(e.target.closest(".wd")); startX = onSticker ? null : e.clientX; }, true);
    leaf.addEventListener("pointerup", (e) => {
      const swiped = startX !== null && e.clientX - startX < -30;
      startX = null;
      if (swiped) onTap();
    }, true);
    leaf.addEventListener("pointerdown", (e) => e.stopPropagation());
    leaf.addEventListener("pointerup", (e) => e.stopPropagation());
    leaf.addEventListener("click", (e) => {
      e.stopPropagation();
      if (!onSticker) onTap(); // a press that began on a sticker and ended elsewhere is not a tap on the cover
    });

    if (!swingShut) return;
    if (reducedMotion()) {
      // a simple cross-fade: the cover appears over the book in place, with no swing and no slide
      leaf.style.opacity = "0";
      void leaf.offsetWidth;
      leaf.style.transition = `opacity ${FADE_MS}ms ease`;
      leaf.style.opacity = "1";
      return;
    }
    // closing is the opening played backwards: the leaf starts lying open on the left and swings shut on its spine
    inMotion(OPEN_MS);
    if (phone) tuck(leaf, -180, 0, OPEN_MS, SWING).onfinish = (e) => e.target.cancel();
    else {
      leaf.style.transform = "rotateY(-180deg)";
      void leaf.offsetWidth;
      leaf.style.transition = `transform ${OPEN_MS}ms ${SWING}`;
      leaf.style.transform = "";
    }
  }

  /** The book is mid-move: the real left page waits until it settles while the tabs slide with the book. */
  function inMotion(ms) {
    root.classList.add("is-opening");
    clearTimeout(moving);
    moving = setTimeout(() => root.classList.remove("is-opening"), ms + 30);
  }

  return {
    get closed() { return closed; },
    /** Lay the cover over the book (when it first loads, or when the wheel goes back past page 1). */
    close({ animate = false } = {}) {
      clearTimeout(timer);
      book.querySelectorAll(":scope > .cover").forEach((n) => n.remove());
      closed = true;
      root.classList.add("is-closed");
      setCovered(true);
      build({ swingShut: animate });
    },
    /** Swing the cover open to the left. */
    open() {
      closed = false;
      clearTimeout(timer);
      root.classList.remove("is-closed");
      setCovered(false);
      const gone = leaf;
      leaf = null;
      if (!gone) return;
      if (!phone) gone.querySelector(".back").replaceChildren(backFace()); // the page now showing, not the one it was built over
      if (reducedMotion()) {
        gone.style.transition = `opacity ${FADE_MS}ms ease`;
        gone.style.opacity = "0";
        timer = setTimeout(() => gone.remove(), FADE_MS + 30);
        return;
      }
      inMotion(OPEN_MS);
      if (phone) tuck(gone, 0, -180, OPEN_MS, SWING);
      else {
        gone.style.transition = `transform ${OPEN_MS}ms ${SWING}`;
        gone.style.transform = "rotateY(-180deg)";
      }
      timer = setTimeout(() => gone.remove(), OPEN_MS + 30);
    },
    destroy() {
      clearTimeout(timer);
      clearTimeout(moving);
      root.classList.remove("is-opening");
      setCovered(false);
      book.querySelectorAll(":scope > .cover").forEach((n) => n.remove());
    },
  };
}
