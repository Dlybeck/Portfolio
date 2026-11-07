// What brings a page's pictures and widgets to life once the engine has put it on a leaf:
// swipe rows, the NBA predictor, and the 3D models. The server writes all of them as plain HTML;
// this only upgrades them. Nothing here is needed to read the words.

import { el, reducedMotion } from "./motion.js";

// ---------- swipe rows: site snapshots, the seven themes, the 3D models ----------

function enhanceSlides(scope) {
  for (const list of scope.querySelectorAll("[data-slides]:not([data-ready])")) {
    list.dataset.ready = "1";
    const slides = [...list.children];
    if (slides.length < 2) continue;
    list.tabIndex = 0; // a scrolling row can be scrolled with the arrow keys once it has focus
    const bar = el("div", "slides-bar");
    bar.innerHTML = `<button type="button" class="slides-prev" aria-label="Previous">‹</button><span class="slides-count" aria-live="polite"></span><button type="button" class="slides-next" aria-label="Next">›</button>`;
    list.after(bar);
    const prev = bar.querySelector(".slides-prev");
    const next = bar.querySelector(".slides-next");
    const count = bar.querySelector(".slides-count");
    const index = () => {
      let best = 0;
      let gap = Infinity;
      slides.forEach((s, i) => {
        const d = Math.abs(s.offsetLeft - list.offsetLeft - list.scrollLeft);
        if (d < gap) { gap = d; best = i; }
      });
      return best;
    };
    const update = () => {
      const i = index();
      count.textContent = `${i + 1} of ${slides.length}`;
      prev.disabled = i === 0;
      next.disabled = i === slides.length - 1;
    };
    const go = (i) => list.scrollTo({ left: slides[i].offsetLeft - list.offsetLeft, behavior: reducedMotion() ? "instant" : "smooth" });
    prev.addEventListener("click", () => go(Math.max(0, index() - 1)));
    next.addEventListener("click", () => go(Math.min(slides.length - 1, index() + 1)));
    let frame = 0;
    list.addEventListener("scroll", () => { cancelAnimationFrame(frame); frame = requestAnimationFrame(update); }, { passive: true });
    update();
  }
}

// ---------- the NBA predictor ----------

let results = null;
const loadResults = () => (results ??= fetch("/static/json/results.json").then((r) => {
  if (!r.ok) throw new Error(`results.json ${r.status}`);
  return r.json();
}).catch((error) => { results = null; throw error; })); // a failed load may be retried

export function predictionFor(data, home, away) {
  if (home === away) return "Pick two different teams.";
  return data[home]?.[away] ?? data[away]?.[home] ?? "I can't predict this matchup.";
}

async function enhancePredictor(scope) {
  for (const box of scope.querySelectorAll("[data-predictor]:not([data-ready])")) {
    box.dataset.ready = "1";
    const homeSelect = box.querySelector(".team-home");
    const awaySelect = box.querySelector(".team-away");
    const go = box.querySelector(".predict-go");
    const out = box.querySelector(".predict-result");
    try {
      const data = await loadResults();
      const teams = Object.keys(data);
      for (const select of [homeSelect, awaySelect]) {
        select.replaceChildren(...teams.map((team) => new Option(team, team)));
        select.disabled = false;
      }
      awaySelect.selectedIndex = 1;
      go.disabled = false;
      go.addEventListener("click", () => { out.textContent = predictionFor(data, homeSelect.value, awaySelect.value); });
    } catch (error) {
      console.warn("The predictor could not load its data", error);
      out.textContent = "The predictor could not load its data. Try again later.";
    }
  }
}

// ---------- 3D models ----------

let viewerReady = null;
const loadViewer = () => (viewerReady ??= import("/static/vendor/model-viewer/model-viewer.min.js").catch((error) => { viewerReady = null; throw error; }));

/** Called when a page has stopped turning: only then do models start to load. */
async function enhanceModels(scope) {
  const models = [...scope.querySelectorAll("model-viewer[data-src]:not([src])")];
  if (!models.length) return;
  try {
    await loadViewer();
  } catch (error) {
    console.warn("The 3D viewer could not load", error);
    return;
  }
  for (const model of models) {
    if (reducedMotion()) model.removeAttribute("auto-rotate");
    model.setAttribute("loading", "lazy"); // only the ones scrolled into view are fetched
    model.setAttribute("src", model.dataset.src);
  }
}

// open it / close it: the same model with its lid off
document.addEventListener("click", (e) => {
  const button = e.target.closest(".model-toggle");
  if (!button) return;
  const model = button.parentElement.querySelector("model-viewer");
  const opened = model.getAttribute("src") === model.dataset.altSrc;
  model.setAttribute("src", opened ? model.dataset.src : model.dataset.altSrc);
  button.textContent = opened ? button.dataset.word : button.dataset.close;
  button.classList.toggle("is-on", !opened);
});

/** A page was written onto the book. */
export function enhance(scope) {
  enhanceSlides(scope);
  enhancePredictor(scope);
}

/** The book stopped turning. */
export function settled(scopes) {
  for (const scope of scopes) if (scope) enhanceModels(scope);
}
