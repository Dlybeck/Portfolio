// What the pad's reader is given: everything written on the pad, as ONE line, redrawn at the size the model likes.
// The pad is small (room for a word, sometimes two), so there is no line-finding: however tall the writing is, and
// however many ruled lines it crosses, it is cropped tightly to the ink and read once. (Cutting it at the rules gave the
// model slices of letters, which it answered with nonsense.)
//
// Everything here is plain geometry on points in the pad's own pixels (x, y from its top left), so it can be tested
// without a model.

/** The pad is ruled in four equal rows (.sc-pad's background-size is 100% 25%). A row is the yardstick for the writing's size. */
export const ROWS = 4;

/** What is read back: at most this many words, this many letters. More than that from one small pad is the model making things up. */
export const MAX_WORDS = 2;
export const MAX_CHARS = 24;

// The redrawing: a ruled row's height becomes about ROW_PX, in thin dark ink on white. Small, thick on-screen ink reads
// far worse than the same strokes redrawn thin and large, which is why the recorded points are kept.
const ROW_PX = 90;
const MAX_INK_H = 200; // writing very tall is scaled down to this, not drawn enormous
const MAX_INK_W = 1200;
const MARGIN = 0.3; // of the ink's height, on every side
const MIN_ASPECT = 1.2; // a lone tall mark is padded out, so the model does not see it stretched
const MIN_INK = 10; // less than this much pen travel (pad px) is a stray touch, not writing

/** Smallest and largest x and y over every point (loops, not Math.min(...), so a huge scribble cannot overflow the call). */
function bounds(strokes) {
  let minX = Infinity, minY = Infinity, maxX = -Infinity, maxY = -Infinity;
  for (const s of strokes) for (const [x, y] of s) { if (x < minX) minX = x; if (x > maxX) maxX = x; if (y < minY) minY = y; if (y > maxY) maxY = y; }
  return { minX, minY, maxX, maxY };
}

/** How far the pen travelled across these strokes (a dot counts as nothing). */
function travel(strokes) {
  let sum = 0;
  for (const s of strokes) for (let i = 1; i < s.length; i++) sum += Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]);
  return sum;
}

/**
 * All the ink as one line: { strokes, width, height } (the size is the ink's, in pad pixels), or null if there is only a
 * stray touch.
 * @param {number[][][]} strokes  each stroke is a list of [x, y]
 */
export function inkLine(strokes) {
  const kept = strokes.filter((s) => s.length);
  if (!kept.length || travel(kept) < MIN_INK) return null;
  const { minX, minY, maxX, maxY } = bounds(kept);
  return { strokes: kept, width: maxX - minX, height: maxY - minY };
}

/**
 * Tidy what the model said and decide whether to believe it: "" when it is not believable. The model, shown a scribble
 * or a few marks, will happily answer with a sentence. So the answer must have a letter or digit in it, be at most
 * MAX_WORDS words and MAX_CHARS long, and be no longer than the ink could hold (a written character is never narrower
 * than about a fifth of the writing's height).
 * @param {string} said  what the model said
 * @param {{ width: number, height: number }} line  the ink's size, in pad pixels
 * @param {number} pitch  the height of one ruled row, in pad pixels
 */
export function believable(said, line, pitch) {
  const text = String(said ?? "").replace(/\s+/g, " ").trim();
  if (!/[\p{L}\p{N}]/u.test(text)) return "";
  if (text.length > MAX_CHARS || text.split(" ").length > MAX_WORDS) return "";
  const narrowest = 0.22 * Math.max(line.height, pitch * 0.5);
  return text.length <= Math.ceil(line.width / narrowest) + 2 ? text : "";
}

/**
 * Draw the line's strokes for the model: dark thin ink on white, and only the ink, cropped to it with a margin.
 * @param {number[][][]} strokes  the strokes
 * @param {number} pitch  the height of one ruled row, in pad pixels
 * @returns {{ width: number, height: number, data: Uint8ClampedArray }} RGBA pixels
 */
export function rasterLine(strokes, pitch) {
  const { minX, minY, maxX, maxY } = bounds(strokes);
  let k = ROW_PX / pitch;
  k = Math.min(k, MAX_INK_H / Math.max(maxY - minY, 1), MAX_INK_W / Math.max(maxX - minX, 1));
  const inkW = (maxX - minX) * k;
  const inkH = Math.max((maxY - minY) * k, ROW_PX * 0.5);
  const lineWidth = Math.min(9, Math.max(3, inkH * 0.055)); // thin, in proportion to the writing
  const m = Math.round(inkH * MARGIN);
  const h = Math.ceil(inkH) + 2 * m;
  const w = Math.max(Math.ceil(inkW) + 2 * m, Math.ceil(h * MIN_ASPECT));
  const offX = (w - inkW) / 2;
  const offY = m + (inkH - (maxY - minY) * k) / 2;

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const g = canvas.getContext("2d");
  g.fillStyle = "#fff";
  g.fillRect(0, 0, w, h);
  g.lineCap = g.lineJoin = "round";
  g.lineWidth = lineWidth;
  g.strokeStyle = "#111";
  for (const s of strokes) {
    g.beginPath();
    s.forEach(([x, y], i) => {
      const X = offX + (x - minX) * k;
      const Y = offY + (y - minY) * k;
      if (i) g.lineTo(X, Y);
      else g.moveTo(X, Y);
    });
    if (s.length === 1) g.lineTo(offX + (s[0][0] - minX) * k + 0.01, offY + (s[0][1] - minY) * k); // a dot
    g.stroke();
  }
  return { width: w, height: h, data: g.getImageData(0, 0, w, h).data };
}
