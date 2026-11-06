// The ScribbleScan pad. It writes a word, scans it and types it out. Draw on it and it "scans" your doodle too.
// (The typed result is a stand-in: the preserved ScribbleScan could read handwriting, this pad only plays the part.)

import { reducedMotion } from "./common.js";

const WORDS = ["hello", "notes", "ideas", "hi there"];
const DOODLE_RESULT = "1 doodle, saved";

export const scan = {
  html: () => `<div class="wd wd-scan"><div class="sc-pad"><svg viewBox="0 0 220 64" aria-hidden="true"><text x="12" y="46" class="sc-w"></text></svg><canvas aria-label="Write or draw here"></canvas><i class="sc-bar"></i></div>
    <div class="sc-out"><span class="sc-k">ScribbleScan</span><code class="sc-t" aria-hidden="true"></code></div><span class="sr-only" role="status"></span></div>`,

  wire(card, { alive }) {
    const word = card.querySelector(".sc-w");
    const bar = card.querySelector(".sc-bar");
    const out = card.querySelector(".sc-t");
    const announce = card.querySelector(".sr-only");
    let cycles = 0;
    const canvas = card.querySelector("canvas");
    let index = 0;
    let timers = [];
    let drawing = false;
    const later = (fn, ms) => timers.push(setTimeout(() => alive() && fn(), ms));
    const clear = () => { timers.forEach(clearTimeout); timers = []; };

    function type(text, then) {
      out.textContent = "";
      announce.textContent = "";
      if (reducedMotion()) { out.textContent = text; announce.textContent = `ScribbleScan read: ${text}`; then?.(); return; }
      let k = 0;
      card.classList.add("typing");
      const tick = () => {
        out.textContent = text.slice(0, ++k);
        if (k < text.length) later(tick, 55);
        else { announce.textContent = `ScribbleScan read: ${text}`; later(() => card.classList.remove("typing"), 200); then?.(); }
      };
      tick();
    }
    function sweep(then) {
      if (reducedMotion()) { then(); return; }
      bar.classList.remove("go");
      void bar.offsetWidth;
      bar.classList.add("go");
      later(then, 620);
    }
    function demo() {
      clear();
      if (drawing) return;
      // the pad shows each word once, then rests (and always rests with reduced motion)
      if (cycles++ >= WORDS.length || (reducedMotion() && cycles > 1)) return;
      const w = WORDS[index++ % WORDS.length];
      word.textContent = w;
      word.classList.remove("wr");
      void card.offsetWidth;
      word.classList.add("wr");
      out.textContent = "";
      later(() => sweep(() => type(w, () => later(demo, 2600))), reducedMotion() ? 0 : 1500);
    }

    // drawing
    const ink = canvas.getContext("2d");
    let pen = null;
    let inked = false;
    const fit = () => {
      const s = 2;
      canvas.width = canvas.clientWidth * s;
      canvas.height = canvas.clientHeight * s;
      ink.setTransform(s, 0, 0, s, 0, 0);
      ink.lineCap = ink.lineJoin = "round";
      ink.lineWidth = 2.6;
      ink.strokeStyle = "#0b4f9c";
    };
    const at = (e) => { const r = canvas.getBoundingClientRect(); return [e.clientX - r.left, e.clientY - r.top]; };
    canvas.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      if (e.button) return;
      if (!canvas.width || !inked) fit();
      clear();
      card.classList.remove("typing");
      drawing = true;
      word.classList.remove("wr");
      word.textContent = "";
      out.textContent = "";
      pen = at(e);
      inked = true;
      try { canvas.setPointerCapture(e.pointerId); } catch { /* not capturable */ }
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!pen) return;
      const p = at(e);
      ink.beginPath();
      ink.moveTo(...pen);
      ink.lineTo(...p);
      ink.stroke();
      pen = p;
    });
    const lift = (e) => {
      if (!pen) return;
      e?.stopPropagation();
      pen = null;
      clear();
      later(() => sweep(() => type(DOODLE_RESULT, () => later(() => {
        ink.clearRect(0, 0, canvas.width, canvas.height);
        inked = false;
        drawing = false;
        cycles = 0;
        demo();
      }, 2200))), 700);
    };
    canvas.addEventListener("pointerup", lift);
    canvas.addEventListener("pointercancel", lift);
    demo();
  },
};
