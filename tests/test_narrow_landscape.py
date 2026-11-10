"""A phone on its side that is 560 to 639px wide (an iPhone SE is 568x320) gets the short-landscape spread, not a stamp-sized one-page book."""

from __future__ import annotations

import pytest

# widths just under the old 640px boundary, at the heights phones have on their side
SIZES = [(560, 320), (568, 320), (600, 360), (639, 360), (639, 320)]
ROUTES = ["/projects/websites/scribblescan", "/jobs", "/education/college", "/hobbies/tennis", "/projects/programs", "/#say-hi"]
CUT_OFF = "() => [...document.querySelectorAll('.nb-in')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.scrollWidth - e.clientWidth)"

METRICS = """() => {
  const box = (s) => { const n = document.querySelector(s); const r = n && n.getBoundingClientRect(); return r && { x: r.left, y: r.top, w: r.width, h: r.height }; };
  const centre = (s) => { const r = document.querySelector(s).getBoundingClientRect(); return [(r.left + r.right) / 2, (r.top + r.bottom) / 2]; };
  const hit = (s) => { const [x, y] = centre(s); const top = document.elementFromPoint(x, y); const n = document.querySelector(s); return top === n || n.contains(top); };
  return { mode: document.getElementById('notebook').className, book: box('.nb-book'), page: box('.nb-page.r'), wheel: box('.wheel'),
           prev: hit('.nb-ear.prev'), next: hit('.nb-ear.next'), hscroll: document.documentElement.scrollWidth - innerWidth };
}"""


@pytest.mark.parametrize("width,height", SIZES, ids=lambda v: str(v))
def test_a_narrow_landscape_phone_gets_a_readable_spread(browser_page, width, height) -> None:
    page, base = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.goto(base + "/projects/websites/scribblescan")
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(500)
    m = page.evaluate(METRICS)

    assert "nb--desktop" in m["mode"], m  # the spread, as at 640px and wider (the one-page layout leaves no height for the book beside the wheel)
    assert m["book"]["h"] >= 220, m  # as a one-page book it was about 110px tall
    assert m["page"]["w"] >= 130, m  # each page has room for words; as a one-page book it was 70px wide
    assert m["book"]["x"] >= m["wheel"]["x"] + m["wheel"]["w"] * 0.5, m  # beside the wheel, not under it
    assert m["prev"] and m["next"], m  # both page corners can be tapped (they covered each other on a 70px page)
    assert m["hscroll"] <= 0, m

    for route in ROUTES:  # and nothing is cut off at a page's edge (the accuracy bars on ScribbleScan were)
        page.goto(base + route)
        page.wait_for_selector("#notebook.nb--desktop")
        page.wait_for_timeout(400)
        assert page.evaluate(CUT_OFF) == [], route


# landscape windows that are tall enough to skip the short-landscape rules but still have two narrow pages (a Surface Duo on its side is 720x540)
MEDIUM = [(700, 530), (720, 540), (800, 600), (839, 530), (900, 530), (899, 700), (900, 611), (939, 700), (959, 700)]
BARS = "() => [...document.querySelectorAll('.nb-page.r .bar i')].map((e) => Math.round(e.getBoundingClientRect().width))"


@pytest.mark.parametrize("width,height", MEDIUM, ids=lambda v: str(v))
def test_a_landscape_window_with_narrow_pages_cuts_nothing_off_and_keeps_its_bars(browser_page, width, height) -> None:
    page, base = browser_page
    page.set_viewport_size({"width": width, "height": height})
    for route in ROUTES:
        page.goto(base + route)
        page.wait_for_selector("#notebook.nb--desktop")
        page.wait_for_timeout(400)
        assert page.evaluate(CUT_OFF) == [], route

    page.goto(base + "/projects/websites/scribblescan")
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(400)
    bars = page.evaluate(BARS)
    assert len(bars) == 3 and min(bars) >= 25, bars  # they were 2px stubs (17-41px up to 940px wide), and the values ran past the page edge


@pytest.mark.parametrize("width,height", [(960, 700), (1100, 610), (1280, 600), (1366, 768)], ids=lambda v: str(v))
def test_a_wide_landscape_window_over_560px_tall_keeps_the_three_column_bars(browser_page, width, height) -> None:
    """The stacked bars are for pages too narrow for the three columns; a wide window this tall keeps them as they were."""
    page, base = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.goto(base + "/projects/websites/scribblescan")
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(400)
    columns = page.evaluate("getComputedStyle(document.querySelector('.nb-page.r .bar')).gridTemplateColumns.split(' ').length")
    assert columns == 3


def test_a_portrait_phone_keeps_the_one_page_book(browser_page) -> None:
    """The portrait phone layout does not change: a window that is taller than wide, however short, stays the one-page book."""
    page, base = browser_page
    page.set_viewport_size({"width": 320, "height": 480})
    page.goto(base + "/projects/websites/scribblescan")
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    assert "nb--phone" in page.locator("#notebook").get_attribute("class")
