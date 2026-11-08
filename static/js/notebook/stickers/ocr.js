// The page's side of the pad's reader (ocr.worker.js). One shared worker, started the first time something asks for it:
// nothing is downloaded or run before that. If it fails or goes silent the worker is thrown away, so asking again starts clean.
//
// The reader must never make the site lag. While it loads or reads, the page is watched (frame times and long tasks); if
// it starts to struggle the worker is thrown away and the reader stays off for the rest of the visit.

const SILENCE_MS = 90_000; // a worker that says nothing for this long (no progress, no result) is stuck

let worker = null;
let session = null; // { promise, resolve, reject } for the load in flight, or the one that finished
let lastPct = 0;
let watchdog = 0;
let nextId = 0;
let queue = Promise.resolve();
let generation = 0; // bumped by cancel(): reads asked for before it are not worth doing
const watchers = new Set();
const jobs = new Map(); // id -> { lines, onLine, resolve, reject }

// ---- switching off: if the page struggles while the reader works, the reader stops and stays off for this visit

const OFF_KEY = "pad-reader-off";
const WINDOW_MS = 4000; // the stretch of time looked at
const SLOW_FRAME_MS = 100; // a frame this late is a visible stutter (about six missed frames at 60 Hz)
const JANK_FRAMES = 5; // this many stutters within the window: the page is struggling
const FREEZE_MS = 800; // one frame this late: the page froze
const LONG_TASK_MS = 1200; // long tasks (50 ms or more each) adding up to this much of the window: the main thread is swamped

const TOO_WEAK_GB = 1; // a device with this much memory or less cannot hold the model beside the page: reading is simply off there

let off = false;
try { off = sessionStorage.getItem(OFF_KEY) === "1"; } catch { /* storage blocked: it just will not be remembered */ }
if (navigator.deviceMemory !== undefined && navigator.deviceMemory <= TOO_WEAK_GB) off = true; // (not remembered: the number does not change)
const offWatchers = new Map(); // callback -> is it still wanted?
let watching = null;

const isOff = () => Object.assign(new Error("The reader is off on this device"), { name: "ReaderOff" });

/** Throw the worker (and with it the model) away, remember that for the visit, and tell whoever is listening. */
function switchOff(why) {
  if (off) return;
  off = true;
  try { sessionStorage.setItem(OFF_KEY, "1"); } catch { /* not remembered */ }
  fail(isOff());
  for (const cb of offWatchers.keys()) cb(why);
}

/** Is the reader doing something that could slow the page: loading, or reading? */
const working = () => jobs.size > 0 || Boolean(session && !session.done);

function stopWatching() {
  watching?.stop();
  watching = null;
}

/** Watch frame times and long tasks, but only while the reader is working. */
function watch() {
  if (off || !working()) { stopWatching(); return; }
  if (watching) return;
  let last = performance.now();
  let skip = false;
  let raf = 0;
  let stopped = false;
  let observer = null;
  const slow = []; // [when, how late] for each late frame
  const long = []; // [when, how long] for each long task
  const check = () => {
    const now = performance.now();
    for (const list of [slow, long]) while (list.length && now - list[0][0] > WINDOW_MS) list.shift();
    if (slow.some(([, late]) => late >= FREEZE_MS)) switchOff("the page froze");
    else if (slow.length >= JANK_FRAMES) switchOff("frames were dropping");
    else if (long.reduce((sum, [, ms]) => sum + ms, 0) >= LONG_TASK_MS) switchOff("the page was busy");
  };
  const frame = (now) => {
    const gap = now - last;
    last = now;
    if (skip) skip = false; // the first frame after the tab was hidden is late for a good reason
    else if (gap >= SLOW_FRAME_MS) { slow.push([now, gap]); check(); } // (this can switch the reader off, which stops the watch)
    if (!stopped) raf = requestAnimationFrame(frame);
  };
  const resume = () => { skip = true; last = performance.now(); };
  try {
    observer = new PerformanceObserver((list) => {
      for (const entry of list.getEntries()) long.push([entry.startTime + entry.duration, entry.duration]);
      check();
    });
    observer.observe({ entryTypes: ["longtask"] });
  } catch { /* no long-task timing here (Safari): the frame times still do the job */ }
  document.addEventListener("visibilitychange", resume);
  raf = requestAnimationFrame(frame);
  watching = { stop() { stopped = true; cancelAnimationFrame(raf); observer?.disconnect(); document.removeEventListener("visibilitychange", resume); } };
}

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
  watch();
}

