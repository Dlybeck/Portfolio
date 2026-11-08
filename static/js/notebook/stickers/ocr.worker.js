// The pad's reader, in its own thread so the page never waits on it.
// It reads one line of handwriting at a time with TrOCR (small, handwriting) through transformers.js.
//
// The model and the library come from public CDNs at the moment someone first uses the pad; nothing is fetched before.
// The browser's Cache API keeps the weights (transformers.js does this itself), so the second visit starts at once.
//
// Messages in:  { type: "load" }   { type: "read", id, rows: [{ width, height, data }] }
// Messages out: { type: "progress", pct }   { type: "ready", device }   { type: "line", id, index, text }
//               { type: "done", id }   { type: "error", id?, message }

const LIBRARY = "https://cdn.jsdelivr.net/npm/@huggingface/transformers@4.3.2/dist/transformers.min.js"; // exact version, ONNX Runtime bundled
const MODEL = "Xenova/trocr-small-handwritten"; // MIT licence, trained on IAM handwriting lines
const REVISION = "02bea33ca09a70e2e2d91140a7e6e1a729606a5b"; // the exact files, not whatever the branch holds later
const DTYPE = "q8"; // 8-bit weights: about 65 MB, and no worse than the 250 MB full-precision files on a test set of written lines

// What a first load downloads, so the bar can be a true fraction of the whole before every file has said its size.
const EXPECTED = { "encoder_model_quantized.onnx": 23.1e6, "decoder_model_merged_quantized.onnx": 40.6e6, "tokenizer.json": 1.1e6 };
const EXPECTED_TOTAL = Object.values(EXPECTED).reduce((a, b) => a + b, 0);

let lib = null;
let reader = null;
let device = "wasm";
let loading = null;

const say = (message) => postMessage(message);

/** WebGPU only on a real graphics adapter: a software one is far slower than plain WebAssembly. */
async function pickDevice() {
  try {
    const adapter = await navigator.gpu?.requestAdapter();
    if (adapter && !(adapter.isFallbackAdapter || adapter.info?.isFallbackAdapter)) return "webgpu";
  } catch { /* no WebGPU */ }
  return "wasm";
}

function makeProgress() {
  const files = new Map();
  let top = 0;
  return (p) => {
    if (p.status !== "progress" || !p.total) return;
    files.set(p.file, [p.loaded, p.total]);
    let loaded = 0;
    let total = 0;
    for (const [l, t] of files.values()) { loaded += l; total += t; }
    const seen = [...files.keys()].map((f) => f.split("/").pop());
    for (const [name, size] of Object.entries(EXPECTED)) if (!seen.includes(name)) total += size; // files still to come
    top = Math.max(top, Math.min(99, Math.floor((loaded / Math.max(total, EXPECTED_TOTAL * 0.9)) * 100))); // never backwards, never "done" early
    say({ type: "progress", pct: top });
  };
}

async function build(where) {
  const { pipeline } = lib;
  return pipeline("image-to-text", MODEL, { revision: REVISION, dtype: DTYPE, device: where, progress_callback: makeProgress() });
}

function load() {
  loading ??= (async () => {
    lib = await import(LIBRARY);
    lib.env.allowLocalModels = false;
    device = await pickDevice();
    try {
      reader = await build(device);
    } catch (error) {
      if (device === "wasm") throw error;
      device = "wasm"; // WebGPU would not start: the plain WebAssembly path always can
      reader = await build(device);
    }
    say({ type: "ready", device });
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

async function read(id, rows) {
  await load();
  for (let index = 0; index < rows.length; index++) {
    let text;
    try {
      text = await readLine(rows[index]);
    } catch (error) {
      if (device !== "webgpu") throw error;
      device = "wasm"; // it loaded on the GPU but would not run: redo this on WebAssembly
      try { await reader.dispose?.(); } catch { /* already gone */ } // free the GPU's share first
      reader = await build(device);
      text = await readLine(rows[index]);
    }
    say({ type: "line", id, index, text });
  }
  say({ type: "done", id });
}

addEventListener("message", ({ data }) => {
  if (data.type === "load") load().catch((e) => say({ type: "error", message: String(e?.message ?? e) }));
  else if (data.type === "read") read(data.id, data.rows).catch((e) => say({ type: "error", id: data.id, message: String(e?.message ?? e) }));
});
