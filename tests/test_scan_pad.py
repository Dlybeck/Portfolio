"""The ScribbleScan pad on the cover: its strokes belong to it, it reads them lazily, and it always says what it is doing.

The reader (a worker that fetches a 65 MB model) is replaced by a stub here, so none of this downloads anything.
"""

from __future__ import annotations

import math

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
BROKEN_READER = 'addEventListener("message", () => postMessage({ type: "error", message: "network down" }));'


def serve(page, *bodies):
    """Answer each request for the reader's worker with the next body (the last one repeats)."""
    calls = []

    def handle(route):
        calls.append(route.request.url)
        route.fulfill(body=bodies[min(len(calls), len(bodies)) - 1], content_type="text/javascript")

    page.route(WORKER, handle)
    return calls


def open_cover(page, base, viewport=None):
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


def test_nothing_is_fetched_until_the_pad_is_used(browser_page) -> None:
    page, base = browser_page
    requested = []
    page.on("request", lambda r: requested.append(r.url))
    calls = serve(page, READER)
    open_cover(page, base, DESKTOP)
    page.wait_for_timeout(1500)
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
    assert len(set(fractions)) >= 3 and fractions == sorted(fractions)  # the bar moved, and only forwards
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
