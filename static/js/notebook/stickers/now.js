// The "now" pill: what I'm doing now, and tap for what came before.

import { restart, tap } from "./common.js";

const NOW = [["now", "AI tools at Denali", true], ["2025", "ScribbleScan LLC"], ["2024", "2nd Chair intern"], ["2022", "tennis coach"]];

export const now = {
  html: () => `<div class="wd wd-now" role="button" tabindex="0" aria-label="What I'm doing. Tap for earlier."><i class="dot"></i><b></b><span></span></div>`,

  wire(pill) {
    let i = 0;
    const show = () => {
      const [when, what, live] = NOW[i];
      pill.querySelector("b").textContent = when;
      pill.querySelector("span").textContent = what;
      pill.classList.toggle("live", Boolean(live));
    };
    show();
    tap(pill, () => {
      i = (i + 1) % NOW.length;
      show();
      restart(pill, "flip");
    });
  },
};
