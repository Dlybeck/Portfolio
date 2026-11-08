// "Your sticker": an empty spot you can fill by drawing or adding a picture, in a shape and colour you pick.
// It stays in this browser only.

import { tap } from "./common.js";

const KEY = "nb-your-sticker"; // the picture, a data address (older stickers: an opaque white JPEG)
const STYLE_KEY = "nb-your-sticker-style"; // {"shape": ..., "bg": ...}; older stickers have none, which means the original look
const SIZE = 400; // the drawing is square, then shown in the chosen shape
const PENS = [["#1b2436", "Ink"], ["#0062cc", "Blue"], ["#c8372d", "Red"], ["#2e8b57", "Green"], ["#f2b705", "Yellow"]];
/** The shapes (their outlines are in stickers.css). The first is the original look. */
export const SHAPES = [["circle", "Circle"], ["rounded", "Rounded square"], ["square", "Square"], ["pentagon", "Pentagon"], ["hexagon", "Hexagon"], ["triangle", "Triangle"], ["diamond", "Diamond"]];
/** Shapes that were offered before and are gone now; a saved one becomes the circle. */
const RETIRED = ["star", "heart"];
/** Backgrounds, from the site's paper colours (stickers.css has the dark ink on each, all well over 4.5:1). The first is the original look. */
export const SWATCHES = [["white", "White", "#ffffff"], ["lemon", "Lemon", "#ffe94d"], ["pink", "Pink", "#ff8fcf"], ["tangerine", "Tangerine", "#ffb238"], ["mint", "Mint", "#6cf0b0"], ["sky", "Sky", "#a5d0fd"]];
const DEFAULT_STYLE = { shape: SHAPES[0][0], bg: SWATCHES[0][0] };

const read = (key) => { try { return localStorage.getItem(key); } catch { return null; } };
const write = (key, value) => { try { value ? localStorage.setItem(key, value) : localStorage.removeItem(key); } catch { /* storage may be blocked */ } };

/** Whatever was saved, made safe: anything missing, damaged or unknown means the original look. */
export function readStyle(raw) {
  let saved = null;
  try { saved = raw ? JSON.parse(raw) : null; } catch { saved = null; }
  if (!saved || typeof saved !== "object") return null;
  const shape = SHAPES.some(([id]) => id === saved.shape) ? saved.shape : DEFAULT_STYLE.shape;
  const bg = SWATCHES.some(([id]) => id === saved.bg) ? saved.bg : DEFAULT_STYLE.bg;
  return shape === DEFAULT_STYLE.shape && bg === DEFAULT_STYLE.bg ? null : { shape, bg };
}
const sameStyle = (a, b) => (a?.shape ?? DEFAULT_STYLE.shape) === (b?.shape ?? DEFAULT_STYLE.shape) && (a?.bg ?? DEFAULT_STYLE.bg) === (b?.bg ?? DEFAULT_STYLE.bg);
const swatch = (id) => SWATCHES.find(([s]) => s === id) ?? SWATCHES[0];

let mine = read(KEY);
let style = readStyle(read(STYLE_KEY)); // null = the original look
let dialog = null;
let canvas = null;
let pen = null;
let color = PENS[0][0];
let dirty = false;
let photo = false; // a picture was added (it fills the shape, so it is saved as a JPEG)
let choice = { ...DEFAULT_STYLE }; // what the dialog currently shows

function paintAll() {
  const shape = style?.shape ?? DEFAULT_STYLE.shape;
  for (const el of document.querySelectorAll(".wd-mine")) {
    el.classList.toggle("has", Boolean(mine));
    el.classList.toggle("styled", Boolean(style));
    el.dataset.shape = shape;
    el.style.setProperty("--sticker-bg", swatch(style?.bg)[2]);
    el.querySelector(".mn-img").style.backgroundImage = mine ? `url("${mine}")` : "";
    el.setAttribute("aria-label", mine || style ? "Your sticker. Tap to change it." : "your sticker here. Tap to draw one or add a picture.");
  }
}

function blank() {
  canvas.getContext("2d").clearRect(0, 0, SIZE, SIZE);
  dirty = false;
  photo = false;
}

