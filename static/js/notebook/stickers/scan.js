// The scan pad. It writes a word, scans it and types it out; write on it yourself and it reads what you wrote.
//
// Reading is real: the strokes are kept, split by the pad's ruled rows, and each row goes to a small handwriting model
// that runs in a worker (ocr.js). The model (about 65 MB) is fetched only when someone first writes on the pad or presses
// "scan", and the browser keeps it after that. Until then the pad just plays its little word demo.

import { reducedMotion } from "./common.js";
import { ocr, preload } from "./ocr.js";
import { ROWS, rasterRow, splitRows } from "./ink.js";

const WORDS = ["hello", "notes", "ideas", "hi there"];
const PAUSE_MS = 1500; // after the pen lifts, wait this long for more writing before reading it
const LINGER_MS = 12000; // a result stays this long (plus a little per letter), then the pad clears and the demo resumes
const GUARD_MS = 400; // the click that ends a stroke is not a tap, for this long

export const scan = {
  html: () => `<div class="wd wd-scan"><div class="sc-pad"><svg viewBox="0 0 220 64" aria-hidden="true"><text x="12" y="46" class="sc-w"></text></svg><canvas aria-label="Write here and the pad reads it"></canvas><i class="sc-bar"></i><button type="button" class="sc-clear" aria-label="Clear the pad" title="Clear" hidden><i aria-hidden="true"></i></button></div>
    <div class="sc-out"><i class="sc-pg"></i><span class="sc-k">It reads</span><code class="sc-t" aria-hidden="true"></code><button type="button" class="sc-go" hidden>scan</button></div><span class="sr-only" role="status"></span></div>`,

  wire(card, { alive }) {
    const word = card.querySelector(".sc-w");
    const bar = card.querySelector(".sc-bar");
    const out = card.querySelector(".sc-t");
    const progress = card.querySelector(".sc-pg");
    const go = card.querySelector(".sc-go");
    const clearButton = card.querySelector(".sc-clear");
    const announce = card.querySelector(".sr-only");
    const canvas = card.querySelector("canvas");
    const ink = canvas.getContext("2d");
    let cycles = 0;
    let index = 0;
    let timers = [];
    let shown = ""; // the text the typing is heading for, so a stroke that interrupts it can finish it at once

    const later = (fn, ms) => timers.push(setTimeout(() => alive() && fn(), ms));
    const clear = () => { timers.forEach(clearTimeout); timers = []; };
    const say = (text) => { announce.textContent = text; };

    /** idle: the demo plays · ink: writing waits to be read · load / read: working · done: a result · error: something failed · off: reading is switched off here */
    const setState = (state) => {
      card.dataset.state = state;
      go.hidden = state !== "ink" && state !== "error";
      clearButton.hidden = !strokes.length; // there is something to clear once there is ink
      go.textContent = state === "error" ? "retry" : "scan";
      bar.classList.toggle("loop", state === "read");
      progress.classList.toggle("busy", state === "read" || (state === "load" && !progress.style.getPropertyValue("--p")));
    };
    /** Plain words in the result's place. With a percentage the bar fills to it; without, the bar just keeps moving. */
    const message = (text, pct) => {
      shown = "";
      out.classList.add("msg");
      out.textContent = text;
      if (pct === undefined) progress.style.removeProperty("--p");
      else progress.style.setProperty("--p", String(pct / 100));
    };
    const blank = () => {
      shown = "";
      out.classList.remove("msg");
      out.textContent = "";
      progress.style.removeProperty("--p");
    };

    function type(text, then) {
      shown = text;
      out.classList.remove("msg");
      out.textContent = "";
      const spoken = `The pad read: ${text.replace(/\n/g, ", ")}`;
      if (reducedMotion()) { out.textContent = text; say(spoken); then?.(); return; }
      const step = Math.max(10, Math.min(55, 1400 / text.length));
      let k = 0;
      card.classList.add("typing");
      const tick = () => {
        out.textContent = text.slice(0, ++k);
        if (k < text.length) later(tick, step);
        else { say(spoken); later(() => card.classList.remove("typing"), 200); then?.(); }
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

    // the word demo: it writes each word once, then rests (and always rests with reduced motion)
    function demo() {
      clear();
      if (strokes.length) return;
      if (cycles++ >= WORDS.length || (reducedMotion() && cycles > 1)) return;
      const w = WORDS[index++ % WORDS.length];
      word.textContent = w;
      word.classList.remove("wr");
      void card.offsetWidth;
      word.classList.add("wr");
      blank();
      later(() => sweep(() => type(w, () => later(demo, 2600))), reducedMotion() ? 0 : 1500);
    }

    // ---- what is written is kept as points (in the pad's own pixels) and drawn as it goes
    let strokes = []; // each a list of [x, y]
    let pen = null; // the stroke being written
    let penId = -1;
    let epoch = 0; // bumped whenever the pad is wiped, so a late answer for old writing is dropped
    let version = 0; // bumped on every new stroke, so an answer for writing that has since grown is not shown as final
    const results = new Map(); // ruled row -> { key, text }
    let readTimer = 0;
    let clearTimer = 0;

    const fit = () => {
      const s = 2;
      canvas.width = canvas.clientWidth * s;
      canvas.height = canvas.clientHeight * s;
      ink.setTransform(s, 0, 0, s, 0, 0);
      ink.lineCap = ink.lineJoin = "round";
      ink.lineWidth = 2.6;
      ink.strokeStyle = ink.fillStyle = "#0b4f9c";
    };
    // offsetX and offsetY are in the canvas's own (untilted, unscaled) pixels: the sticker sits turned on the cover
    const at = (e) => [e.offsetX, e.offsetY];

    // ---- the reader (ocr.ready says whether the worker is up with the model; it goes false again if the worker dies)
    let active = 0; // reads asked for and not yet finished

    /** Start (or join) the load. Progress shows while the card is waiting on it; once ready, a card that only had the loading note goes back to waiting. */
    function warm() {
      return ocr.load((pct) => {
        if (ocr.ready || !alive() || (card.dataset.state !== "ink" && card.dataset.state !== "load")) return;
        const starting = pct >= 99; // every byte is here; the model is being set up
        if (starting) message("Starting reader\u2026");
        else if (pct < 1) message("Loading reader\u2026"); // nothing has arrived yet: the bar keeps moving instead of sitting empty
        else message(`Loading reader ${pct}%`, pct);
        setState("load");
      }).then(() => {
        if (!active && alive() && card.dataset.state === "load") { blank(); setState("ink"); } // it was loading in the background while they wrote
      });
    }
    /** The background load a first stroke starts. If it fails while nothing is waiting on it, say so now (with retry) rather than sit on a stale percentage. */
    function warmInBackground() {
      warm().catch((error) => {
        if (active || !alive() || ocr.off || card.dataset.state !== "load") return; // a read in flight reports its own failure
        console.warn("scan pad:", error);
        clearTimeout(readTimer); // the error stays until they press retry
        const text = navigator.onLine === false ? "Offline. Check your connection" : "Couldn\u2019t load the reader";
        setState("error");
        message(text);
        say(text);
      });
    }

    const rowKey = (r) => `${r.strokes.length}:${r.strokes.reduce((n, s) => n + s.length, 0)}`;

    async function read() {
      clearTimeout(readTimer);
      clearTimeout(clearTimer);
      const mine = epoch;
      const seen = version;
      if (ocr.off) { showOff(); return; }
      let rows;
      try { rows = splitRows(strokes, canvas.clientHeight); } catch { rows = []; }
      if (!rows.length) {
        message("Nothing to read yet");
        setState("done");
        clearTimer = setTimeout(() => alive() && mine === epoch && wipe(), 3000);
        return;
      }
      active++;
      let stage = "load";
      try {
        if (!ocr.ready) {
          setState("load");
          message("Loading reader\u2026");
          say("Loading the reader");
          await warm();
          if (mine !== epoch || !alive()) return;
        }
        stage = "read";
        setState("read");
        message("Reading…");
        say("Reading");
        const pitch = canvas.clientHeight / ROWS;
        const todo = rows.filter((r) => results.get(r.row)?.key !== rowKey(r)); // rows already read and unchanged are kept
        const keys = todo.map(rowKey);
        const lines = todo.length ? await ocr.read(todo.map((r) => rasterRow(r.strokes, pitch))) : [];
        if (mine !== epoch || !alive()) return;
        todo.forEach((r, i) => results.set(r.row, { key: keys[i], text: lines[i] }));
        if (seen !== version) return; // more was written meanwhile; the read that follows it shows the answer
        const text = rows.map((r) => results.get(r.row)?.text).filter(Boolean).join("\n");
        setState("done");
        if (text) { progress.style.removeProperty("--p"); sweep(() => type(text)); }
        else { message("Couldn’t read that"); say("Couldn’t read that"); }
        clearTimer = setTimeout(() => alive() && mine === epoch && wipe(), LINGER_MS + text.length * 60);
      } catch (error) {
        if (mine !== epoch || !alive() || ocr.off) return; // (switching off shows its own note)
        console.warn("scan pad:", error);
        setState("error");
        const text = stage === "read" ? "Couldn’t read that" : navigator.onLine === false ? "Offline. Check your connection" : "Couldn’t load the reader";
        message(text);
        say(text);
      } finally {
        if (mine === epoch) active--; // (a clear has already zeroed the count)
      }
    }

    // ---- reading switched off (the page struggled while the reader worked): the pad stays a drawing pad, with a calm note
    const OFF_NOTE = "Reading is off on this device";
    function showOff() {
      clearTimeout(readTimer);
      clearTimeout(clearTimer);
      setState("off");
      message(OFF_NOTE);
      say(OFF_NOTE);
      if (!pen) clearTimer = setTimeout(() => alive() && !pen && wipe(), LINGER_MS); // like a result, the drawing stays a while, then the pad clears
    }
    ocr.onOff(() => {
      if (alive() && (strokes.length || card.dataset.state !== "idle")) showOff(); // if nobody has touched the pad, the note waits for the first stroke
    }, alive);

    /** Back to a blank pad. Anything being read for the old writing is called off; a loaded model stays loaded. */
    function reset() {
      clearTimeout(readTimer);
      clearTimeout(clearTimer);
      clear(); // the demo's and the typing's timers
      epoch++; // an answer still on its way for the old writing is dropped when it lands
      active = 0; // and the reads asked for are forgotten (their own bookkeeping, below, no longer counts)
      ocr.cancel(); // and the reader stops spending time on it
      strokes = [];
      pen = null;
      results.clear();
      ink.clearRect(0, 0, canvas.width, canvas.height);
      card.classList.remove("typing");
      word.classList.remove("wr");
      word.textContent = "";
      blank();
      setState("idle");
    }

    /** The pad clears itself a while after a result, and the little word demo starts again. */
    function wipe() {
      reset();
      cycles = 0;
      demo();
    }

    /** The clear button: blank, and quiet (no demo restarting over the empty pad). */
    function clearPad() {
      reset();
      cycles = WORDS.length;
      say("Pad cleared");
    }

    // ---- strokes. Every one of them belongs to the pad: none may turn the page or open the cover.
    // The canvas captures the pointer, so the release comes back here even if the pen has left the pad. If a browser
    // does not honour that, the release is still stopped at the document before it can reach the page's swipe handlers.
    // Everything else that could reach the page's swipe and tap handlers is stopped at the pad, and the click that some
    // browsers send when a drag ends (to the nearest element both ends share, which can lie outside the pad) is swallowed.
    let guardUntil = 0;
    const swallow = (e) => {
      if (!alive()) { document.removeEventListener(e.type, swallow, true); return; }
      // only the click aimed at the canvas or something around it (what a drag that ended elsewhere sends); a press on the pad's own button, or on another sticker, is a real one
      if (performance.now() < guardUntil && e.target.contains(canvas)) { e.stopPropagation(); e.preventDefault(); }
    };
    document.addEventListener("click", swallow, true);
    document.addEventListener("dblclick", swallow, true);

    const finish = (e) => {
      if (!alive()) { document.removeEventListener(e.type, finish, true); return; }
      if (!pen || e.pointerId !== penId) return;
      e.stopPropagation(); // the release is the pad's, wherever it landed
      guardUntil = performance.now() + GUARD_MS;
      pen = null;
      clearTimeout(readTimer);
      readTimer = setTimeout(() => alive() && read(), PAUSE_MS);
    };
    document.addEventListener("pointerup", finish, true);
    document.addEventListener("pointercancel", finish, true);

    for (const type of ["mousedown", "mouseup", "dblclick", "auxclick", "touchstart", "touchmove", "touchend", "contextmenu"]) {
      card.addEventListener(type, (e) => { e.stopPropagation(); if (type === "contextmenu" || type === "touchmove") e.preventDefault(); }, { passive: false });
    }
    // two fingers sliding on a trackpad (or a wheel) over the pad is not for the page either: it must not scroll or swipe back
    card.addEventListener("wheel", (e) => { e.preventDefault(); e.stopPropagation(); }, { passive: false });

    canvas.addEventListener("pointerdown", (e) => {
      e.stopPropagation();
      e.preventDefault();
      if (e.button || !e.isPrimary) return;
      if (!canvas.width || !strokes.length) fit();
      clear();
      clearTimeout(readTimer);
      clearTimeout(clearTimer);
      card.classList.remove("typing");
      if (shown) { out.textContent = shown; shown = ""; } // finish a result that was still typing
      version++;
      word.classList.remove("wr");
      word.textContent = "";
      if (!strokes.length || (out.classList.contains("msg") && card.dataset.state !== "load")) blank(); // an old note (nothing to read, couldn't read) goes when writing resumes
      pen = [at(e)];
      penId = e.pointerId;
      strokes.push(pen);
      ink.beginPath();
      ink.arc(...pen[0], 1.3, 0, Math.PI * 2);
      ink.fill();
      const state = card.dataset.state;
      if (ocr.off) showOff();
      else if (state === "read") { blank(); setState("ink"); } // the answer being worked out is for writing that is about to change
      else if (state !== "load") setState("ink");
      if (!ocr.off && !ocr.ready) warmInBackground(); // the first stroke starts the download
      try { canvas.setPointerCapture(e.pointerId); } catch { /* not capturable */ }
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!pen || e.pointerId !== penId) return;
      const p = at(e);
      const last = pen[pen.length - 1];
      if (p[0] === last[0] && p[1] === last[1]) return;
      ink.beginPath();
      ink.moveTo(...last);
      ink.lineTo(...p);
      ink.stroke();
      pen.push(p);
    });

    go.addEventListener("click", () => read());
    clearButton.addEventListener("click", clearPad);

    setState("idle");
    demo();
    if (card.closest(".nb")?.classList.contains("is-closed")) preload(() => Boolean(document.querySelector(".nb--phone"))); // the pad is in view (the cover is shut): get the reader ready quietly, except on a phone
  },
};
