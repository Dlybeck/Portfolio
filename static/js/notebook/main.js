// Starts the notebook: picks phone or desktop, builds the book, the wheel and the cover,
// and keeps the address bar in step with the page that is showing.

import { createBook } from "./book.js?v=4";
import { createCover } from "./cover.js?v=6";
import { enhance, settled } from "./media.js";
import { createTabs } from "./tabs.js";
import { createWheel } from "./wheel.js";

const root = document.getElementById("notebook");
const data = JSON.parse(document.getElementById("nb-data").textContent);
const sourceNode = document.getElementById("nb-sources");
const sources = new Map([...sourceNode.querySelectorAll(":scope > article")].map((a) => [a.dataset.page, a]));
const wide = window.matchMedia("(min-width: 900px), (orientation: landscape) and (min-width: 640px)");

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
  const hooks = {
    page: (id, duration) => {
      spinning = true;
      book.turn(id, { duration });
      spinning = false;
    },
    open: () => openCover({ fromWheel: true }),
    close: () => closeCover({ fromWheel: true }),
    isClosed: () => cover.closed,
    current: () => book.current,
  };
  // The wheel and the address follow whatever page the book shows, however it was turned.
  book = createBook({
    root, data, sources, mode: phone ? "phone" : "desktop", onFill: enhance, onSettled: settled,
    onView: (id) => {
      if (!spinning) wheel?.sync(id);
      if (!cover.closed && here() !== addressOf(id)) history.replaceState({ page: id }, "", addressOf(id));
    },
  });
  wheel = createWheel({ root, data, order: book.order, phone, hooks });
  cover = createCover({ root, book: book.book, phone, onTap: () => openCover() });
  tabs = createTabs({ root, book: book.book, data, addressOf }); // a phone gets slim tabs too

  function openCover({ fromWheel = false } = {}) {
    if (!cover.closed) return;
    cover.open();
    if (!fromWheel) wheel.sync(book.current);
    if (here() !== addressOf(book.current)) history.pushState({ page: book.current }, "", addressOf(book.current));
  }
  function closeCover({ push = true, fromWheel = false } = {}) {
    if (cover.closed) return;
    book.show(book.order[0]);
    cover.close({ animate: true });
    if (!fromWheel) wheel.sync("cover");
    if (push) history.pushState({ page: null }, "", "/");
  }

  /** Show a page (a link, the contents, back and forward): turn to it, opening the cover first if it is shut. */
  function go(id, anchor, { push = true } = {}) {
    const page = book.normalize(id);
    if (push && here() !== addressOf(page)) history.pushState({ page }, "", addressOf(page));
    if (cover.closed) {
      book.show(page, anchor);
      cover.open();
    } else {
      book.turn(page, { anchor });
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
