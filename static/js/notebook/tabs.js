// Tabs on the edge of the notebook that jump straight to a main section. They are plain links
// (so they work with a keyboard and "open in a new tab"); main.js turns the page when one is chosen.
//
// Two placements are being tried, picked by ?tabs=a or ?tabs=b (the class on #notebook does the rest):
//   a: along the top edge of the book on a phone, down the right edge on desktop
//   b: down the right edge on both

import { el } from "./motion.js";

/**
 * @param {object} o
 * @param {HTMLElement} o.root
 * @param {HTMLElement} o.book  the .nb-book element the tabs are attached to
 * @param {object} o.data  table of contents
 * @param {"a"|"b"} o.variant
 */
export function createTabs({ root, book, data, variant: asked, addressOf }) {
  // on a narrow phone the top row cannot fit six readable words, so placement a uses the right edge there
  const variant = asked === "a" && matchMedia("(max-width: 379px)").matches ? "b" : asked;
  root.classList.add(`nb--tabs-${variant}`);
  const nav = el("nav", "nb-tabs", { "aria-label": "Sections" });
  // each tab opens its section's first page: the index page on a phone, the first story on desktop
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

  return {
    destroy() {
      root.removeEventListener("nb:view", onView);
      root.classList.remove(`nb--tabs-${variant}`);
      nav.remove();
    },
  };
}
