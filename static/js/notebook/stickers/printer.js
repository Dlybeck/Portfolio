// The 3D printer: it prints the logo layer by layer, and prints it again when tapped.

import { LOGO, reducedMotion, tap } from "./common.js";

export const printer = {
  html: () => `<div class="wd wd-p12 p12a" role="button" tabindex="0" aria-label="3D printer. Tap to print again."><div class="p12-m"><i class="p12-sp" aria-hidden="true"></i><i class="p12-fil" aria-hidden="true"></i><i class="p12-rl"></i><i class="p12-rr"></i><i class="p12-top"></i><div class="p12-o" style="--logo:url('${LOGO}')"></div><i class="p12-g"><i class="p12-n"></i></i><i class="p12-bed"></i></div></div>`,

  wire(machine, { alive }) {
    const run = () => {
      machine.classList.remove("go", "done");
      void machine.offsetWidth;
      if (reducedMotion()) { machine.classList.add("done"); return; }
      machine.classList.add("go");
      setTimeout(() => alive() && machine.classList.add("done"), 3300);
    };
    setTimeout(() => alive() && run(), 700);
    tap(machine, run);
  },
};
