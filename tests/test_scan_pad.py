"""The scan pad on the cover: its strokes belong to it, it reads them lazily, and it always says what it is doing.

The reader (a worker that fetches a 65 MB model) is replaced by a stub here, so none of this downloads anything.
"""

from __future__ import annotations

import math

import pytest

DESKTOP = {"width": 1280, "height": 800}
WORKER = "**/stickers/ocr.worker.js"

# loads in about a second, reporting its progress; reads every row it is given as "line 1", "line 2", ...
READER = """
addEventListener("message", ({ data }) => {
  if (data.type === "load") {
    let pct = 0;
    const tick = setInterval(() => {
      pct += 33;
      if (pct < 99) return postMessage({ type: "progress", pct });
      clearInterval(tick);
      postMessage({ type: "progress", pct: 99 });
      setTimeout(() => postMessage({ type: "ready", device: "wasm" }), 300);
    }, 250);
  } else if (data.type === "read") {
    setTimeout(() => { // a real read takes a moment
      data.rows.forEach((row, index) => postMessage({ type: "line", id: data.id, index, text: `line ${index + 1}` }));
      postMessage({ type: "done", id: data.id });
    }, 600);
  }
});
"""
# reads one row every half second, and reports what it does on a BroadcastChannel the page listens to
CANCELLABLE_READER = """
const log = new BroadcastChannel("stub");
const cancelled = new Set();
addEventListener("message", ({ data }) => {
  if (data.type === "load") { setTimeout(() => postMessage({ type: "ready", device: "wasm" }), 100); }
  else if (data.type === "cancel") { cancelled.add(data.id); log.postMessage("cancel:" + data.id); }
  else if (data.type === "read") {
    log.postMessage("read:" + data.id + ":" + data.rows.length);
    let index = 0;
    const next = () => {
      if (cancelled.has(data.id)) return log.postMessage("stopped:" + data.id + ":after " + index);
      if (index === data.rows.length) return postMessage({ type: "done", id: data.id });
      postMessage({ type: "line", id: data.id, index, text: `line ${index + 1}` });
      index++;
      setTimeout(next, 500);
    };
    setTimeout(next, 500);
  }
});
"""
BROKEN_READER = 'addEventListener("message", () => postMessage({ type: "error", message: "network down" }));'


def serve(page, *bodies):
    """Answer each request for the reader's worker with the next body (the last one repeats)."""
    calls = []

    def handle(route):
        calls.append(route.request.url)
        route.fulfill(body=bodies[min(len(calls), len(bodies)) - 1], content_type="text/javascript")

    page.route(WORKER, handle)
    return calls


def link(**properties):
    """An init script that makes the browser report this kind of connection (navigator.connection)."""
    value = str(properties).replace("True", "true").replace("False", "false")
    return f"Object.defineProperty(navigator, 'connection', {{ value: {value}, configurable: true }})"


NO_CONNECTION_API = "Object.defineProperty(navigator, 'connection', { value: undefined, configurable: true })"  # as in Safari
SAVE_DATA = link(saveData=True)


def open_cover(page, base, viewport=None, connection=SAVE_DATA):
    """Most tests want the reader to start only when the pad is used, so they report Save-Data (which skips the preload)."""
    page.add_init_script(connection)
    if viewport:
        page.set_viewport_size(viewport)
    page.goto(base + "/")
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_selector(".wd-scan canvas")
    page.wait_for_timeout(700)


def pad_geometry(page):
    """Where the pad is: its size, its centre on screen and its tilt (it sits turned on the cover)."""
    return page.evaluate(
        """() => {
          const c = document.querySelector('.wd-scan canvas'), r = c.getBoundingClientRect();
          const slot = c.closest('.wd-slot');
          return { w: c.clientWidth, h: c.clientHeight, cx: r.x + r.width / 2, cy: r.y + r.height / 2, rot: parseFloat(getComputedStyle(slot).rotate) || 0 };
        }"""
    )


def screen(geo, fx, fy):
    """The screen point at a fraction (0 to 1) across and down the pad, allowing for its tilt."""
    dx, dy = (fx - 0.5) * geo["w"], (fy - 0.5) * geo["h"]
    a = math.radians(geo["rot"])
    return geo["cx"] + dx * math.cos(a) - dy * math.sin(a), geo["cy"] + dx * math.sin(a) + dy * math.cos(a)