function showChoice() {
  dialog.dataset.shape = choice.shape;
  dialog.style.setProperty("--sticker-bg", swatch(choice.bg)[2]);
  dialog.querySelectorAll("[data-shape-pick]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.shapePick === choice.shape));
  dialog.querySelectorAll("[data-bg-pick]").forEach((b) => b.setAttribute("aria-pressed", b.dataset.bgPick === choice.bg));
}

function build() {
  dialog = document.createElement("dialog");
  dialog.className = "maker";
  dialog.setAttribute("aria-labelledby", "maker-title");
  dialog.innerHTML = `<form method="dialog" class="maker-in">
    <h2 id="maker-title">Make your sticker</h2>
    <p class="maker-note">Draw on the sticker, or add a picture and draw on top. It stays in this browser only.</p>
    <div class="maker-stage"><div class="maker-shape-wrap"><canvas width="${SIZE}" height="${SIZE}" aria-label="Drawing area"></canvas></div></div>
    <div class="maker-tools">
      <div class="maker-pens" role="group" aria-label="Pen color">${PENS.map(([c, label], i) => `<button type="button" data-color="${c}" aria-label="${label} pen" aria-pressed="${i === 0}" style="--c:${c}"></button>`).join("")}</div>
      <label class="maker-btn">Add a picture<input class="sr-only" type="file" accept="image/*"></label>
      <button type="button" class="maker-btn" data-action="clear">Clear</button>
    </div>
    <div class="maker-look">
      <div class="maker-opts" role="group" aria-label="Shape">${SHAPES.map(([id, label]) => `<button type="button" class="maker-shape" data-shape-pick="${id}" data-shape="${id}" aria-label="${label}" aria-pressed="false"></button>`).join("")}</div>
      <div class="maker-opts" role="group" aria-label="Background color">${SWATCHES.map(([id, label, hex]) => `<button type="button" class="maker-swatch" data-bg-pick="${id}" aria-label="${label} background" aria-pressed="false" style="--c:${hex}"></button>`).join("")}</div>
    </div>
    <div class="maker-foot">
      <button type="button" class="maker-btn quiet" data-action="off">Take it off</button>
      <span class="maker-gap"></span>
      <button type="button" class="maker-btn" data-action="cancel">Cancel</button>
      <button type="button" class="maker-btn primary" data-action="done">Stick it on</button>
    </div></form>`;
  document.body.append(dialog);
  canvas = dialog.querySelector("canvas");
  const g = canvas.getContext("2d");
  const at = (e) => { const r = canvas.getBoundingClientRect(); return [((e.clientX - r.left) * SIZE) / r.width, ((e.clientY - r.top) * SIZE) / r.height]; };
  canvas.addEventListener("pointerdown", (e) => {
    if (e.button) return;
    e.preventDefault();
    pen = at(e);
    try { canvas.setPointerCapture(e.pointerId); } catch { /* not capturable */ }
    g.fillStyle = color;
    g.beginPath();
    g.arc(pen[0], pen[1], 3, 0, 7);
    g.fill();
    dirty = true;
  });
  canvas.addEventListener("pointermove", (e) => {
    if (!pen) return;
    const p = at(e);
    g.strokeStyle = color;
    g.lineWidth = 6;
    g.lineCap = g.lineJoin = "round";
    g.beginPath();
    g.moveTo(...pen);
    g.lineTo(...p);
    g.stroke();
    pen = p;
  });
  const lift = () => { pen = null; };
  canvas.addEventListener("pointerup", lift);
  canvas.addEventListener("pointercancel", lift);
  dialog.querySelectorAll(".maker-pens button").forEach((b) => b.addEventListener("click", () => {
    color = b.dataset.color;
    dialog.querySelectorAll(".maker-pens button").forEach((x) => x.setAttribute("aria-pressed", x === b));
  }));
  dialog.querySelectorAll("[data-shape-pick]").forEach((b) => b.addEventListener("click", () => { choice.shape = b.dataset.shapePick; showChoice(); }));
  dialog.querySelectorAll("[data-bg-pick]").forEach((b) => b.addEventListener("click", () => { choice.bg = b.dataset.bgPick; showChoice(); }));
  dialog.querySelector("input[type=file]").addEventListener("change", (e) => {
    const file = e.target.files?.[0];
    e.target.value = "";
    if (!file || !file.type.startsWith("image/")) return;
    const url = URL.createObjectURL(file);
    const image = new Image();
    image.onload = () => {
      blank();
      const scale = Math.max(SIZE / image.width, SIZE / image.height);
      g.drawImage(image, (SIZE - image.width * scale) / 2, (SIZE - image.height * scale) / 2, image.width * scale, image.height * scale);
      URL.revokeObjectURL(url);
      dirty = true;
      photo = true;
    };
    image.onerror = () => URL.revokeObjectURL(url);
    image.src = url;
  });
  dialog.addEventListener("click", (e) => {
    const action = e.target.closest("[data-action]")?.dataset.action;
    if (action === "clear") blank();
    else if (action === "cancel") dialog.close();
    else if (action === "off") { mine = null; style = null; write(KEY, null); write(STYLE_KEY, null); paintAll(); dialog.close(); }
    else if (action === "done") {
      if (dirty) {
        // a drawing keeps its see-through background (so the colour shows behind it); a picture fills the shape
        mine = photo ? canvas.toDataURL("image/jpeg", 0.86) : canvas.toDataURL("image/png");
        write(KEY, mine);
      }
      if (!sameStyle(choice, style)) {
        style = readStyle(JSON.stringify(choice));
        write(STYLE_KEY, style ? JSON.stringify(style) : null);
      }
      paintAll();
      dialog.close();
    }
  });
}

function open() {
  if (!dialog) build();
  blank();
  choice = { ...DEFAULT_STYLE, ...(style ?? {}) };
  showChoice();
  dialog.querySelector('[data-action="off"]').hidden = !mine && !style;
  if (mine) {
    const image = new Image();
    image.onload = () => { canvas.getContext("2d").drawImage(image, 0, 0, SIZE, SIZE); dirty = false; photo = mine.startsWith("data:image/jpeg"); };
    image.src = mine;
  }
  dialog.showModal();
}

export const blankSticker = {
  html: () => `<div class="wd wd-blank wd-round wd-mine" role="button" tabindex="0" aria-label="your sticker here. Tap to draw one or add a picture."><span class="mn-shape"><span class="mn-t">your<br>sticker<br>here</span><i class="mn-img" aria-hidden="true"></i></span></div>`,
  wire(sticker) {
    tap(sticker, open);
    paintAll();
  },
};
