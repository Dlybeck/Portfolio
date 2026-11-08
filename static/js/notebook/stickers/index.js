// The cover's stickers. Which ones there are, and where each sits, is in layout.json (written by Sticker Studio):
// "front" is the cover itself, "inside" the inside front cover and "back" the inside back cover. Each entry is
// {id, x, y, r, s}; the array order is the paint order (later ones on top). x and y are the left and top of the
// sticker's unrotated, unscaled box in cqw and cqh of its face; r (degrees) and s (scale) turn and grow it about its centre.

import { keepEventsHere } from "./common.js";
import { ball } from "./ball.js?v=3";
import { blankSticker } from "./blank.js?v=2";
import { cow } from "./cow.js";
import { hike } from "./hike.js";
import { name } from "./name.js";
import { now } from "./now.js";
import { printer } from "./printer.js";
import { puzzle } from "./puzzle.js";
import { scan } from "./scan.js";
import { startHints } from "./hints.js";

/** Every sticker there is, by the id the layout uses. */
const STICKERS = { name, now, hike, scan, puzzle, printer, blank: blankSticker, ball, cow };

const EMPTY = { front: [], inside: [], back: [] };
const LAYOUT = await fetch(new URL("./layout.json?v=1", import.meta.url))
  .then((r) => (r.ok ? r.json() : EMPTY))
  .catch(() => EMPTY); // no layout means a bare cover, never a broken page

const num = (value, fallback) => (Number.isFinite(value) ? value : fallback);

/** The HTML of a face's stickers: each in a positioned slot, in paint order. */
export function stickersHtml(face) {
  const entries = Array.isArray(LAYOUT[face]) ? LAYOUT[face] : [];
  return entries
    .filter((e) => Object.hasOwn(STICKERS, e?.id))
    .map((e, i) => `<div class="wd-slot" data-sticker="${e.id}" style="left:${num(e.x, 0)}cqw;top:${num(e.y, 0)}cqh;rotate:${num(e.r, 0)}deg;scale:${num(e.s, 1)};z-index:${i + 1}">${STICKERS[e.id].html()}</div>`)
    .join("");
}

/** Make the stickers on `face` (the cover's front or an inside cover) live. They stop by themselves when the face leaves the page. */
export function wireStickers(face) {
  const alive = () => face.isConnected;
  for (const slot of face.querySelectorAll(":scope > .wd-slot")) {
    const el = slot.firstElementChild;
    keepEventsHere(el);
    el.insertAdjacentHTML("beforeend", `<i class="wd-sh" aria-hidden="true"></i><i class="wd-mt" aria-hidden="true"></i>${el.classList.contains("wd-name") ? '<i class="wd-curl" aria-hidden="true"></i>' : ""}`);
    STICKERS[slot.dataset.sticker].wire(el, { alive, cover: face });
  }
  if (face.classList.contains("cover-front")) startHints(face, alive); // a quiet nudge that they are tappable, until the first touch (only while the cover is shut)
}

/** Put an inside cover's stickers on it ("front" or "back") and make them live. */
export function wireInside(inside, side) {
  const html = stickersHtml(side === "front" ? "inside" : "back");
  if (!html) return;
  inside.insertAdjacentHTML("beforeend", html);
  inside.removeAttribute("aria-hidden"); // it has things to press now
  wireStickers(inside);
}