def stroke_mouse(page, points):
    page.mouse.move(*points[0])
    page.mouse.down()
    for p in points[1:]:
        page.mouse.move(*p, steps=6)
    page.mouse.up()


def stroke_touch(cdp, points):
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": points[0][0], "y": points[0][1]}]})
    for x, y in points[1:]:
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def untouched(page):
    """The book still shows its shut cover on the home address."""
    return page.evaluate("document.getElementById('notebook').classList.contains('is-closed') && location.pathname === '/'")


def strokes_along_the_ruled_line(page, geo):
    """Long sideways strokes along a ruled line, each ending somewhere different, some off the pad altogether."""
    far_left = (6, geo["cy"])
    page_edge = (page.viewport_size["width"] - 4, page.viewport_size["height"] - 4)
    return [
        [screen(geo, 0.05, 0.5), screen(geo, 0.95, 0.5)],  # all the way along the line
        [screen(geo, 0.95, 0.75), screen(geo, 0.05, 0.75)],  # and back, leftwards (the direction that opens the cover)
        [screen(geo, 0.6, 0.5), far_left],  # released far off the pad, to the left
        [screen(geo, 0.4, 0.75), page_edge],  # released at the page's corner
        [screen(geo, 0.5, 0.25), screen(geo, 1.4, 0.4)],  # released just off the pad's right edge
    ]


