// A raccoon at a keyboard. Tap and it types a quick hello.

import { reducedMotion, tap } from "./common.js";

const KEYBOARD = `<rect class="ty-kb" x="5" y="28" width="38" height="7" rx="1.6"/><path class="ty-ks" d="M8 30.6h32M8 32.8h32" />`;
const RACCOON = `<g class="ty-hd"><circle class="ty-c1" cx="15" cy="6.5" r="4"/><circle class="ty-c1" cx="33" cy="6.5" r="4"/><circle class="ty-c3" cx="15" cy="6.5" r="1.8"/><circle class="ty-c3" cx="33" cy="6.5" r="1.8"/>
  <ellipse class="ty-c1" cx="24" cy="15" rx="12" ry="10"/><ellipse class="ty-c2" cx="24" cy="19" rx="7.5" ry="5.5"/><path class="ty-c3" d="M12.6 13.5q5.4-4.5 11.4-.4q6-4.1 11.4.4q-2.6 4.2-6.8 3.2q-2.8-.8-4.6-.8t-4.6.8q-4.2 1-6.8-3.2Z"/>
  <g class="ty-eye"><circle cx="19" cy="13.3" r="1.5" fill="#fff"/><circle cx="29" cy="13.3" r="1.5" fill="#fff"/></g><circle class="ty-c3" cx="24" cy="19.2" r="1.6"/></g>
  ${KEYBOARD}<ellipse class="ty-a ty-c1" cx="17" cy="29" rx="2.8" ry="2.2"/><ellipse class="ty-b ty-c1" cx="31" cy="29" rx="2.8" ry="2.2"/>`;
const WORDS = ["hi!", "hello", "hey there"];

export const raccoon = {
  html: () => `<div class="wd wd-pal wd-pal-raccoon" role="button" tabindex="0" aria-label="A raccoon at a keyboard. Tap to say hi."><span class="pty ty-raccoon"><svg viewBox="0 0 48 36" aria-hidden="true">${RACCOON}</svg></span><span class="pal-say" aria-hidden="true"></span></div>`,

  wire(pal, { alive }) {
    const say = pal.querySelector(".pal-say");
    let timer = 0;
    let k = 0;
    tap(pal, () => {
      clearTimeout(timer);
      pal.classList.add("typing", "saying");
      say.textContent = "";
      const word = WORDS[k++ % WORDS.length];
      let i = 0;
      const step = () => {
        if (!alive()) return;
        say.textContent = word.slice(0, ++i);
        if (i < word.length) timer = setTimeout(step, reducedMotion() ? 0 : 110);
        else timer = setTimeout(() => {
          pal.classList.remove("typing");
          timer = setTimeout(() => { say.textContent = ""; }, 1300);
        }, 300);
      };
      step();
    });
  },
};
