// The nine stickers on the cover, in the order they are stuck on (later ones sit on top).

import { keepEventsHere } from "./common.js";
import { ball } from "./ball.js";
import { blankSticker } from "./blank.js";
import { hike } from "./hike.js";
import { name } from "./name.js";
import { now } from "./now.js";
import { printer } from "./printer.js";
import { puzzle } from "./puzzle.js";
import { raccoon } from "./raccoon.js";
import { scan } from "./scan.js";
import { startHints } from "./hints.js";

const SET = [name, now, hike, scan, puzzle, printer, raccoon, blankSticker, ball];

/** The HTML of every sticker. */
export const stickersHtml = () => SET.map((s) => s.html()).join("");

/** Make the stickers inside `cover` live. They stop by themselves when the cover leaves the page. */
export function wireStickers(cover) {
  const alive = () => cover.isConnected;
  const elements = [...cover.querySelectorAll(":scope > .wd")];
  elements.forEach((el, i) => {
    keepEventsHere(el);
    el.insertAdjacentHTML("beforeend", `<i class="wd-sh" aria-hidden="true"></i>${el.classList.contains("wd-name") ? '<i class="wd-curl" aria-hidden="true"></i>' : ""}`);
    SET[i].wire(el, { alive, cover });
  });
  startHints(cover, alive); // a quiet nudge that they are tappable, until the first touch
}
