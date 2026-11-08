// The inside of the notebook's covers, for the first and last spreads of a desktop book. Each is a stable element,
// `.cover-inside` plus `--front` or `--back`, the size of a page, with `container-type: size` (see cover.css) so what
// is placed on it can be positioned in cqw and cqh. Their stickers come from stickers/layout.json (see stickers/index.js).

import { el } from "./motion.js";
import { wireInside } from "./stickers/index.js?v=3";

/** @param {"front"|"back"} side */
export function insideCover(side) {
  const inside = el("div", `cover-inside cover-inside--${side}`);
  inside.setAttribute("aria-hidden", "true");
  const page = el("div", "page");
  wireInside(inside, side);
  page.append(inside);
  return page;
}
