// The book: puts the server-written pages onto one page (phone) or a two-page spread (desktop)
// and turns them. Several leaves can be in the air at once, so a fast wheel riffles through the book.

import { insideCover } from "./inside.js";
import { el, reducedMotion, tuck } from "./motion.js";

const TURN_MS = 720;
const EASE = "cubic-bezier(0.4, 0.1, 0.3, 1)";
const MAX_IN_AIR = 8;
const SWIPE_MIN = 56; // px sideways
const SWIPE_RATIO = 2; // and at least twice as far sideways as up or down

/**
 * @param {object} o
 * @param {HTMLElement} o.root      the #notebook element
 * @param {object} o.data           the table of contents (core/notebook.py client_data)
 * @param {Map<string, HTMLElement>} o.sources  page id -> its <article> as written by the server
 * @param {"phone"|"desktop"} o.mode
 * @param {(id: string) => void} o.onView  called when a page is showing
 * @param {(side: HTMLElement) => void} [o.onFill]  a page was written onto a side of the book
 * @param {(sides: HTMLElement[]) => void} [o.onSettled]  the book has stopped turning
 */
export function createBook({ root, data, sources, mode, onView, onFill, onSettled }) {
  const phone = mode === "phone";
  const order = phone ? data.phone : data.desktop;
  const total = order.length;

  root.insertAdjacentHTML(
    "beforeend",
    `<div class="nb-book" role="main" aria-label="David Lybeck's notebook">
       <div class="nb-back"></div>
       ${phone
         ? `<div class="nb-page one"><div class="nb-in" role="region" tabindex="0"></div></div>`
         : `<div class="nb-page l"><div class="nb-in" role="region" tabindex="0"></div></div><div class="nb-page r"><div class="nb-in" role="region" tabindex="0"></div></div><div class="nb-gutter"></div>`}
       <div class="nb-leaf"><div class="face front"></div><div class="face back"></div></div>
       <div class="nb-band"></div>
       <span class="nb-pn lft"></span><span class="nb-pn rgt"></span>
       <button type="button" class="nb-ear prev" aria-label="Previous page"></button>
       <button type="button" class="nb-ear next" aria-label="Next page"></button>
       <span class="nb-hint-flip" aria-hidden="true">flip</span>
     </div>
     <p class="sr-only" role="status" aria-live="polite" id="nb-status"></p>`,
  );
  const book = root.querySelector(".nb-book");
  const status = root.querySelector("#nb-status");
  const inL = book.querySelector(".nb-page .nb-in");
  const inR = phone ? null : book.querySelector(".nb-page.r .nb-in");
  const pnL = book.querySelector(".nb-pn.lft");
  const pnR = book.querySelector(".nb-pn.rgt");
  const prev = book.querySelector(".prev");
  const next = book.querySelector(".next");
  const hint = book.querySelector(".nb-hint-flip");
  book.querySelector(".nb-leaf").remove(); // leaves are made on demand

  let current = null;
  let seq = 0;
  let inAir = 0;
  const sideSeq = { L: 0, R: 0 };

  // ---------- which page is on which side ----------
  /** The list pages are not spreads on desktop: a list folds into its first story. */
  const normalize = (id) => (phone || order.includes(id) ? id : (data.lists[id] || [data.desktop[0]])[0]);

  function wrap(nodes, { cur } = {}) {
    const page = el("div", "page");
    for (const node of nodes) {
      const copy = node.cloneNode(true);
      for (const keep of [copy, ...copy.querySelectorAll("[id]")]) {
        if (keep.id) {
          keep.dataset.id = keep.id;
          keep.removeAttribute("id");
        }
      }
      page.append(copy);
    }
    if (cur) page.querySelector(`[data-page-link="${cur}"]`)?.classList.add("cur");
    return page;
  }
  const sectionsOf = (id) => [...sources.get(id).children];

  /** The element(s) a page is made of: one on a phone, a left and a right on desktop. */
  function compose(id) {
    if (phone) return [wrap(sectionsOf(id))];
    const info = data.pages[id];
    // like a real notebook: the first page sits alone on the right of the inside front cover, and the last page
    // sits alone on the left of the inside back cover; both covers are bare, ready for stickers
    if (info.layout === "front") return [insideCover("front"), wrap(sectionsOf(id))];
    if (info.layout === "back") return [wrap(sectionsOf(id)), insideCover("back")];
    if (info.layout === "split") {
      const parts = sectionsOf(id);
      const at = info.split ?? 1;
      return [wrap(parts.slice(0, at)), wrap(parts.slice(at))];
    }
    // "list": the section's list of stories on the left, this story on the right
    return [wrap(sectionsOf(info.section), { cur: id }), wrap(sectionsOf(id))];
  }

  const numberOf = (id) => order.indexOf(normalize(id)) + 1;
  const sectionTab = (id) => data.sections.find((s) => s.id === data.pages[id].section).tab;

  function fill(side, page) {
    const target = side === "L" ? inL : inR;
    stopWatching(target);
    target.replaceChildren(page);
    target.scrollTop = 0;
    for (const slot of target.querySelectorAll("[data-pg-for]")) slot.textContent = `p.${numberOf(slot.dataset.pgFor)}`;
    onFill?.(target);
    settleSoon();
  }

  // Heavy things (3D models) wait until the book has been still for a moment.
  let settleTimer = 0;
  function settleSoon() {
    clearTimeout(settleTimer);
    settleTimer = setTimeout(() => { if (inAir === 0) onSettled?.([inL, inR]); }, 320);
  }

  /** A copy of a page for a turning leaf: pictures and text only, no live 3D models. */
  function lookalike(page) {
    const copy = page.cloneNode(true);
    for (const live of copy.querySelectorAll("model-viewer")) live.replaceWith(el("div", "model-ph"));
    return copy;
  }

  /**
   * What belongs to one side of the book: the left side's folio and whether it is the inside front cover, the right side's page
   * number and whether it is the inside back cover. They follow the page that is actually on that side, so while a leaf is in the
   * air they change when that side's page does (the leaf's start side at once, its landing side when it lands), never early.
   * (A folio or a corner fold that shows up over a bare inside cover before the page has landed was this.)
   */
  function sideChrome(side, id) {
    if (phone) return;
    const layout = data.pages[id].layout;
    if (side === "L") {
      root.classList.toggle("is-first-spread", layout === "front");
      pnL.textContent = sectionTab(id);
    } else {
      root.classList.toggle("is-last-spread", layout === "back");
      pnR.textContent = `p.${order.indexOf(id) + 1}`;
    }
  }

  /** The book-wide state of a view; pass { sides: false } when a turn will update each side as its page changes. */
  function chrome(id, { sides = true } = {}) {
    const i = order.indexOf(id);
    root.dataset.page = id;
    root.dispatchEvent(new CustomEvent("nb:view", { detail: id }));
    const title = data.pages[id].title;
    const layout = data.pages[id].layout;
    inL.setAttribute("aria-label", phone ? title : layout === "front" ? "Inside front cover" : `${title}, left page`);
    inR?.setAttribute("aria-label", layout === "back" ? "Inside back cover" : `${title}, right page`);
    root.classList.toggle("is-turned", i > 0);
    prev.disabled = i <= 0;
    next.disabled = i >= total - 1;
    if (phone) pnR.textContent = `p.${i + 1} of ${total}`;
    else if (sides) {
      sideChrome("L", id);
      sideChrome("R", id);
    }
  }

  // Fonts and pictures arriving can move the part of the page we scrolled to. For a moment after
  // arriving we keep it in place, unless the visitor has scrolled on their own.
  const watching = new Map();
  function stopWatching(scroller) {
    watching.get(scroller)?.stop();
    watching.delete(scroller);
  }
  function scrollToAnchor(anchor) {
    if (!anchor) return;
    for (const scroller of [inL, inR]) {
      const target = scroller?.querySelector(`[data-id="${anchor}"]`);
      if (!target) continue;
      stopWatching(scroller);
      const place = () => {
        const box = scroller.getBoundingClientRect();
        scroller.scrollTo({ top: scroller.scrollTop + target.getBoundingClientRect().top - box.top - 14, behavior: "instant" });
      };
      place();
      // anything the visitor does with the page ends the watch; the browser's own scroll adjustments do not
      const done = () => stopWatching(scroller);
      const gestures = ["wheel", "touchstart", "pointerdown", "keydown"];
      for (const type of gestures) scroller.addEventListener(type, done, { once: true, passive: true });
      const observer = new ResizeObserver(place);
      observer.observe(scroller.firstElementChild);
      const timer = setTimeout(done, 2500);
      watching.set(scroller, { stop() { observer.disconnect(); clearTimeout(timer); for (const type of gestures) scroller.removeEventListener(type, done); } });
    }
  }

  function announce(id) {
    status.textContent = `${data.pages[id].title}, page ${order.indexOf(id) + 1} of ${total}`;
  }

  function paint(id, anchor) {
    const [l, r] = compose(id);
    fill("L", l);
    if (r) fill("R", r);
    chrome(id);
    scrollToAnchor(anchor);
  }

  // ---------- turning ----------
  /**
   * Turn to a page. A normal turn takes TURN_MS; the wheel passes a shorter time while it spins,
   * so each page it passes flips live.
   */
  function turn(to, { duration = TURN_MS, anchor, silent = false } = {}) {
    const id = normalize(to);
    if (id === current) {
      if (anchor) scrollToAnchor(anchor);
      else for (const scroller of [inL, inR]) scroller?.scrollTo({ top: 0, behavior: "instant" });
      return;
    }
    const forward = current === null || order.indexOf(id) > order.indexOf(current);
    const from = current;
    current = id;
    hint.style.opacity = 0;
    if (!silent) onView(id);
    announce(id);

    if (from === null || reducedMotion() || duration <= 0 || inAir >= MAX_IN_AIR) {
      seq += 1;
      sideSeq.L = sideSeq.R = seq;
      paint(id, anchor);
      return;
    }

    const mine = ++seq;
    const [nl, nr] = compose(id);
    const face = (page) => {
      const wrapper = el("div", "nb-in");
      wrapper.append(page);
      return wrapper;
    };
    const leaf = el("div", "nb-leaf is-flying is-riffle");
    const front = el("div", "face front");
    const back = el("div", "face back");
    leaf.append(front, back);
    let startSide = null;
    let landSide = null;
    let angleFrom = 0;
    let angleTo = -180;
    const oldL = lookalike(inL.firstElementChild);
    const oldR = inR && lookalike(inR.firstElementChild);

    if (phone) {
      Object.assign(leaf.style, { left: 0, right: 0, transformOrigin: "left center" });
      if (forward) {
        front.append(face(oldL));
        startSide = "L";
      } else {
        front.append(face(nl));
        landSide = "L";
        angleFrom = -180;
        angleTo = 0;
      }
    } else if (forward) {
      Object.assign(leaf.style, { left: "50%", right: 0, transformOrigin: "left center" });
      front.classList.add("r-face");
      front.append(face(oldR));
      back.append(face(nl));
      startSide = "R";
      landSide = "L";
    } else {
      Object.assign(leaf.style, { left: 0, right: "50%", transformOrigin: "right center" });
      front.append(face(oldL));
      back.classList.add("r-face");
      back.append(face(nr));
      startSide = "L";
      landSide = "R";
      angleTo = 180;
    }
    leaf.style.zIndex = forward ? 60 - (mine % 50) : 10 + (mine % 50);

    chrome(id, { sides: false });
    if (startSide) {
      sideSeq[startSide] = mine;
      fill(startSide, startSide === "L" ? nl : nr);
      sideChrome(startSide, id);
    }
    book.append(leaf);
    inAir += 1;
    leaf.style.transform = `rotateY(${angleFrom}deg)`;
    void leaf.offsetWidth;
    if (phone) tuck(leaf, angleFrom, angleTo, duration, EASE);
    else {
      leaf.style.transition = `transform ${duration}ms ${EASE}`;
      leaf.style.transform = `rotateY(${angleTo}deg)`;
    }
    setTimeout(() => {
      if (landSide && mine > sideSeq[landSide]) {
        sideSeq[landSide] = mine;
        fill(landSide, landSide === "L" ? nl : nr);
        sideChrome(landSide, id);
      }
      leaf.remove();
      inAir -= 1;
      settleSoon();
      if (mine === seq) scrollToAnchor(anchor);
    }, duration + 30);
  }

  const step = (d) => {
    const target = order[order.indexOf(current) + d];
    if (target) turn(target);
  };
  prev.addEventListener("click", () => step(-1));
  next.addEventListener("click", () => step(1));

  // swipe the page sideways to turn it (the corners and the wheel do the same)
  let start = null;
  // a swipe that starts on a swipe row, a model, a video or a field belongs to that thing, not the book
  const OWN_GESTURE = "[data-slides], model-viewer, video, select, input, button.slides-prev, button.slides-next, .nb-tab";
  // Only a single finger can swipe: a second finger (a pinch or a two-finger drag) is a non-primary pointer and cancels it.
  book.addEventListener("pointerdown", (e) => {
    if (!e.isPrimary) { start = null; return; }
    start = e.target.closest(OWN_GESTURE) ? null : { x: e.clientX, y: e.clientY, at: e.timeStamp };
  });
  // The browser takes a gesture that starts moving up or down (it scrolls the page and cancels ours),
  // so what reaches pointerup here began sideways. Even so, only a clearly horizontal stroke turns the page.
  book.addEventListener("pointercancel", () => { start = null; });
  book.addEventListener("pointerup", (e) => {
    if (!e.isPrimary || !start) return;
    const dx = e.clientX - start.x;
    const dy = e.clientY - start.y;
    const quick = e.timeStamp - start.at < 900;
    start = null;
    if (Math.abs(dx) >= SWIPE_MIN && Math.abs(dx) > Math.abs(dy) * SWIPE_RATIO && quick) step(dx < 0 ? 1 : -1);
  });

  return {
    mode,
    order,
    book,
    turn,
    normalize,
    /** Show a page at once, with no turn. */
    show(id, anchor) { turn(id, { duration: 0, anchor, silent: true }); },
    get current() { return current; },
    destroy() {
      clearTimeout(settleTimer);
      book.remove();
      status.remove();
    },
  };
}
