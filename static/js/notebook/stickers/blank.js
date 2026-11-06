// "Your sticker": an empty spot you can fill by drawing or adding a picture. It stays in this browser only.

import { tap } from "./common.js";

const KEY = "nb-your-sticker";
const SIZE = 400; // the drawing is square, shown in a circle
const PENS = [["#1b2436", "Ink"], ["#0062cc", "Blue"], ["#c8372d", "Red"], ["#2e8b57", "Green"], ["#f2b705", "Yellow"]];

const store = {
  get() { try { return localStorage.getItem(KEY); } catch { return null; } },
  set(value) { try { value ? localStorage.setItem(KEY, value) : localStorage.removeItem(KEY); } catch { /* storage may be blocked */ } },
};

let mine = store.get();
let dialog = null;
let canvas = null;
let pen = null;
let color = PENS[0][0];
let dirty = false;

function paintAll() {
  for (const el of document.querySelectorAll(".wd-mine")) {
    el.classList.toggle("has", Boolean(mine));
    el.querySelector(".mn-img").style.backgroundImage = mine ? `url("${mine}")` : "";
    el.setAttribute("aria-label", mine ? "Your sticker. Tap to change it." : "your sticker here. Tap to draw one or add a picture.");
  }
}

function blank() {
  const g = canvas.getContext("2d");
  g.setTransform(1, 0, 0, 1, 0, 0);
  g.fillStyle = "#fff";
  g.fillRect(0, 0, SIZE, SIZE);
  dirty = false;
}

function build() {
  dialog = document.createElement("dialog");
  dialog.className = "maker";
  dialog.setAttribute("aria-labelledby", "maker-title");
  dialog.innerHTML = `<form method="dialog" class="maker-in">
    <h2 id="maker-title">Make your sticker</h2>
    <p class="maker-note">Draw on the circle, or add a picture and draw on top. It stays in this browser only.</p>
    <div class="maker-stage"><canvas width="${SIZE}" height="${SIZE}" aria-label="Drawing area"></canvas></div>
    <div class="maker-tools">
      <div class="maker-pens" role="group" aria-label="Pen color">${PENS.map(([c, label], i) => `<button type="button" data-color="${c}" aria-label="${label} pen" aria-pressed="${i === 0}" style="--c:${c}"></button>`).join("")}</div>
      <label class="maker-btn">Add a picture<input class="sr-only" type="file" accept="image/*"></label>
      <button type="button" class="maker-btn" data-action="clear">Clear</button>
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
    };
    image.onerror = () => URL.revokeObjectURL(url);
    image.src = url;
  });
  dialog.addEventListener("click", (e) => {
    const action = e.target.closest("[data-action]")?.dataset.action;
    if (action === "clear") blank();
    else if (action === "cancel") dialog.close();
    else if (action === "off") { mine = null; store.set(null); paintAll(); dialog.close(); }
    else if (action === "done") {
      if (dirty) { mine = canvas.toDataURL("image/jpeg", 0.86); store.set(mine); paintAll(); }
      dialog.close();
    }
  });
}

function open() {
  if (!dialog) build();
  blank();
  dialog.querySelector('[data-action="off"]').hidden = !mine;
  if (mine) {
    const image = new Image();
    image.onload = () => { canvas.getContext("2d").drawImage(image, 0, 0, SIZE, SIZE); dirty = false; };
    image.src = mine;
  }
  dialog.showModal();
}

export const blankSticker = {
  html: () => `<div class="wd wd-blank wd-round wd-mine" role="button" tabindex="0" aria-label="your sticker here. Tap to draw one or add a picture."><span class="mn-t">your<br>sticker<br>here</span><i class="mn-img" aria-hidden="true"></i></div>`,
  wire(sticker) {
    tap(sticker, open);
    paintAll();
  },
};