/** Called on every sign of life; the timer only runs while something is waiting on the worker. */
function alive() {
  clearTimeout(watchdog);
  if (working()) watchdog = setTimeout(() => fail(new Error("The reader stopped responding")), SILENCE_MS);
  watch();
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

// ---- preloading: fetch the model quietly once the page is done, so most visitors find the reader ready

const SETTLE_MS = 1500; // after the page's load event, so first paint and the first moments are untouched
const IDLE_MS = 5000; // and then at the browser's first idle moment, or at the latest after this

const WEAK_MEMORY_GB = 2; // navigator.deviceMemory at or below this is a weak device
const WEAK_CORES = 4; // and so are this many logical cores or fewer

/** A weak device (little memory, few cores) is not asked to fetch and start a 70 MB model on its own. It still can if the visitor writes. */
function weakDevice() {
  const memory = navigator.deviceMemory; // Chromium only
  const cores = navigator.hardwareConcurrency;
  return (memory !== undefined && memory <= WEAK_MEMORY_GB) || (cores !== undefined && cores <= WEAK_CORES);
}

/** A weak device, a visitor who asked to save data, or one probably on a metered or slow link gets the model only if they write on the pad. */
function worthPreloading() {
  if (off || weakDevice()) return false;
  const c = navigator.connection;
  if (c) return !(c.saveData || c.type === "cellular" || ["slow-2g", "2g", "3g"].includes(c.effectiveType));
  // Safari does not say what the link is. A phone or tablet (touch first) might be on cellular, so do not spend its data unasked.
  return !matchMedia("(pointer: coarse)").matches;
}

let preloadAsked = false;

/**
 * Start fetching the model in the background when the page has settled and the browser is idle. It never shows anything:
 * the pad shows progress only once someone touches it, and then joins this load from where it has got to. Safe to call
 * again; only the first call does anything. A failure here is silent, and the pad starts afresh when it is used.
 * `isPhone()` says whether the notebook is in its phone layout; a phone never preloads (the link may be mobile data
 * whatever the browser reports), and the reader loads on the first stroke instead. It is asked again when the wait ends,
 * since the layout can change meanwhile.
 */
export function preload(isPhone = () => false) {
  if (preloadAsked) return;
  preloadAsked = true;
  if (isPhone() || !worthPreloading()) return;
  const go = () => setTimeout(() => {
    const start = () => { if (!isPhone() && !off && worthPreloading()) ocr.load().catch(() => {}); }; // the link can change while it waits: ask again
    const idle = () => {
      if ("requestIdleCallback" in window) requestIdleCallback(start, { timeout: IDLE_MS });
      else setTimeout(start, 500); // Safari has no idle callback
    };
    if (document.hidden) document.addEventListener("visibilitychange", idle, { once: true }); // a tab nobody is looking at waits until it is shown
    else idle();
  }, SETTLE_MS);
  if (document.readyState === "complete") go();
  else addEventListener("load", go, { once: true });
}

export const ocr = {
  /** The worker is up and the model is loaded. False again if the worker has been thrown away. */
  get ready() { return Boolean(session?.done); },

  /**
   * Call off every read that has been asked for: queued ones never start, the one being worked on stops after the line
   * it is on, and its promise settles at once with whatever lines were done. The loaded model stays loaded.
   */
  cancel() {
    generation++;
    for (const [id, job] of jobs) {
      worker?.postMessage({ type: "cancel", id });
      jobs.delete(id);
      job.resolve(job.lines);
    }
    alive();
  },

  /** The reader was switched off because the page was struggling. It stays off until the visit ends. */
  get off() { return off; },

  /** Be told when the reader switches itself off, for as long as `stillWanted()` is true. Returns the way to stop being told. */
  onOff(callback, stillWanted = () => true) {
    for (const [cb, wanted] of offWatchers) if (!wanted()) offWatchers.delete(cb); // a pad that has left the page is not told
    offWatchers.set(callback, stillWanted);
    return () => offWatchers.delete(callback);
  },

  /**
   * Begin loading the model (if it has not begun) and report progress, 0 to 99, as it downloads.
   * Resolves when the reader is ready to read; rejects if it could not load.
   */
  load(onProgress) {
    if (off) return Promise.reject(isOff());
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
    const asked = generation;
    const run = queue.catch(() => {}).then(async () => { // one at a time: the model reads a line, then the next
      if (asked !== generation) return []; // called off while it waited its turn
      await ocr.load();
      if (asked !== generation) return [];
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