def test_strokes_on_the_pad_never_open_the_cover_with_a_mouse(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    geo = pad_geometry(page)
    for points in strokes_along_the_ruled_line(page, geo):
        stroke_mouse(page, points)
        page.wait_for_timeout(250)
        assert untouched(page), f"a stroke ending at {points[-1]} moved the book"
    # a trackpad's sideways scroll over the pad (not just anywhere): the pad must claim it, so the page and Safari's swipe-back never see it
    page.evaluate("window.__wheel = []; document.addEventListener('wheel', () => window.__wheel.push(1), { passive: true })")
    page.mouse.move(*screen(geo, 0.5, 0.5))
    page.mouse.wheel(260, 0)
    page.wait_for_timeout(200)
    assert page.evaluate("window.__wheel") == []  # it never got past the pad
    assert page.evaluate("!document.querySelector('.wd-scan canvas').dispatchEvent(new WheelEvent('wheel', { deltaX: 260, bubbles: true, cancelable: true }))")  # and the pad cancelled it
    assert untouched(page)


def test_strokes_on_the_pad_never_open_the_cover_with_a_finger(mobile_browser_page) -> None:
    page, base = mobile_browser_page
    serve(page, READER)
    open_cover(page, base)
    cdp = page.context.new_cdp_session(page)
    geo = pad_geometry(page)
    for points in strokes_along_the_ruled_line(page, geo):
        stroke_touch(cdp, points)
        page.wait_for_timeout(250)
        assert untouched(page), f"a stroke ending at {points[-1]} moved the book"


def test_the_ink_lands_under_the_pen_on_the_tilted_pad(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    geo = pad_geometry(page)
    assert abs(geo["rot"]) > 1  # the pad really is tilted, so this checks something
    x, y = screen(geo, 0.5, 0.5)
    stroke_mouse(page, [(x, y), (x + 1, y + 1)])
    inked = page.evaluate(
        "() => { const c = document.querySelector('.wd-scan canvas'); return c.getContext('2d').getImageData(c.width / 2 - 6, c.height / 2 - 6, 12, 12).data.some((v, i) => i % 4 === 3 && v > 0); }"
    )
    assert inked


def test_on_save_data_nothing_is_fetched_until_the_pad_is_used(browser_page) -> None:
    page, base = browser_page
    requested = []
    page.on("request", lambda r: requested.append(r.url))
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP)
    page.wait_for_timeout(5000)  # well past when a preload would have started
    assert calls == []  # the reader's worker is not even started
    assert not [u for u in requested if not u.startswith(base)]  # and no other site is contacted
    geo = pad_geometry(page)
    stroke_mouse(page, [screen(geo, 0.2, 0.4), screen(geo, 0.5, 0.45)])
    page.wait_for_timeout(500)
    assert len(calls) == 1  # the first stroke starts it


# notes the pad's state, the bar's fill and its text every 40 ms, from inside the page
WATCH = """() => {
  window.__seen = [];
  const pad = document.querySelector('.wd-scan');
  setInterval(() => window.__seen.push([pad.dataset.state, pad.querySelector('.sc-pg').style.getPropertyValue('--p'), pad.querySelector('.sc-t').textContent]), 40);
}"""


def test_the_pad_shows_progress_then_reads_each_written_row(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    page.evaluate(WATCH)
    geo = pad_geometry(page)
    stroke_mouse(page, [screen(geo, 0.1, 0.12), screen(geo, 0.6, 0.15), screen(geo, 0.8, 0.1)])  # row 1
    stroke_mouse(page, [screen(geo, 0.1, 0.62), screen(geo, 0.6, 0.65), screen(geo, 0.8, 0.6)])  # row 3 (row 2 left empty)
    page.wait_for_function("window.__seen.some((s) => s[2] === 'line 1\\nline 2')", timeout=10000)
    seen = page.evaluate("window.__seen")
    states = [s[0] for s in seen]
    fractions = [float(s[1]) for s in seen if s[0] == "load" and s[1]]
    assert "load" in states and "read" in states and "done" in states, states
    assert len(set(fractions)) >= 2 and fractions == sorted(fractions)  # the bar filled, and only forwards (before the first byte it is the moving bar, not an empty one)
    assert any(s[0] == "load" and s[2].startswith("Loading reader") for s in seen)
    assert any(s[0] == "read" and s[2] == "Reading\u2026" for s in seen)  # and something says it is reading while it reads
    assert untouched(page)


def test_a_failed_load_says_so_and_retry_works(browser_page) -> None:
    page, base = browser_page
    calls = serve(page, BROKEN_READER, READER)  # the load a first stroke starts fails; the retry's fresh worker works
    open_cover(page, base, DESKTOP)
    geo = pad_geometry(page)
    stroke_mouse(page, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'error'", timeout=8000)
    assert "reader" in page.locator(".wd-scan .sc-t").inner_text()
    retry = page.locator(".wd-scan .sc-go")
    assert retry.is_visible() and retry.text_content() == "retry"
    retry.click()
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert len(calls) == 2  # the broken worker was thrown away and a fresh one started
    assert untouched(page)


def test_the_scan_button_reads_without_waiting(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    geo = pad_geometry(page)
    stroke_mouse(page, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'ink'", timeout=8000)  # the reader is up; the pad waits
    page.wait_for_timeout(1800)  # let the first stroke's own wait run out and its result clear
    page.wait_for_function("['ink', 'done', 'idle'].includes(document.querySelector('.wd-scan').dataset.state)", timeout=15000)
    page.evaluate("document.querySelector('.wd-scan .sc-go').addEventListener('click', () => { window.__pressed = (window.__pressed || 0) + 1; })")
    stroke_mouse(page, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])
    page.locator(".wd-scan .sc-go").click()  # straight after the stroke, inside the moment the pad guards against a drag's click
    assert page.evaluate("window.__pressed") == 1  # the press was not swallowed
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'read'", timeout=1000)  # and it read at once, well before the 1.5 s wait
    assert untouched(page)


# ---- the quiet preload: the reader is fetched once the page is idle, unless the visitor's connection says not to

def device(memory, cores):
    """An init script for a device with this much memory (GB) and this many cores."""
    return f"Object.defineProperty(navigator, 'deviceMemory', {{ value: {memory}, configurable: true }}); Object.defineProperty(navigator, 'hardwareConcurrency', {{ value: {cores}, configurable: true }})"


STRONG = device(8, 8)
WIFI = link(effectiveType="4g", saveData=False, type="wifi") + "; " + STRONG  # a good link on a capable device


def write(page, geo):
    stroke_mouse(page, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])


def wait_for_worker(page, calls, seconds=6):
    for _ in range(seconds * 10):
        if calls:
            return
        page.wait_for_timeout(100)


def test_the_reader_is_fetched_quietly_once_the_page_is_idle_and_reused_when_someone_writes(browser_page) -> None:
    page, base = browser_page
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP, connection=WIFI)
    page.evaluate(WATCH)
    wait_for_worker(page, calls)
    assert len(calls) == 1, "the reader did not start by itself"
    page.wait_for_timeout(2500)  # it finishes loading with nobody there
    seen = page.evaluate("window.__seen")
    assert {s[0] for s in seen} == {"idle"}  # no progress, no loading note: the pad just plays its demo
    assert not [s for s in seen if "reader" in s[2].lower()]
    page.evaluate("window.__seen.length = 0")
    write(page, pad_geometry(page))
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert "load" not in {s[0] for s in page.evaluate("window.__seen")}  # it was ready: straight to reading
    assert len(calls) == 1  # one download, reused
    assert untouched(page)


def test_touching_the_pad_while_the_preload_is_under_way_shows_where_it_has_got_to(browser_page) -> None:
    page, base = browser_page
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP, connection=WIFI)
    page.evaluate(WATCH)
    wait_for_worker(page, calls)
    assert len(calls) == 1
    page.wait_for_timeout(600)  # the stub has reported a third or two thirds by now
    write(page, pad_geometry(page))
    page.wait_for_function("window.__seen.some((s) => s[0] === 'load')", timeout=3000)
    first = next(s for s in page.evaluate("window.__seen") if s[0] == "load")
    assert first[2].startswith("Starting") or (first[1] != "" and float(first[1]) >= 0.33), first  # joined part way, not restarted
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert len(calls) == 1  # still the one download
    assert untouched(page)


SLOW_OR_METERED = {
    "save-data": link(saveData=True),
    "3g": link(effectiveType="3g", saveData=False),
    "slow-2g": link(effectiveType="slow-2g", saveData=False),
    "cellular": link(type="cellular", effectiveType="4g", saveData=False),
}


@pytest.mark.parametrize("kind", list(SLOW_OR_METERED))
def test_a_slow_or_metered_connection_skips_the_preload_but_still_loads_on_the_first_stroke(browser_page, kind) -> None:
    page, base = browser_page
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP, connection=SLOW_OR_METERED[kind])
    page.wait_for_timeout(5000)
    assert calls == []
    write(page, pad_geometry(page))
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert len(calls) == 1
    assert untouched(page)


