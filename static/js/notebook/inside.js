// The inside of the notebook's covers, for the first and last spreads of a desktop book. Each is a stable element,
// `.cover-inside` plus `--front` or `--back`, the size of a page, with `container-type: size` (see cover.css) so what
// sits on it can be placed in cqw and cqh. The stickers here are the cover's own markup, made still: no wiring.

import { el } from "./motion.js";
import { hike } from "./stickers/hike.js";
import { raccoon } from "./stickers/raccoon.js";

const STICKERS = { front: hike, back: raccoon };

/** A sticker's markup with nothing to press: decoration, hidden from keyboards and screen readers. */
const still = (sticker) => sticker.html().replace(' role="button" tabindex="0"', ' aria-hidden="true"');

/**
 * @param {"front"|"back"} side
 * @param {HTMLElement} [note]  a page of words (the contents) to rest on the cover as a paper card
 */
export function insideCover(side, note) {
  const inside = el("div", `cover-inside cover-inside--${side}`);
  inside.innerHTML = still(STICKERS[side]);
  if (note) {
    const card = el("div", "cover-inside__card");
    card.append(note);
    inside.prepend(card);
  }
  const page = el("div", "page");
  page.append(inside);
  return page;
}
