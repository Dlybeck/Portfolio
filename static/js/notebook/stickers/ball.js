// The tennis ball. Tap to bounce it; drag and let go to throw it around the cover.

import { reducedMotion } from "./common.js";

const GRAVITY = 1500;
const BOUNCE = 0.72;

export const ball = {
  html: () => `<div class="wd wd-ball" role="button" tabindex="0" aria-label="Tennis ball. Tap to bounce it, or throw it."></div>`,

  wire(el, { alive, cover }) {
    let x = 0; let y = 0; let vx = 0; let vy = 0; let spin = 0; let rot = 0;
    let raf = 0; let last = 0; let drag = null; let homed = false;
    const slot = el.closest(".wd-slot"); // the layout turns and scales the ball through its slot until it is free
    const homeTurn = parseFloat(slot?.style.rotate) || 0;
    const scale = parseFloat(slot?.style.scale) || 1;
    const size = () => el.offsetWidth * scale; // its size on the cover, as the visitor sees it
    const grow = () => (el.offsetWidth * (scale - 1)) / 2; // a scaled box grows about its centre, so its layout box sits this far inside
    const width = () => cover.clientWidth;
    const height = () => cover.clientHeight;

    const put = () => {
      el.style.translate = `${x + grow()}px ${y + grow()}px`;
      el.style.rotate = `${rot}deg`;
      const sheen = el.querySelector(":scope > .wd-mt");
      if (sheen) sheen.style.rotate = `${-rot}deg`; // the highlight stays put while the ball turns
    };
    // from its place in the layout to a free ball that moves by translate (x and y are the corner of the ball as seen)
    const free = () => {
      if (homed) return;
      const r = el.getBoundingClientRect();
      const c = cover.getBoundingClientRect();
      x = r.left + r.width / 2 - size() / 2 - c.left - cover.clientLeft; // from its centre: turning does not move that
      y = r.top + r.height / 2 - size() / 2 - c.top - cover.clientTop;
      rot = homeTurn; // carry on from the turn the layout gave it
      if (slot) Object.assign(slot.style, { left: "0", top: "0", rotate: "none", scale: "none" });
      el.style.setProperty("--slot-scale", scale);
      el.classList.add("free");
      homed = true;
      put();
    };

    function step(now) {
      const dt = Math.min(0.033, (now - last) / 1000 || 0.016);
      last = now;
      if (!alive()) { raf = 0; return; }
      if (!drag) {
        vy += GRAVITY * dt;
        x += vx * dt;
        y += vy * dt;
        const maxX = width() - size();
        const maxY = height() - size();
        rot += spin * dt;
        spin *= 0.75 ** dt;
        if (x < 0) { x = 0; vx = -vx * BOUNCE; spin = -spin * 0.5 + vy * 0.2; }
        if (x > maxX) { x = maxX; vx = -vx * BOUNCE; spin = -spin * 0.5 - vy * 0.2; }
        if (y < 0) { y = 0; vy = -vy * BOUNCE; }
        if (y > maxY) {
          y = maxY;
          vy = -vy * BOUNCE;
          const r = size() / 2;
          const v = (5 * vx + 2 * ((spin * Math.PI) / 180) * r) / 7; // rolling friction on the floor
          vx = v * 0.92;
          spin = ((vx / r) * 180) / Math.PI;
          if (Math.abs(vy) < 60) vy = 0;
        }
      }
      put();
      if (drag || Math.abs(vx) > 4 || Math.abs(vy) > 0 || Math.abs(spin) > 8 || y < height() - size() - 0.5) raf = requestAnimationFrame(step);
      else { raf = 0; vx = 0; spin = 0; }
    }
    const run = () => { if (!raf) { last = performance.now(); raf = requestAnimationFrame(step); } };
    const kick = () => {
      free();
      if (reducedMotion()) { el.classList.remove("hop"); void el.offsetWidth; el.classList.add("hop"); return; }
      vy = -720;
      vx = (Math.random() - 0.5) * 420;
      spin = (Math.random() < 0.5 ? -1 : 1) * (800 + Math.random() * 900);
      run();
    };

    el.querySelector(":scope > .wd-mt")?.style.setProperty("rotate", `${-homeTurn}deg`); // the highlight stays put from the start

    // a cover that gets smaller (turning the phone) must not leave the ball outside it
    new ResizeObserver(() => {
      if (!homed || !alive()) return;
      x = Math.max(0, Math.min(width() - size(), x));
      y = Math.max(0, Math.min(height() - size(), y));
      put();
    }).observe(cover);

    el.addEventListener("pointerdown", (e) => {
      if (e.button) return;
      e.stopPropagation();
      free();
      drag = { sx: e.clientX, sy: e.clientY, ox: x, oy: y, moved: false, trail: [[performance.now(), x, y]] };
      try { el.setPointerCapture(e.pointerId); } catch { /* not capturable */ }
      vx = vy = 0;
      el.classList.add("held");
    });
    el.addEventListener("pointermove", (e) => {
      if (!drag) return;
      const dx = e.clientX - drag.sx;
      const dy = e.clientY - drag.sy;
      if (!drag.moved && Math.hypot(dx, dy) > 4) drag.moved = true;
      if (!drag.moved) return;
      x = Math.max(0, Math.min(width() - size(), drag.ox + dx));
      y = Math.max(0, Math.min(height() - size(), drag.oy + dy));
      put();
      const now = performance.now();
      drag.trail.push([now, x, y]);
      while (drag.trail.length > 2 && now - drag.trail[0][0] > 80) drag.trail.shift();
    });
    const release = (e) => {
      if (!drag) return;
      e?.stopPropagation();
      const d = drag;
      drag = null;
      el.classList.remove("held");
      if (!d.moved) { kick(); return; }
      if (reducedMotion()) { vx = vy = 0; return; }
      const [t0, x0, y0] = d.trail[0];
      const dt = Math.max(0.016, (performance.now() - t0) / 1000);
      vx = Math.max(-1600, Math.min(1600, (x - x0) / dt));
      vy = Math.max(-1600, Math.min(1600, (y - y0) / dt));
      spin = vx * 2.4 + (Math.random() - 0.5) * 300;
      run();
    };
    el.addEventListener("pointerup", release);
    el.addEventListener("pointercancel", release);
    el.addEventListener("click", (e) => e.stopPropagation());
    el.addEventListener("keydown", (e) => {
      if (e.key === "Enter" || e.key === " ") { e.preventDefault(); e.stopPropagation(); kick(); }
    });
  },
};