def test_a_phone_that_cannot_say_what_link_it_is_on_does_not_preload(mobile_browser_page) -> None:
    page, base = mobile_browser_page
    calls = serve(page, READER)
    open_cover(page, base, connection=NO_CONNECTION_API)
    page.wait_for_timeout(5000)
    assert calls == []
    cdp = page.context.new_cdp_session(page)
    geo = pad_geometry(page)
    stroke_touch(cdp, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])  # a finger still starts it
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert len(calls) == 1


def test_a_phone_never_preloads_even_on_a_normal_4g_link_and_loads_on_the_first_stroke(mobile_browser_page) -> None:
    page, base = mobile_browser_page
    calls = serve(page, READER)
    open_cover(page, base, connection=link(effectiveType="4g", saveData=False) + "; " + STRONG)  # looks like fine wifi to the browser
    assert page.evaluate("document.getElementById('notebook').classList.contains('nb--phone')")
    page.wait_for_timeout(8000)  # past the settle time and the idle timeout
    assert calls == []
    cdp = page.context.new_cdp_session(page)
    geo = pad_geometry(page)
    stroke_touch(cdp, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert len(calls) == 1
    assert untouched(page)


def test_the_pad_never_calls_itself_by_the_old_name(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    write(page, pad_geometry(page))
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    page.wait_for_timeout(600)
    everything = page.evaluate(
        "() => { const pad = document.querySelector('.wd-scan'); const labels = [...pad.querySelectorAll('[aria-label], [title], [alt]')].map((n) => (n.getAttribute('aria-label') || '') + (n.title || '') + (n.getAttribute('alt') || '')); return [pad.innerText, pad.textContent, ...labels].join(' | '); }"
    )
    assert "scribblescan" not in everything.lower()
    assert page.locator(".wd-scan .sc-k").inner_text().lower() == "it reads"


# ---- weak devices, and the reader switching itself off when the page struggles

HANGS = 'addEventListener("message", ({ data }) => { if (data.type === "load") postMessage({ type: "progress", pct: 10 }); });'  # loads for ever

# a main thread that keeps getting blocked, as a struggling device's would be
JANK = "setInterval(() => { const t = performance.now(); while (performance.now() - t < 170); }, 220)"

FREEZE = "setTimeout(() => { const t = performance.now(); while (performance.now() - t < 900); }, 300)"  # one frozen moment, too short to count as long tasks alone

WEAK = {
    "2 GB of memory": device(2, 8),
    "4 cores": device(8, 4),
    "1 GB and 2 cores": device(1, 2),
}


@pytest.mark.parametrize("kind", list(WEAK))
def test_a_weak_device_does_not_preload_but_still_reads_what_is_written(browser_page, kind) -> None:
    page, base = browser_page
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP, connection=link(effectiveType="4g", saveData=False, type="wifi") + "; " + WEAK[kind])
    page.wait_for_timeout(5000)
    assert calls == []
    write(page, pad_geometry(page))
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert len(calls) == 1
    assert untouched(page)


def test_the_reader_switches_itself_off_when_the_page_struggles_and_stays_off_for_the_visit(browser_page) -> None:
    page, base = browser_page
    calls = serve(page, HANGS)
    open_cover(page, base, DESKTOP, connection=WIFI)
    geo = pad_geometry(page)
    write(page, geo)  # the reader starts loading (and never finishes: it is only here to be working while the page struggles)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'load'", timeout=5000)
    page.evaluate(JANK)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'off'", timeout=8000)
    pad = page.locator(".wd-scan")
    assert pad.locator(".sc-t").inner_text() == "Reading is off on this device"
    assert not pad.locator(".sc-go").is_visible()  # no retry: this is not an error
    assert page.evaluate("sessionStorage.getItem('pad-reader-off')") == "1"
    assert len(calls) == 1
    page.reload()  # a new page in the same visit
    page.wait_for_selector(".wd-scan canvas")
    page.wait_for_timeout(4500)  # past when a preload would start
    assert len(calls) == 1  # no second try
    geo = pad_geometry(page)
    write(page, geo)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'off'", timeout=3000)
    assert page.locator(".wd-scan .sc-t").inner_text() == "Reading is off on this device"
    inked = page.evaluate(
        "() => { const c = document.querySelector('.wd-scan canvas'); return c.getContext('2d').getImageData(0, 0, c.width, c.height).data.some((v, i) => i % 4 === 3 && v > 0); }"
    )
    assert inked  # it is still a drawing pad
    assert len(calls) == 1
    assert untouched(page)


def test_a_single_freeze_switches_the_reader_off_by_the_frame_rule_alone(browser_page) -> None:
    page, base = browser_page
    serve(page, HANGS)
    open_cover(page, base, DESKTOP, connection=WIFI)
    write(page, pad_geometry(page))
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'load'", timeout=5000)
    page.evaluate(FREEZE)  # 900 ms: past the freeze rule (800 ms), under the long-task rule (1.2 s)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'off'", timeout=5000)


def test_once_off_nothing_keeps_watching_and_even_a_tiny_mark_gets_the_note(browser_page) -> None:
    page, base = browser_page
    serve(page, HANGS)
    open_cover(page, base, DESKTOP, connection=WIFI)
    geo = pad_geometry(page)
    write(page, geo)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'load'", timeout=5000)
    page.evaluate(JANK)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'off'", timeout=8000)
    page.evaluate("for (let i = 1; i < 10000; i++) clearInterval(i)")  # the page is quiet again
    page.wait_for_timeout(300)
    page.evaluate("(() => { window.__raf = 0; const raf = window.requestAnimationFrame.bind(window); window.requestAnimationFrame = (f) => { window.__raf++; return raf(f); }; })()")
    page.wait_for_timeout(1500)
    assert page.evaluate("window.__raf") < 10  # the watch's own frame loop is gone (it asked for a frame every 16 ms)
    x, y = screen(geo, 0.5, 0.9)
    stroke_mouse(page, [(x, y), (x + 1, y)])  # a dot, which would otherwise read as "nothing to read"
    page.wait_for_timeout(2200)
    assert page.locator(".wd-scan .sc-t").inner_text() == "Reading is off on this device"


# ---- the clear button

PAD_BLANK = """() => {
  const c = document.querySelector('.wd-scan canvas');
  const clean = !c.width || !c.getContext('2d').getImageData(0, 0, c.width, c.height).data.some((v, i) => i % 4 === 3 && v > 0);
  const pad = document.querySelector('.wd-scan');
  return { clean, text: pad.querySelector('.sc-t').textContent, state: pad.dataset.state, word: pad.querySelector('.sc-w').textContent };
}"""


def clear_button(page):
    return page.locator(".wd-scan .sc-clear")


def test_the_clear_button_wipes_the_ink_and_the_text_and_leaves_the_reader_loaded(browser_page) -> None:
    page, base = browser_page
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP)
    assert clear_button(page).is_hidden()  # nothing to clear yet
    geo = pad_geometry(page)
    write(page, geo)
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    button = clear_button(page)
    assert button.is_visible()
    assert button.get_attribute("aria-label") == "Clear the pad"
    box = button.bounding_box()
    assert box["width"] >= 36 and box["height"] >= 36  # a comfortable target (44 where the pointer is a finger)
    button.click()
    assert page.evaluate(PAD_BLANK) == {"clean": True, "text": "", "state": "idle", "word": ""}  # no stroke was started by the press either
    assert button.is_hidden()
    page.wait_for_timeout(4000)  # the little word demo does not start over an empty pad
    assert page.evaluate(PAD_BLANK) == {"clean": True, "text": "", "state": "idle", "word": ""}
    page.evaluate(WATCH)
    write(page, geo)  # and it writes and reads again
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert "load" not in {s[0] for s in page.evaluate("window.__seen")}  # the model had stayed loaded
    assert len(calls) == 1
    assert untouched(page)


