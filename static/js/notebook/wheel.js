// The wheel: one notch per page, plus one before page 1 for the cover.
// Drag, flick or scroll it. It coasts, eases to a stop and settles on a notch, and every page it
// passes flips on the way, so a fast spin riffles through the book.

import { el, reducedMotion } from "./motion.js";

const SPRING = 150;
const DAMPING = 2 * Math.sqrt(SPRING);
const FRICTION = 3.2;
const WHEEL_DIRECT = 0.004;
const WHEEL_GAIN = 0.024;
const MAX_SPEED = 26;
const COVER = -1;

const clamp = (v, lo, hi) => Math.max(lo, Math.min(hi, v));

/**
 * @param {object} o
 * @param {HTMLElement} o.root
 * @param {object} o.data  table of contents
 * @param {string[]} o.order  page ids in turning order for this layout
 * @param {boolean} o.phone
 * @param {{ page(id: string, duration: number, input: number): void, open(input: number): void, close(input: number): void, rest?(): void, isClosed(): boolean, current(): string|null }} o.hooks
 *   `input` numbers what the visitor did: every turn one spin, drag, click or key press makes carries the same number.
 */
export function createWheel({ root, data, order, phone, hooks }) {
  const count = order.length;
  const step = Math.min(phone ? 16 : 14, 300 / count); // degrees per notch
  const radius = phone ? 100 : 196;
  const tickRadius = phone ? 112 : 212;
  const base = phone ? -90 : 0; // where notch 0 sits on the circle
  const firstOf = data.sections.map((s) => order.findIndex((id) => data.pages[id].section === s.id));

  const wrap = el("nav", "wheel", { "aria-label": "Page wheel" });
  wrap.innerHTML = `<div class="wheel-pointer"></div>
    <div class="wheel-dial" role="slider" tabindex="0" aria-label="Turn the pages" aria-valuemin="0" aria-valuemax="${count}">
      ${order.map((_, i) => `<i class="wheel-tick" style="--a:${base + i * step}deg;--tr:${tickRadius}px"></i>`).join("")}
      <div class="wheel-dot is-cover"><span class="wheel-hit" data-notch="${COVER}"><i></i></span></div>
      ${data.sections.map((s, k) => (firstOf[k] < 0 ? "" : `<div class="wheel-dot"><span class="wheel-hit" data-notch="${firstOf[k]}" data-section="${k}" style="--dot:var(--paper-${s.color})"><i></i></span></div>`)).join("")}
    </div>
    <div class="wheel-name"><b></b><small></small></div>`;
  root.append(wrap);
  const dial = wrap.querySelector(".wheel-dial");
  const buttons = [...dial.querySelectorAll(".wheel-hit")];
  const nameEl = wrap.querySelector(".wheel-name b");
  const subEl = wrap.querySelector(".wheel-name small");
  for (const b of buttons) {
    const angle = ((base + Number(b.dataset.notch) * step) * Math.PI) / 180;
    b.style.left = `${Math.cos(angle) * radius}px`;
    b.style.top = `${Math.sin(angle) * radius}px`;
  }

  // Position is in notches (a float); speed is notches per second.
  const nearest = (p) => clamp(Math.round(p), COVER, count - 1);
  let pos = COVER;
  let speed = 0;
  let target = null;
  let drag = null;
  let raf = 0;
  let lastFrame = 0;
  let shown = COVER; // the notch the book is showing
  let quiet = false; // something else turned the page; glide without flipping again
  let lastInput = 0;
  let scrollAcc = 0;
  let input = 0; // which visitor input the flips belong to: a spin of the wheel, a drag, a click, one key press
  let lastWheelAt = -Infinity;
  const aimedBy = new Map(); // notch -> the key press that aimed the wheel at it, so each press's page is its own input
  let samples = [];

  function render() {
    dial.style.rotate = `${-pos * step}deg`;
    const i = nearest(pos);
    if (i < 0) {
      for (const b of buttons) b.classList.toggle("is-current", b.dataset.notch === String(COVER));
      nameEl.textContent = "Cover";
      subEl.textContent = "";
      dial.setAttribute("aria-valuenow", 0);
      dial.setAttribute("aria-valuetext", "Cover");
      return;
    }
    const id = order[i];
    const info = data.pages[id];
    const k = data.sections.findIndex((s) => s.id === info.section);
    for (const b of buttons) b.classList.toggle("is-current", b.dataset.section === String(k));
    nameEl.textContent = data.sections[k].tab;
    subEl.textContent = `p.${i + 1}`;
    dial.setAttribute("aria-valuenow", i + 1);
    dial.setAttribute("aria-valuetext", `${info.title}, page ${i + 1}`);
  }

  function flipTo() {
    const i = nearest(pos);
    if (i === shown) return;
    if (quiet) { shown = i; return; }
    const duration = clamp(700 - Math.abs(speed) * 38, 230, 700);
    const dir = i > shown ? 1 : -1;
    while (shown !== i) {
      shown += dir;
      const by = aimedBy.get(shown) ?? input;
      if (shown < 0) { hooks.close(by); continue; }
      if (shown === 0 && dir > 0 && hooks.isClosed()) { hooks.open(by); continue; }
      hooks.page(order[shown], duration, by);
    }
  }

  function frame(t) {
    const dt = Math.min(0.05, (t - lastFrame) / 1000 || 0.016);
    lastFrame = t;
    if (drag) {
      // the position follows the finger
    } else if (target !== null) {
      if (reducedMotion()) { pos = target; speed = 0; } else {
        speed += (-SPRING * (pos - target) - DAMPING * speed) * dt;
        pos += speed * dt;
      }
      if (Math.abs(pos - target) < 0.003 && Math.abs(speed) < 0.03) { pos = target; speed = 0; target = null; quiet = false; }
    } else {
      speed *= Math.exp(-FRICTION * dt);
      pos += speed * dt;
      if (pos < COVER || pos > count - 1) target = nearest(pos);
      else if (Math.abs(speed) < 1.4 && t - lastInput > 140) target = nearest(pos + speed * 0.08);
    }
    render();
    flipTo();
    raf = drag || target !== null || Math.abs(speed) > 0.01 ? requestAnimationFrame(frame) : 0;
    if (!raf) hooks.rest?.(); // the wheel has come to rest: whatever it turned is done
  }
  const kick = () => { if (!raf) { lastFrame = performance.now(); raf = requestAnimationFrame(frame); } };
  const take = () => {
    if (!quiet) return;
    quiet = false;
    shown = hooks.isClosed() ? COVER : Math.max(0, order.indexOf(hooks.current()));
  };

  // scrolling over the wheel turns it and keeps the page still
  wrap.addEventListener("wheel", (e) => {
    e.preventDefault();
    take();
    const now = performance.now();
    if (now - lastWheelAt > 400) input += 1; // a pause ends one spin; the next scroll starts another
    lastWheelAt = now;
    aimedBy.clear();
    let d = Math.abs(e.deltaY) >= Math.abs(e.deltaX) ? e.deltaY : e.deltaX;
    d *= e.deltaMode === 1 ? 33 : e.deltaMode === 2 ? 400 : 1;
    if (reducedMotion()) {
      scrollAcc += d;
      if (Math.abs(scrollAcc) >= 70) { target = nearest(Math.round(pos) + Math.sign(scrollAcc)); scrollAcc = 0; kick(); }
      return;
    }
    target = null;
    lastInput = performance.now();
    pos = clamp(pos + d * WHEEL_DIRECT, COVER - 0.4, count - 0.6);
    speed = clamp(speed + d * WHEEL_GAIN, -MAX_SPEED, MAX_SPEED);
    kick();
  }, { passive: false });

  // drag and flick
  const angleOf = (e) => {
    const r = dial.getBoundingClientRect();
    return (Math.atan2(e.clientY - (r.top + r.height / 2), e.clientX - (r.left + r.width / 2)) * 180) / Math.PI;
  };
  const rubber = (p) => (p < COVER ? COVER + (p - COVER) * 0.3 : p > count - 1 ? count - 1 + (p - (count - 1)) * 0.3 : p);
  dial.addEventListener("pointerdown", (e) => {
    if (e.button) return;
    take();
    input += 1;
    aimedBy.clear();
    drag = { angle: angleOf(e), raw: pos, moved: false, target: e.target };
    target = null;
    speed = 0;
    samples = [[performance.now(), pos]];
    try { dial.setPointerCapture(e.pointerId); } catch { /* not capturable */ }
    kick();
  });
  dial.addEventListener("pointermove", (e) => {
    if (!drag) return;
    let da = angleOf(e) - drag.angle;
    if (da > 180) da -= 360;
    if (da < -180) da += 360;
    if (!drag.moved && Math.abs(da) > 3) { drag.moved = true; dial.classList.add("is-dragging"); }
    if (!drag.moved) return;
    drag.angle = angleOf(e);
    drag.raw -= da / step;
    pos = rubber(drag.raw);
    const now = performance.now();
    samples.push([now, pos]);
    while (samples.length > 2 && now - samples[0][0] > 90) samples.shift();
  });
  const release = () => {
    if (!drag) return;
    const { moved, target: hit } = drag;
    drag = null;
    dial.classList.remove("is-dragging");
    if (moved) {
      const [t0, p0] = samples[0];
      const now = performance.now();
      speed = reducedMotion() ? 0 : clamp(now - t0 > 8 ? (pos - p0) / ((now - t0) / 1000) : 0, -MAX_SPEED, MAX_SPEED);
      lastInput = 0;
      if (reducedMotion() || Math.abs(speed) < 1.4) target = nearest(pos + speed * 0.08);
    } else {
      const dot = hit.closest && hit.closest(".wheel-hit");
      target = dot ? Number(dot.dataset.notch) : nearest(pos);
    }
    kick();
  };
  dial.addEventListener("pointerup", release);
  dial.addEventListener("pointercancel", release);
  dial.addEventListener("keydown", (e) => {
    const k = { ArrowRight: 1, ArrowDown: 1, PageDown: 1, ArrowLeft: -1, ArrowUp: -1, PageUp: -1 }[e.key];
    if (!k) return;
    e.preventDefault();
    take();
    input += 1;
    target = nearest((target ?? Math.round(pos)) + k);
    aimedBy.set(target, input);
    speed = 0;
    kick();
  });

  render();
  return {
    /** Something else turned the page (a corner, a swipe, a link): glide the wheel there without flipping again. */
    sync(id) {
      const i = id === "cover" ? COVER : order.indexOf(id);
      if (i < COVER) return;
      quiet = true;
      shown = i;
      target = i;
      speed = 0;
      kick();
    },
    /** Put the wheel on a notch with no glide. */
    set(id) {
      const i = id === "cover" ? COVER : order.indexOf(id);
      pos = i;
      shown = i;
      target = null;
      speed = 0;
      render();
    },
    destroy() {
      if (raf) cancelAnimationFrame(raf);
      wrap.remove();
    },
  };
}
