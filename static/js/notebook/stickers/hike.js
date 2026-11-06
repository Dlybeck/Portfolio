// The trail stamp: tap and a hiker climbs to the top, then the sun sets. Tap again for morning.

import { reducedMotion, tap } from "./common.js";

export const hike = {
  html: () => `<div class="wd wd-hike" role="button" tabindex="0" aria-label="Stamp of a mountain trail. Tap to go for a hike."><svg viewBox="0 0 120 72" aria-hidden="true">
    <rect class="m-sky" width="120" height="72"/><rect class="m-band" y="12" width="120" height="4"/><circle class="m-sun" cx="28" cy="24" r="9"/>
    <path class="m-far" d="M0 48 L20 32 L32 40 L56 12 L74 34 L88 26 L120 44 V72 H0Z"/><path class="m-snow" d="M50 19 L56 12 L62 18.5 L59 17.5 L56 20.5 L53 18Z"/>
    <rect class="m-mead" y="54" width="120" height="18"/><path class="m-trail" d="M66 72 C82 64 52 60 68 52 S74 36 57 15" fill="none"/>
    <g class="m-hiker"><circle r="2" cy="-5"/><rect x="-1.5" y="-3.4" width="3" height="4.6" rx="1"/><rect x="-3.2" y="-3" width="1.9" height="3.4" rx=".6" class="pack"/></g>
    <path class="m-tree" d="M4 66 L11 40 L18 66Z M16 68 L22 50 L28 68Z M96 68 L104 42 L112 68Z"/></svg></div>`,

  wire(stamp, { alive }) {
    const trail = stamp.querySelector(".m-trail");
    const hiker = stamp.querySelector(".m-hiker");
    const length = trail.getTotalLength();
    const place = (fraction) => {
      const point = trail.getPointAtLength(length * fraction);
      hiker.setAttribute("transform", `translate(${point.x} ${point.y})`);
    };
    place(0);
    let walking = false;
    tap(stamp, () => {
      if (walking) return;
      if (stamp.classList.contains("dusk")) { stamp.classList.remove("dusk"); place(0); return; }
      if (reducedMotion()) { place(1); stamp.classList.add("dusk"); return; }
      walking = true;
      const start = performance.now();
      const DURATION = 2200;
      const step = (now) => {
        if (!alive()) return;
        const f = Math.min(1, (now - start) / DURATION);
        place(f < 0.5 ? 2 * f * f : 1 - (-2 * f + 2) ** 2 / 2);
        if (f < 1) requestAnimationFrame(step);
        else { stamp.classList.add("dusk"); walking = false; }
      };
      requestAnimationFrame(step);
    });
  },
};
