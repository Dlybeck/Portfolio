// A sliding puzzle with the logo on its tiles. Slide the tiles back into place.

import { LOGO } from "./common.js";

const adjacent = (a, b) => Math.abs((a % 3) - (b % 3)) + Math.abs(Math.floor(a / 3) - Math.floor(b / 3)) === 1;

export const puzzle = {
  html: () => `<div class="wd wd-puzzle"><div class="pz" role="group" aria-label="Sliding puzzle">${[0, 1, 2, 3, 4, 5, 6, 7].map((i) => `<button type="button" class="pz-t" data-i="${i}" aria-label="Tile ${i + 1}"></button>`).join("")}</div><span class="pz-k">puzzle box</span></div>`,

  wire(card) {
    const tiles = [...card.querySelectorAll(".pz-t")];
    const label = card.querySelector(".pz-k");
    card.querySelector(".pz").style.setProperty("--logo-img", `url("${LOGO}")`);
    tiles.forEach((tile) => {
      const i = Number(tile.dataset.i);
      tile.style.backgroundImage = `url("${LOGO}")`;
      tile.style.backgroundPosition = `${(i % 3) * 50}% ${Math.floor(i / 3) * 50}%`;
    });
    // cells[position] = tile; 8 is the gap. The same few moves from "solved" every time.
    const cells = [0, 1, 2, 3, 4, 5, 6, 7, 8];
    let seed = 7;
    const random = () => (seed = (seed * 16807) % 2147483647) / 2147483647;
    let previous = -1;
    for (let k = 0; k < 7; k++) {
      const gap = cells.indexOf(8);
      const options = cells.map((_, p) => p).filter((p) => adjacent(p, gap) && p !== previous);
      const p = options[Math.floor(random() * options.length)];
      [cells[gap], cells[p]] = [cells[p], cells[gap]];
      previous = gap;
    }
    const place = () => {
      cells.forEach((tile, p) => {
        if (tile < 8) tiles[tile].style.translate = `${(p % 3) * 100}% ${Math.floor(p / 3) * 100}%`;
      });
      const solved = cells.every((tile, p) => tile === p);
      card.classList.toggle("solved", solved);
      label.textContent = solved ? "solved!" : "puzzle box";
    };
    tiles.forEach((tile) => tile.addEventListener("click", () => {
      const p = cells.indexOf(Number(tile.dataset.i));
      const gap = cells.indexOf(8);
      if (!adjacent(p, gap)) return;
      [cells[gap], cells[p]] = [cells[p], cells[gap]];
      place();
    }));
    place();
  },
};
