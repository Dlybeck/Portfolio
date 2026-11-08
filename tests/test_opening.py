"""The book opening and closing: one continuous move (the cover swings on its spine while the book slides)."""

from __future__ import annotations

DESKTOP = {"width": 1280, "height": 800}
PHONE = {"width": 390, "height": 844}

# what the page records while the cover moves: sampled every animation frame, so nothing between frames is missed
WATCH = """() => {
  window.__samples = [];
  const book = document.querySelector('.nb-book'), root = document.getElementById('notebook');
  const t0 = performance.now();
  const tick = () => {
    const leaf = document.querySelector('.nb-leaf.cover');
    const left = document.querySelector('.nb-page.l');
    const back = document.querySelector('.nb-back');
    window.__samples.push({
      t: Math.round(performance.now() - t0),
      opening: root.classList.contains('is-opening'),
      closed: root.classList.contains('is-closed'),
      leaf: leaf ? { w: leaf.offsetWidth, h: leaf.offsetHeight, transform: getComputedStyle(leaf).transform, opacity: getComputedStyle(leaf).opacity } : null,
      folio: (() => { const f = document.querySelector('.nb-pn.lft'); return f ? getComputedStyle(f).visibility : null; })(),
      leftVisible: left ? getComputedStyle(left).visibility : null,
      leftOpacity: left ? getComputedStyle(left).opacity : null,
      book: getComputedStyle(book).transform,
      backW: back.offsetWidth, backH: back.offsetHeight,
      tabs: (() => { const t = document.querySelector('.nb-tabs'); return t ? getComputedStyle(t).opacity : null; })(),
    });
    if (performance.now() - t0 < 1500) requestAnimationFrame(tick);
  };
  tick();
}"""


def start(browser_page, route, viewport, reduced=False):
    page, base = browser_page
    if reduced:
        page.emulate_media(reduced_motion="reduce")
    page.set_viewport_size(viewport)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(600)
    return page


def samples(page):
    page.wait_for_timeout(1700)
    return page.evaluate("window.__samples")


def translate_x(matrix: str) -> float:
    if matrix in ("none", ""):
        return 0.0
    return float(matrix.strip("matrix()").split(",")[4])


