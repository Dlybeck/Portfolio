// Starts the notebook: picks phone or desktop, builds the book, the wheel and the cover,
// and keeps the address bar in step with the page that is showing.

import { createBook } from "./book.js?v=4";
import { createCover } from "./cover.js?v=6";
import { enhance, settled } from "./media.js";
import { createTabs } from "./tabs.js";
import { createWheel } from "./wheel.js?v=5";
import { createWheelTip } from "./wheel-tip.js";
import { hasSeenOpening, liftCornerOnce, playOpening, rememberOpening } from "./opening.js";
import { reducedMotion } from "./motion.js";

const root = document.getElementById("notebook");
const data = JSON.parse(document.getElementById("nb-data").textContent);
const sourceNode = document.getElementById("nb-sources");
const sources = new Map([...sourceNode.querySelectorAll(":scope > article")].map((a) => [a.dataset.page, a]));
const wide = window.matchMedia("(min-width: 900px), (orientation: landscape) and (min-width: 640px), (orientation: landscape) and (max-height: 520px) and (min-width: 560px)");

/** Where an address points: a page and maybe a part of it, or null for the closed cover. */
function targetFor({ pathname, hash }) {
  const route = data.routes[pathname.replace(/(.)\/$/, "$1")];
  if (route) return route;
  const name = hash.slice(1);
  const found = Object.entries(data.pages).find(([, page]) => page.hash && page.hash === name);
  if (found) return { page: found[0], anchor: null };
  const old = data.hashAliases[name]; // an address from before the intro page went
  return old ? { page: old, anchor: null } : null;
}

/** The address a page lives at. Pages without a route of their own use a hash on "/". */
const addressOf = (id) => data.pages[id].path || `/#${data.pages[id].hash}`;
const here = () => location.pathname + location.hash;

// ---------- the history ----------
// A turn is a step, so Back undoes it: every turn writes its entry at once (a link, the contents, the cover, a corner, a swipe, a key).
// The turns one wheel input makes (a spin through several pages, a drag, opening the cover and then turning) share one entry, so a
// fast spin does not bury the history; wheel.js numbers each input. One continuous scroll that goes forward and then back to where it
// began leaves that start page on the history twice. Back or Forward ends the input, and showing the page of an entry they landed on
// only tidies that entry's address, so Forward keeps working.
let replaying = false; // Back or Forward is showing the page of an entry that is already in the history
let lastInput = null; // the wheel input that wrote the entry on top; null when anything else did

function remember(page, input = null) {
  const state = { page };
  const address = page ? addressOf(page) : "/";
  if (replaying || (input !== null && input === lastInput)) history.replaceState(state, "", address);
  else history.pushState(state, "", address);
  lastInput = replaying ? null : input;
}