def test_clearing_in_the_middle_of_a_read_stops_it_from_landing_afterwards(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    geo = pad_geometry(page)
    write(page, geo)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'read'", timeout=10000)
    clear_button(page).click()
    page.wait_for_timeout(1800)  # long past when the stub's answer arrives
    assert page.evaluate(PAD_BLANK) == {"clean": True, "text": "", "state": "idle", "word": ""}
    write(page, geo)
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)  # the next writing is read as normal
    assert untouched(page)


def test_the_pad_can_be_cleared_after_the_reader_switched_off(browser_page) -> None:
    page, base = browser_page
    serve(page, HANGS)
    open_cover(page, base, DESKTOP, connection=WIFI)
    geo = pad_geometry(page)
    write(page, geo)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'load'", timeout=5000)
    page.evaluate(JANK)
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'off'", timeout=8000)
    page.evaluate("for (let i = 1; i < 10000; i++) clearInterval(i)")
    clear_button(page).click()
    assert page.evaluate(PAD_BLANK) == {"clean": True, "text": "", "state": "idle", "word": ""}
    write(page, geo)  # still a drawing pad, still honest about reading
    page.wait_for_function("document.querySelector('.wd-scan').dataset.state === 'off'", timeout=3000)
    assert page.locator(".wd-scan .sc-t").inner_text() == "Reading is off on this device"
    assert untouched(page)


