// What the pad's reader is given: the recorded strokes, split by the pad's ruled rows and redrawn at the size the
// model likes. The model reads one line of writing at a time, and a ruled pad is already a stack of lines.
//
// Everything here is plain geometry on points in the pad's own pixels (x, y from its top left), so it can be tested
// without a model.

/** The pad is ruled in four equal rows (.sc-pad's background-size is 100% 25%). */
export const ROWS = 4;

// The redrawing: one ruled row becomes about ROW_PX tall, in thin dark ink on white. Small, thick on-screen ink reads
// far worse than the same strokes redrawn thin and large, which is why the recorded points are kept.
const ROW_PX = 90;
const LINE_PX = 5;
const MARGIN = 0.3; // of the ink's height, on every side
const MIN_ASPECT = 1.2; // a lone tall mark is padded out, so the model does not see it stretched
const MIN_INK = 10; // less than this much pen travel (pad px) in a row is a stray touch, not writing

const pointsOf = (strokes) => strokes.flatMap((s) => s);

/** Which ruled row a stroke belongs to: the row its middle falls in. */
export function rowOf(stroke, height) {
  const ys = stroke.map((p) => p[1]);
  const mid = (Math.min(...ys) + Math.max(...ys)) / 2;
  return Math.min(ROWS - 1, Math.max(0, Math.floor((mid / height) * ROWS)));
}

/** How far the pen travelled across these strokes (a dot counts as nothing). */
function travel(strokes) {
  let sum = 0;
  for (const s of strokes) for (let i = 1; i < s.length; i++) sum += Math.hypot(s[i][0] - s[i - 1][0], s[i][1] - s[i - 1][1]);
  return sum;
}

/**
 * The rows that hold writing, top to bottom: [{ row, strokes }]. Empty rows and stray touches are left out.
 * @param {number[][][]} strokes  each stroke is a list of [x, y]
 * @param {number} height  the pad's height in the same pixels
 */
export function splitRows(strokes, height) {
  const rows = Array.from({ length: ROWS }, () => []);
  for (const s of strokes) if (s.length) rows[rowOf(s, height)].push(s);
  return rows.map((list, row) => ({ row, strokes: list })).filter((r) => r.strokes.length && travel(r.strokes) >= MIN_INK);
}

/**
 * Draw one row's strokes for the model: dark thin ink on white, sized by the row (not by how much was written).
 * @param {number[][][]} strokes  the row's strokes
 * @param {number} pitch  the height of one ruled row, in pad pixels
 * @returns {{ width: number, height: number, data: Uint8ClampedArray }} RGBA pixels
 */
export function rasterRow(strokes, pitch) {
  const k = ROW_PX / pitch;
  const all = pointsOf(strokes);
  const xs = all.map((p) => p[0]);
  const ys = all.map((p) => p[1]);
  const minX = Math.min(...xs);
  const minY = Math.min(...ys);
  const inkW = (Math.max(...xs) - minX) * k;
  const inkH = Math.max((Math.max(...ys) - minY) * k, ROW_PX * 0.5);
  const m = Math.round(inkH * MARGIN);
  const h = Math.ceil(inkH) + 2 * m;
  const w = Math.max(Math.ceil(inkW) + 2 * m, Math.ceil(h * MIN_ASPECT));
  const offX = (w - inkW) / 2;
  const offY = m + (inkH - (Math.max(...ys) - minY) * k) / 2;

  const canvas = document.createElement("canvas");
  canvas.width = w;
  canvas.height = h;
  const g = canvas.getContext("2d");
  g.fillStyle = "#fff";
  g.fillRect(0, 0, w, h);
  g.lineCap = g.lineJoin = "round";
  g.lineWidth = LINE_PX;
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