def test_desktop_opening_is_one_swing_on_the_spine_with_the_book_sliding_at_the_same_time(browser_page) -> None:
    page = start(browser_page, "/", DESKTOP)
    page.evaluate(WATCH)
    page.locator(".cover-open").click(no_wait_after=True)
    s = samples(page)

    moving = [x for x in s if x["leaf"] and x["opening"]]
    assert len(moving) >= 10, len(moving)  # a real animation, not a jump
    # the cover is never scaled or stretched: its box and its back board keep their size the whole time
    assert len({(x["leaf"]["w"], x["leaf"]["h"]) for x in moving}) == 1
    assert len({(x["backW"], x["backH"]) for x in s}) == 1
    assert all("matrix3d" in x["leaf"]["transform"] or x["leaf"]["transform"] in ("none", "matrix(1, 0, 0, 1, 0, 0)") for x in moving)
    # the swing is a rotation about the vertical axis: matrix3d(a, 0, c, 0 ...) with a = cos and c = sin
    swing = [float(x["leaf"]["transform"].strip("matrix3d()").split(",")[0]) for x in moving if "matrix3d" in x["leaf"]["transform"]]
    assert max(swing) > 0.9 and min(swing) < -0.95, (max(swing), min(swing))  # from flat shut to flat open (cos 0 to cos 180)
    # at the same time the book slides: its position changes during the swing, not before or after
    slides = [translate_x(x["book"]) for x in moving]
    assert slides[0] < -50 and abs(slides[-1]) < 40 and slides[0] < slides[len(slides) // 2] < slides[-1]
    # the real left page waits until the cover has landed on it: no fade, no second flip
    assert all(x["leftVisible"] == "hidden" for x in moving)
    assert all(x["folio"] == "hidden" for x in moving)  # the left page number does not float on the empty board
    done = [x for x in s if not x["leaf"] and not x["opening"]]
    assert done and all(x["leftVisible"] == "visible" and x["leftOpacity"] == "1" and abs(translate_x(x["book"])) < 0.5 for x in done)
    # the tabs are always there: they ride with the book and slide out with the cover (no fade, no pop; see test_tabs.py)
    assert all(x["tabs"] == "1" for x in moving)
    assert page.locator(".nb-tabs").is_visible()


def test_the_opening_takes_under_a_second_with_an_ease_in_out(browser_page) -> None:
    page = start(browser_page, "/", DESKTOP)
    page.evaluate(WATCH)
    page.locator(".cover-open").click(no_wait_after=True)
    s = samples(page)

    opening = [x for x in s if x["opening"]]
    span = opening[-1]["t"] - opening[0]["t"]
    assert 650 <= span <= 950, span
    angles = []  # (time, degrees)
    for x in opening:
        if x["leaf"] and "matrix3d" in x["leaf"]["transform"]:
            import math
            angles.append((x["t"], math.degrees(math.acos(max(-1, min(1, float(x["leaf"]["transform"].strip("matrix3d()").split(",")[0])))))))
    # ease-in-out: symmetric, so the cover is about half way round (90 degrees) half way through the time
    middle = opening[0]["t"] + span / 2
    halfway = min(angles, key=lambda a: abs(a[0] - middle))[1]
    assert 60 < halfway < 120, halfway


def test_desktop_closing_is_the_same_move_in_reverse(browser_page) -> None:
    page = start(browser_page, "/jobs", DESKTOP)
    page.evaluate(WATCH)
    page.evaluate("document.querySelector('[data-home]').click()")
    s = samples(page)

    moving = [x for x in s if x["leaf"] and x["opening"]]
    assert len(moving) >= 10
    assert len({(x["leaf"]["w"], x["leaf"]["h"]) for x in moving}) == 1
    swing = [float(x["leaf"]["transform"].strip("matrix3d()").split(",")[0]) for x in moving if "matrix3d" in x["leaf"]["transform"]]
    assert min(swing) < -0.9 and swing[0] < swing[-1]  # starts lying open on the left, ends flat shut
    slides = [translate_x(x["book"]) for x in moving]
    assert slides[0] > -40 and slides[-1] < -50  # and the book slides back to its shut, centred spot
    assert all(x["leftVisible"] == "hidden" for x in moving)
    assert s[-1]["closed"] and s[-1]["leaf"] is not None


def test_with_reduced_motion_the_cover_cross_fades_and_nothing_swings_or_slides(browser_page) -> None:
    page = start(browser_page, "/", DESKTOP, reduced=True)
    page.evaluate(WATCH)
    page.locator(".cover-open").click(no_wait_after=True)
    s = samples(page)

    assert not any(x["opening"] for x in s)
    fading = [x for x in s if x["leaf"]]
    assert fading and all("matrix3d" not in x["leaf"]["transform"] for x in fading)
    after_click = [x for x in s if not x["closed"]]
    assert after_click and all(abs(translate_x(x["book"])) < 0.5 for x in after_click)  # the book is at its open spot at once
    assert fading[-1]["t"] < 500 and min(float(x["leaf"]["opacity"]) for x in fading) < 0.6  # it fades out, quickly
    assert s[-1]["leftVisible"] == "visible" and not s[-1]["leaf"]


def test_with_reduced_motion_closing_cross_fades_in(browser_page) -> None:
    page = start(browser_page, "/jobs", DESKTOP, reduced=True)
    page.evaluate(WATCH)
    page.evaluate("document.querySelector('[data-home]').click()")
    s = samples(page)

    assert not any(x["opening"] for x in s)
    leaf = [x for x in s if x["leaf"]]
    assert leaf and all("matrix3d" not in x["leaf"]["transform"] for x in leaf)
    assert float(leaf[0]["leaf"]["opacity"]) < 0.5 and float(leaf[-1]["leaf"]["opacity"]) == 1.0


def test_phone_opening_still_swings_over_the_first_page_without_a_second_flip(browser_page) -> None:
    page = start(browser_page, "/", PHONE)
    page.evaluate(WATCH)
    page.locator(".cover-open").click(no_wait_after=True)
    s = samples(page)

    assert len([x for x in s if x["leaf"]]) >= 8
    assert not s[-1]["leaf"] and not s[-1]["closed"]
    assert page.locator("#notebook").get_attribute("data-page") == "toc"
    # the book does not move on a phone, and the cover keeps its size
    assert len({translate_x(x["book"]) for x in s}) == 1
    assert len({(x["leaf"]["w"], x["leaf"]["h"]) for x in s if x["leaf"]}) == 1
