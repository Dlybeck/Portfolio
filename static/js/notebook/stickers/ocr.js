// The page's side of the pad's reader (ocr.worker.js). One shared worker, started the first time something asks for it:
// nothing is downloaded or run before that. If it fails or goes silent the worker is thrown away, so asking again starts clean.

const SILENCE_MS = 90_000; // a worker that says nothing for this long (no progress, no result) is stuck

let worker = null;
let session = null; // { promise, resolve, reject } for the load in flight, or the one that finished
let lastPct = 0;
let watchdog = 0;
let nextId = 0;
let queue = Promise.resolve();
const watchers = new Set();
const jobs = new Map(); // id -> { lines, onLine, resolve, reject }

function fail(error) {
  clearTimeout(watchdog);
  worker?.terminate();
  worker = null;
  const failed = session;
  session = null;
  lastPct = 0;
  failed?.reject(error);
  for (const job of jobs.values()) job.reject(error);
  jobs.clear();
}

/** Called on every sign of life; the timer only runs while something is waiting on the worker. */
function alive() {
  clearTimeout(watchdog);
  if (jobs.size || (session && !session.done)) watchdog = setTimeout(() => fail(new Error("The reader stopped responding")), SILENCE_MS);
}

function onMessage({ data }) {
  if (data.type === "progress") {
    lastPct = data.pct;
    watchers.forEach((cb) => cb(data.pct));
  } else if (data.type === "ready") {
    session.done = true;
    session.resolve(data.device);
  } else if (data.type === "line") {
    const job = jobs.get(data.id);
    if (job) { job.lines[data.index] = data.text; job.onLine?.(data.index, data.text); }
  } else if (data.type === "done") {
    const job = jobs.get(data.id);
    jobs.delete(data.id);
    job?.resolve(job.lines);
  } else if (data.type === "error") {
    if (data.id === undefined) { fail(new Error(data.message)); return; }
    const job = jobs.get(data.id);
    jobs.delete(data.id);
    job?.reject(new Error(data.message));
  }
  alive();
}

/** Start the worker if it is not running (and begin loading the model in it). */
function start() {
  if (worker) return;
  const made = new Worker(new URL("./ocr.worker.js", import.meta.url), { type: "module" });
  worker = made;
  session = {};
  session.promise = new Promise((resolve, reject) => { session.resolve = resolve; session.reject = reject; });
  session.promise.catch(() => {}); // callers handle it; this keeps an unwatched failure from being "unhandled"
  made.onmessage = onMessage;
  made.onerror = (e) => { if (worker === made) fail(new Error(e.message || "The reader could not start")); };
  made.postMessage({ type: "load" });
  alive();
}

export const ocr = {
  /**
   * Begin loading the model (if it has not begun) and report progress, 0 to 99, as it downloads.
   * Resolves when the reader is ready to read; rejects if it could not load.
   */
  load(onProgress) {
    try { start(); } catch (error) { return Promise.reject(error); }
    const run = session;
    if (onProgress) { watchers.add(onProgress); onProgress(lastPct); }
    return run.promise.finally(() => watchers.delete(onProgress));
  },

  /**
   * Read rows of writing, one line each, top to bottom. `onLine(index, text)` is called as each line is done.
   * @param {{ width: number, height: number, data: Uint8ClampedArray }[]} rows
   * @returns {Promise<string[]>}
   */
  read(rows, onLine) {
    const run = queue.catch(() => {}).then(async () => { // one at a time: the model reads a line, then the next
      await ocr.load();
      const id = nextId++;
      const done = new Promise((resolve, reject) => jobs.set(id, { lines: [], onLine, resolve, reject }));
      worker.postMessage({ type: "read", id, rows }, rows.map((r) => r.data.buffer));
      alive();
      return done;
    });
    queue = run;
    return run;
  },
};
