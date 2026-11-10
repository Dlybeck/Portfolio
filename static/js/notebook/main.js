// Starts the notebook: picks phone or desktop, builds the book, the wheel and the cover,
// and keeps the address bar in step with the page that is showing.

import { createBook } from "./book.js?v=4";
import { createCover } from "./cover.js?v=6";
import { enhance, settled } from "./media.js";
import { createTabs } from "./tabs.js";
import { createWheel } from "./wheel.js?v=2";

const root = document.getElementById("notebook");
const data = JSON.parse(document.getElementById("nb-data").textContent);
const sourceNode = document.getElementById("nb-sources");
const sources = new Map([...sourceNode.querySelectorAll(":scope > article")].map((a) => [a.dataset.page, a]));
const wide = window.matchMedia("(min-width: 900px), (orientation: landscape) and (min-width: 640px), (orientation: landscape) and (max-height: 520px) and (min-width: 480px)");

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

function mount(initial) {
  const phone = !wide.matches;
  root.classList.remove("nb--phone", "nb--desktop", "is-closed", "is-turned");
  root.classList.add(phone ? "nb--phone" : "nb--desktop");
  if (!initial) root.classList.add("is-closed"); // shut from the start, so the book does not slide into place on load

  let book; let wheel; let cover; let tabs = null;
  let spinning = false; // the wheel is turning the pages, so it must not be re-aimed
  let replaying = false; // Back or Forward is showing the page of an entry that is already in the history
  let spinInput = null; // the wheel input whose turn is being shown (see wheel.js), so its turns can share a history entry
  let lastInput = null; // the wheel input that wrote the history entry on top; null when anything else did

  /**
   * Write what is showing (a page, or null for the shut cover) into the history. A turn is a step, so Back undoes it; the turns
   * one wheel input makes (a spin through several pages, or opening the cover and then turning) share one entry. Showing the
   * page of an entry Back or Forward landed on only tidies that entry's address, which keeps Forward working.
   */
  function remember(page, input = null) {
    const state = { page };
    const address = page ? addressOf(page) : "/";
    if (replaying || (input !== null && input === lastInput)) history.replaceState(state, "", address);
    else history.pushState(state, "", address);
    lastInput = replaying ? null : input;
  }
  const hooks = {
    page: (id, duration, input) => {
      spinning = true;
      spinInput = input;
      book.turn(id, { duration });
      spinning = false;
    },
    open: (input) => openCover({ fromWheel: true, input }),
    close: (input) => closeCover({ fromWheel: true, input }),
    isClosed: () => cover.closed,
    current: () => book.current,
  };
  // The wheel and the address follow whatever page the book shows, however it was turned.
  book = createBook({
    root, data, sources, mode: phone ? "phone" : "desktop", onFill: enhance, onSettled: settled,
    onView: (id) => {
      if (!spinning) wheel?.sync(id);
      if (cover.closed || here() === addressOf(id)) return;
      remember(id, spinning ? spinInput : null); // a corner, swipe or key turn (a link or tab already wrote its entry in go())
    },
  });
  wheel = createWheel({ root, data, order: book.order, phone, hooks });
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
    if (here() !== addressOf(book.current)) history.replaceState({ page: book.current }, "", addressOf(book.current));
  } else {
    book.show(book.order[0]);
    cover.close();
    wheel.set("cover");
  }

  return {
    go,
    home: (options) => closeCover(options),
    focusPage() { (book.book.querySelector(".nb-page.r .nb-in") ?? book.book.querySelector(".nb-page .nb-in"))?.focus({ preventScroll: true }); },
    get isClosed() { return cover.closed; },
    get page() { return cover.closed ? null : book.current; },
    destroy() { tabs?.destroy(); cover.destroy(); wheel.destroy(); book.destroy(); },
  };
}

let view = mount(targetFor(location));

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
  const target = targetFor(location);
  if (target) view.go(target.page, target.anchor, { push: false });
  else if (!view.isClosed) view.home({ push: false });
});

// moving between phone and desktop sizes rebuilds the book at the same page
wide.addEventListener("change", () => {
  const page = view.page;
  view.destroy();
  view = mount(page ? { page, anchor: null } : null);
});
