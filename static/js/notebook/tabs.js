// Tabs on the right edge of the open two-page notebook that jump straight to a main section. They are plain
// links (so they work with a keyboard and "open in a new tab"); main.js turns the page when one is chosen.
// A phone has no tabs: the wheel and the swipe are its way around.

import { el } from "./motion.js";

/**
 * @param {object} o
 * @param {HTMLElement} o.root
 * @param {HTMLElement} o.book  the .nb-book element the tabs are attached to
 * @param {object} o.data  table of contents
 * @param {(id: string) => string} o.addressOf  the real address of a page
 */
export function createTabs({ root, book, data, addressOf }) {
  const nav = el("nav", "nb-tabs", { "aria-label": "Sections" });
  // each tab opens its section's first page (on a spread, the section's first story)
  nav.innerHTML = data.sections
    .map((s) => {
      const first = s.id; // every section has an index page with the same id
      return `<a class="nb-tab" href="${addressOf(first)}" data-open="${first}" data-section="${s.id}" style="--tab:var(--paper-${s.color})">${s.tab}</a>`;
    })
    .join("");
  book.append(nav);

  const mark = (id) => {
    const section = data.pages[id].section;
    for (const tab of nav.children) {
      if (tab.dataset.section === section) tab.setAttribute("aria-current", "page");
      else tab.removeAttribute("aria-current");
    }
  };
  const onView = (e) => mark(e.detail);
  root.addEventListener("nb:view", onView);
  if (root.dataset.page) mark(root.dataset.page);

  // While the cover is shut the tabs only peek out: a mouse can still use them, but a keyboard or screen reader skips them
  const hideWhenShut = () => {
    const shut = root.classList.contains("is-closed");
    if (shut) nav.setAttribute("aria-hidden", "true");
    else nav.removeAttribute("aria-hidden");
    for (const tab of nav.children) tab.tabIndex = shut ? -1 : 0;
  };
  const watch = new MutationObserver(hideWhenShut);
  watch.observe(root, { attributes: true, attributeFilter: ["class"] });
  hideWhenShut();

  return {
    destroy() {
      watch.disconnect();
      root.removeEventListener("nb:view", onView);
      nav.remove();
    },
  };
}