function mount(initial) {
  lastInput = null; // a new wheel numbers its inputs from the start again, so an input of the old one must not match
  const phone = !wide.matches;
  root.classList.remove("nb--phone", "nb--desktop", "is-closed", "is-turned");
  root.classList.add(phone ? "nb--phone" : "nb--desktop");
  if (!initial) root.classList.add("is-closed"); // shut from the start, so the book does not slide into place on load

  let book; let wheel; let cover; let tabs = null;
  let spinning = false; // the wheel is turning the pages, so it must not be re-aimed
  let spinInput = null; // the wheel input whose turn is being shown (see wheel.js)
  let opening = false; // the first-visit spin is running: the address stays "/" and it writes nothing to the history
  let stopOpening = null;
  const hooks = {
    page: (id, duration, input) => {
      spinning = true;
      spinInput = input;
      book.turn(id, { duration });
      spinning = false;
    },
    open: (input) => openCover({ fromWheel: true, input }),
    close: (input) => closeCover({ fromWheel: true, input, push: !opening }),
    isClosed: () => cover.closed,
    current: () => book.current,
  };
  // The wheel and the address follow whatever page the book shows, however it was turned.
  book = createBook({
    root, data, sources, mode: phone ? "phone" : "desktop", onFill: enhance, onSettled: settled,
    onView: (id) => {
      if (!spinning) wheel?.sync(id);
      if (opening || cover.closed || here() === addressOf(id)) return; // (a link or tab already wrote its entry in go(); the opening writes none)
      remember(id, spinning ? spinInput : null);
    },
  });
  wheel = createWheel({ root, data, order: book.order, phone, hooks });
  const tip = createWheelTip(root);
  cover = createCover({ root, book: book.book, phone, onTap: () => openCover() });
  tabs = createTabs({ root, book: book.book, data, addressOf }); // a phone gets slim tabs too

  function openCover({ fromWheel = false, input = null } = {}) {
    if (!cover.closed) return;
    cover.open();
    if (!fromWheel) wheel.sync(book.current);
    if (here() !== addressOf(book.current)) remember(book.current, fromWheel ? input : null);
  }
  function closeCover({ push = true, fromWheel = false, input = null } = {}) {
    if (cover.closed) return;
    book.show(book.order[0]);
    cover.close({ animate: true });
    if (!fromWheel) wheel.sync("cover");
    if (push) remember(null, fromWheel ? input : null);
  }

  /** Show a page (a link, the contents, back and forward): turn to it, opening the cover first if it is shut. */
  function go(id, anchor, { push = true } = {}) {
    const page = book.normalize(id);
    if (push && here() !== addressOf(page)) remember(page);
    replaying = !push;
    try {
      if (cover.closed) {
        book.show(page, anchor);
        cover.open();
      } else {
        book.turn(page, { anchor });
      }
    } finally {
      replaying = false;
    }
    wheel.sync(page);
  }

  if (initial) {
    book.show(initial.page, initial.anchor);
    wheel.set(book.current);
    if (!initial.opening && here() !== addressOf(book.current)) history.replaceState({ page: book.current }, "", addressOf(book.current));
  } else {
    book.show(book.order[0]);
    cover.close();
    wheel.set("cover");
  }

  return {
    /** First visit: spin the book from its last page back to the cover (see opening.js). The address is "/" the whole time. */
    playOpening() {
      opening = true;
      stopOpening = playOpening({
        wheel, tip,
        finish() {
          opening = false;
          if (!cover.closed && here() !== addressOf(book.current)) history.replaceState({ page: book.current }, "", addressOf(book.current)); // the visitor took over on a page
        },
      });
    },
    showTip: () => tip.show(),
    go,
    home: (options) => closeCover(options),
    focusPage() { (book.book.querySelector(".nb-page.r .nb-in") ?? book.book.querySelector(".nb-page .nb-in"))?.focus({ preventScroll: true }); },
    get isClosed() { return cover.closed; },
    get isOpening() { return opening; },
    get page() { return cover.closed || opening ? null : book.current; }, // mid-opening, a rebuild starts again from the cover
    destroy() { stopOpening?.(); tip.hide(); tabs?.destroy(); cover.destroy(); wheel.destroy(); book.destroy(); },
  };
}

// A first visit to plain "/" (not a page address, not ?intro=0) gets the opening; ?intro=1 plays it again.
const introParam = new URLSearchParams(location.search).get("intro");
const firstVisit = !targetFor(location) && introParam !== "0" && (introParam === "1" || !hasSeenOpening());
const spin = firstVisit && !reducedMotion();
let view = mount(spin ? { page: data[wide.matches ? "desktop" : "phone"].at(-1), anchor: null, opening: true } : targetFor(location));
if (firstVisit) {
  rememberOpening();
  liftCornerOnce(root);
  if (spin) view.playOpening();
  else view.showTip(); // reduced motion: no spin, just the tooltip on the cover
}

root.addEventListener("click", (e) => {
  const link = e.target.closest("[data-open], [data-home]");
  if (!link || e.metaKey || e.ctrlKey || e.shiftKey || e.button) return; // keep "open in a new tab" working
  e.preventDefault();
  if (link.hasAttribute("data-home")) view.home();
  else {
    view.go(link.dataset.open);
    view.focusPage(); // the clicked link is gone once the page is rewritten; keep keyboard users in the book
  }
});

window.addEventListener("popstate", () => {
  lastInput = null; // Back or Forward ends a wheel input: its next turn starts an entry of its own
  const target = targetFor(location);
  if (target) view.go(target.page, target.anchor, { push: false });
  else if (!view.isClosed) view.home({ push: false });
});

// moving between phone and desktop sizes rebuilds the book at the same page
wide.addEventListener("change", () => {
  const page = view.page;
  const midOpening = view.isOpening; // the first-visit spin was cut short by the resize: the cover it lands on still gets its tip
  view.destroy();
  view = mount(page ? { page, anchor: null } : null);
  if (midOpening) view.showTip();
});
