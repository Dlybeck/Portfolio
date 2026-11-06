// The name tag. Tap it and the name is wiped and written again in another hand.

import { reducedMotion, tap } from "./common.js";

// [font, size scale so every hand reads about as big, weight]
const HANDS = [["Caveat", 1, 700], ["Permanent Marker", 0.74, 400], ["Homemade Apple", 0.62, 400], ["Gochi Hand", 0.92, 400], ["Nothing You Could Do", 0.72, 400]];

export const name = {
  html: () => `<div class="wd wd-name" role="button" tabindex="0" aria-label="Name tag: David. Tap to write it in another hand." data-hand="0"><span class="tag"><b>HELLO</b><small>my name is</small><span class="nm"><span class="nm-w"><span class="nm-i">David</span><i class="nm-pen" aria-hidden="true"></i></span></span></span></div>`,

  wire(tag, { alive }) {
    const nm = tag.querySelector(".nm");
    let timer = 0;
    const askForFonts = () => HANDS.forEach(([family, , weight]) => document.fonts?.load(`${weight} 2rem "${family}"`).catch(() => {}));
    (window.requestIdleCallback || setTimeout)(askForFonts);

    const setHand = (i) => {
      tag.dataset.hand = i;
      nm.style.fontFamily = `"${HANDS[i][0]}", var(--font-hand)`;
      nm.style.setProperty("--hand-scale", HANDS[i][1]);
      nm.style.fontWeight = HANDS[i][2];
    };
    tap(tag, () => {
      clearTimeout(timer);
      const next = (Number(tag.dataset.hand) + 1) % HANDS.length;
      if (reducedMotion()) { setHand(next); return; }
      tag.classList.remove("go");
      tag.classList.add("out");
      timer = setTimeout(() => {
        if (!alive()) return;
        setHand(next);
        tag.classList.remove("out");
        void tag.offsetWidth;
        tag.classList.add("go");
      }, 260);
    });
  },
};
