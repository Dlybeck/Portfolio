"""The phone wheel can be grabbed from a much wider area, without taking over the page; and it never covers the tabs."""

from __future__ import annotations

import math

import pytest

PHONES = [{"width": 360, "height": 740}, {"width": 390, "height": 844}, {"width": 430, "height": 932}]
IDS = lambda v: f"{v['width']}x{v['height']}"  # noqa: E731
DRAWN = 120  # the drawn dial's radius
GRAB = 190  # the invisible grab circle's radius


def visit(browser_page, route, viewport, touch=False):
    page, base = browser_page
    page.set_viewport_size(viewport)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(900)
    return page


def centre(page):
    box = page.locator(".wheel-dial").bounding_box()
    return box["x"] + box["width"] / 2, box["y"] + box["height"] / 2


def is_dial(page, x, y) -> bool:
    return page.evaluate("([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && !!e.closest('.wheel-dial'); }", [x, y])


@pytest.mark.parametrize("viewport", PHONES, ids=IDS)
def test_the_grab_area_reaches_well_beyond_the_drawn_wheel_and_stops_at_its_edge(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)
    cx, cy = centre(page)

    for deg in (-90, -65, -115, -40, -140):  # straight up and either side
        a = math.radians(deg)
        inside = (cx + math.cos(a) * (GRAB - 12), cy + math.sin(a) * (GRAB - 12))
        beyond = (cx + math.cos(a) * (GRAB + 12), cy + math.sin(a) * (GRAB + 12))
        if 0 <= inside[0] <= viewport["width"] and 0 <= inside[1] <= viewport["height"]:
            assert is_dial(page, *inside), (deg, inside)  # in the invisible circle: the wheel
        if 0 <= beyond[0] <= viewport["width"] and 0 <= beyond[1] <= viewport["height"]:
            assert not is_dial(page, *beyond), (deg, beyond)  # past it: the page
    assert is_dial(page, cx, cy - (DRAWN + 50))  # well above what is drawn, but inside the grab circle


@pytest.mark.parametrize("viewport", PHONES, ids=IDS)
def test_the_larger_grab_area_does_not_cover_the_page_corners_or_the_cover_button(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)
    for sel in (".nb-ear.next", ".nb-ear.prev"):
        if page.locator(sel).count() and page.locator(sel).is_visible():
            box = page.locator(sel).bounding_box()
            x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
            assert page.evaluate("([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && !!e.closest('.nb-ear'); }", [x, y]), sel

    page = visit(browser_page, "/", viewport)
    box = page.locator(".cover-open").bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] / 2
    assert page.evaluate("([x, y]) => { const e = document.elementFromPoint(x, y); return !!e && !!e.closest('.cover-open'); }", [x, y])


@pytest.mark.parametrize("viewport", PHONES, ids=IDS)
def test_a_finger_can_turn_the_wheel_from_outside_the_drawn_circle(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)
    cdp = page.context.new_cdp_session(page)
    cx, cy = centre(page)
    start = (cx - 150 * math.cos(math.radians(60)) * -1, cy - 150)  # straight above the centre, 150px: outside the drawn 120px circle
    start = (cx, cy - 150)
    assert is_dial(page, *start)
    before = page.locator("#notebook").get_attribute("data-page")

    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": start[0], "y": start[1]}]})
    for i in range(1, 9):  # drag sideways along the top of the circle, like turning a wheel
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": start[0] - i * 14, "y": start[1]}]})
        page.wait_for_timeout(16)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(1200)
    assert page.locator("#notebook").get_attribute("data-page") != before


@pytest.mark.parametrize("viewport", PHONES, ids=IDS)
def test_the_page_still_scrolls_and_its_taps_work_away_from_the_wheel(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)
    cdp = page.context.new_cdp_session(page)
    x, y = viewport["width"] / 2, 300  # the middle of the page, far above the wheel
    assert not is_dial(page, x, y)

    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x, "y": y + 120}]})
    for i in range(1, 9):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y + 120 - i * 25}]})
        page.wait_for_timeout(16)
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(700)
    assert page.locator(".nb-in").first.evaluate("n => n.scrollTop") > 0  # it scrolled
    assert page.locator("#notebook").get_attribute("data-page") == "work"  # and did not turn


SWEEP_WIDTHS = (320, 360, 390, 430, 600, 640, 700, 768, 844, 900, 960, 1024, 1280, 1920)
SWEEP_HEIGHTS = (300, 360, 390, 450, 500, 600, 700, 800, 1000)


def test_the_wheel_never_touches_the_section_tabs_at_any_window_size(browser_page) -> None:
    page = visit(browser_page, "/jobs", {"width": 1280, "height": 800})
    js = """(grab) => {
      const d = document.querySelector('.wheel-dial').getBoundingClientRect();
      const cx = d.left + d.width / 2, cy = d.top + d.height / 2;
      const r = document.getElementById('notebook').classList.contains('nb--phone') && innerHeight > 480 ? grab : d.width / 2;
      const hits = [];
      for (const t of document.querySelectorAll('.nb-tab')) {
        const b = t.getBoundingClientRect();
        const nx = Math.max(b.left, Math.min(cx, b.right)), ny = Math.max(b.top, Math.min(cy, b.bottom));
        if (Math.hypot(nx - cx, ny - cy) < r) hits.push(t.textContent);
      }
      return hits;
    }"""
    bad = []
    for w in SWEEP_WIDTHS:
        for h in SWEEP_HEIGHTS:
            page.set_viewport_size({"width": w, "height": h})
            page.wait_for_timeout(200)
            hits = page.evaluate(js, GRAB)
            if hits:
                bad.append((w, h, hits))
    assert not bad, bad
