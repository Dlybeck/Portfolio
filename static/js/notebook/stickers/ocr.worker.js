// The pad's reader, in its own thread so the page never waits on it.
// It reads one line of handwriting at a time with TrOCR (small, handwriting) through transformers.js.
//
// The model and the library come from public CDNs: in the background once the page is idle (see preload() in ocr.js), or
// when someone first uses the pad if that was skipped. The browser's Cache API keeps the weights (transformers.js does
// this itself), so the second visit downloads nothing. It runs on WebAssembly: that is the path measured on real lines
// (see ADR 0003); the 8-bit weights have not been measured on a real GPU, so WebGPU is not used.
//
// Messages in:  { type: "load" }   { type: "read", id, rows: [{ width, height, data }] }   { type: "cancel", id }
// Messages out: { type: "progress", pct }   { type: "ready" }   { type: "line", id, index, text }
//               { type: "done", id }   { type: "error", id?, message }

const LIBRARY = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.2/dist/transformers.min.js"; // exact version, ONNX Runtime bundled
const MODEL = "Xenova/trocr-small-handwritten"; // MIT licence, trained on IAM handwriting lines
const REVISION = "02bea33ca09a70e2e2d91140a7e6e1a729606a5b"; // the exact files, not whatever the branch holds later
const DTYPE = "q8"; // 8-bit weights: about 70 MB in all, and no worse than the 250 MB full-precision files on a test set of written lines

// What a first load downloads, so the bar can be a true fraction of the whole before every file has said its size.
const EXPECTED = { "encoder_model_quantized.onnx": 23.1e6, "decoder_model_merged_quantized.onnx": 40.6e6, "tokenizer.json": 1.1e6 };
const EXPECTED_TOTAL = Object.values(EXPECTED).reduce((a, b) => a + b, 0);

let lib = null;
let reader = null;
let loading = null;

const say = (message) => postMessage(message);
const HEARTBEAT_MS = 5000; // a progress message at least this often while bytes arrive (the page's 90 s silence watchdog)

function makeProgress() {
  const files = new Map();
  let top = 0;
  let lastSaid = -Infinity;
  return (p) => {
    if (p.status !== "progress" || !p.total) return;
    files.set(p.file, [p.loaded, p.total]);
    let loaded = 0;
    let total = 0;
    for (const [l, t] of files.values()) { loaded += l; total += t; }
    const seen = [...files.keys()].map((f) => f.split("/").pop());
    for (const [name, size] of Object.entries(EXPECTED)) if (!seen.includes(name)) total += size; // files still to come
    const pct = Math.max(top, Math.min(99, Math.floor((loaded / Math.max(total, EXPECTED_TOTAL * 0.9)) * 100))); // never backwards, never "done" early
    // The download reports every few kilobytes but the page only shows whole percents: tell it when that changes. On a very slow
    // link a percent takes a while, and the page's watchdog treats silence as a stuck worker, so say so at least every few seconds.
    const now = performance.now();
    if (pct === top && now - lastSaid < HEARTBEAT_MS) return;
    top = pct;
    lastSaid = now;
    say({ type: "progress", pct: top });
  };
}

function build() {
  return lib.pipeline("image-to-text", MODEL, { revision: REVISION, dtype: DTYPE, device: "wasm", progress_callback: makeProgress() });
}

function load() {
  loading ??= (async () => {
    lib = await import(LIBRARY);
    lib.env.allowLocalModels = false;
    reader = await build();
    say({ type: "ready" });
  })();
  loading.catch(() => { loading = null; });
  return loading;
}

function toImage({ width, height, data }) {
  const rgb = new Uint8ClampedArray(width * height * 3);
  for (let i = 0, j = 0; i < data.length; i += 4) { rgb[j++] = data[i]; rgb[j++] = data[i + 1]; rgb[j++] = data[i + 2]; }
  return new lib.RawImage(rgb, width, height, 3);
}

/** One line of text. A trailing full stop is the model's habit with sentences, not something written on a pad. */
async function readLine(row) {
  const [out] = await reader(toImage(row), { max_new_tokens: 48 });
  return out.generated_text.trim().replace(/\.$/, "").trim();
}

const called_off = new Set(); // reads the page no longer wants

async function read(id, rows) {
  await load();
  for (let index = 0; index < rows.length; index++) {
    if (called_off.delete(id)) return; // nobody is waiting for the rest
    say({ type: "line", id, index, text: await readLine(rows[index]) });
  }
  called_off.delete(id);
  say({ type: "done", id });
}

addEventListener("message", ({ data }) => {
  if (data.type === "load") load().catch((e) => say({ type: "error", message: String(e?.message ?? e) }));
  else if (data.type === "cancel") called_off.add(data.id);
  else if (data.type === "read") read(data.id, data.rows).catch((e) => say({ type: "error", id: data.id, message: String(e?.message ?? e) }));
});