def test_the_clear_button_works_from_the_keyboard_and_claims_a_sideways_scroll(browser_page) -> None:
    page, base = browser_page
    serve(page, READER)
    open_cover(page, base, DESKTOP)
    write(page, pad_geometry(page))
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    assert page.evaluate("!document.querySelector('.wd-scan .sc-clear').dispatchEvent(new WheelEvent('wheel', { deltaX: 200, bubbles: true, cancelable: true }))")
    clear_button(page).focus()
    page.keyboard.press("Enter")
    assert page.evaluate(PAD_BLANK)["clean"] and page.evaluate(PAD_BLANK)["text"] == ""
    assert untouched(page)


def test_clearing_calls_off_the_read_in_the_worker_too(browser_page) -> None:
    page, base = browser_page
    serve(page, CANCELLABLE_READER)
    page.add_init_script("window.__stub = []; new BroadcastChannel('stub').onmessage = (e) => window.__stub.push(e.data)")
    open_cover(page, base, DESKTOP)
    geo = pad_geometry(page)
    stroke_mouse(page, [screen(geo, 0.1, 0.12), screen(geo, 0.6, 0.15)])  # two rows, so the read takes a second
    stroke_mouse(page, [screen(geo, 0.1, 0.62), screen(geo, 0.6, 0.65)])
    page.wait_for_function("window.__stub.some((m) => m.startsWith('read:'))", timeout=10000)
    clear_button(page).click()
    page.wait_for_function("window.__stub.some((m) => m.startsWith('cancel:'))", timeout=3000)  # the worker was told
    page.wait_for_function("window.__stub.some((m) => m.startsWith('stopped:'))", timeout=3000)  # and stopped before the second line
    assert not any(m.endswith("after 2") for m in page.evaluate("window.__stub"))
    assert page.evaluate(PAD_BLANK) == {"clean": True, "text": "", "state": "idle", "word": ""}
    write(page, geo)  # the same worker reads the next writing
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)


def test_the_clear_button_works_with_a_finger_and_does_not_turn_the_page(mobile_browser_page) -> None:
    page, base = mobile_browser_page
    serve(page, READER)
    open_cover(page, base)
    cdp = page.context.new_cdp_session(page)
    geo = pad_geometry(page)
    stroke_touch(cdp, [screen(geo, 0.1, 0.3), screen(geo, 0.6, 0.35)])
    page.wait_for_function("document.querySelector('.wd-scan .sc-t').textContent === 'line 1'", timeout=10000)
    box = clear_button(page).bounding_box()
    assert box["width"] >= 44 and box["height"] >= 44  # a full finger-sized target on a phone
    cx, cy = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    before = page.evaluate(PAD_BLANK)
    stroke_touch(cdp, [(cx, cy), (cx - 40, cy + 2)])  # a swipe that starts on the visible button: not a page turn, not a stroke
    page.wait_for_timeout(300)
    assert untouched(page)
    assert page.evaluate(PAD_BLANK)["text"] == before["text"] and not page.evaluate(PAD_BLANK)["clean"]  # the ink is as it was: nothing was drawn or cleared by a swipe
    stroke_touch(cdp, [(cx, cy)])  # a tap clears
    page.wait_for_timeout(300)
    assert page.evaluate(PAD_BLANK) == {"clean": True, "text": "", "state": "idle", "word": ""}
    assert untouched(page)


# ---- the geometry that turns strokes into lines, without a browser pad or a model

SPLIT = """async () => {
  const ink = await import('/static/js/notebook/stickers/ink.js');
  const H = 120; // four rows of 30
  const line = (y, x0 = 10, x1 = 80) => [[x0, y], [(x0 + x1) / 2, y + 3], [x1, y]];
  const rows = ink.splitRows([line(8), line(70), line(75, 20, 90), [[5, 100], [6, 100]]], H); // rows 1 and 3, and a stray touch in row 4
  const raster = ink.rasterRow([line(8)], 30);
  const px = (i) => raster.data.slice(i * 4, i * 4 + 3);
  const dark = Array.from({ length: raster.width * raster.height }, (_, i) => px(i)).filter(([r, g, b]) => r + g + b < 200).length;
  return { rows: rows.map((r) => [r.row, r.strokes.length]), width: raster.width, height: raster.height, corner: [...px(0)], dark, rowOfLow: ink.rowOf(line(118), H), rowOfSpill: ink.rowOf([[0, 28], [1, 38]], H) };
}"""


def test_strokes_are_split_by_ruled_row_and_redrawn_for_the_model(browser_page) -> None:
    page, base = browser_page
    page.goto(base + "/")
    result = page.evaluate(SPLIT)
    assert result["rows"] == [[0, 1], [2, 2]]  # empty rows and the stray touch are skipped
    assert result["rowOfLow"] == 3 and result["rowOfSpill"] == 1  # a stroke belongs to the row its middle is in
    assert result["corner"] == [255, 255, 255]  # dark ink on white, whatever colour it was on the pad
    assert result["dark"] > 100 and result["width"] >= result["height"]
