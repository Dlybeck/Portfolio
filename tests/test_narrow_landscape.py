"""A phone on its side that is narrower than 640px (an iPhone SE is 568x320) gets the short-landscape spread, not a stamp-sized one-page book."""

from __future__ import annotations

import pytest

# widths just under the old 640px boundary, at the heights phones have on their side
SIZES = [(568, 320), (600, 360), (639, 360), (480, 320)]

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


def test_a_portrait_phone_keeps_the_one_page_book(browser_page) -> None:
    """The portrait phone layout does not change: a window that is taller than wide, however short, stays the one-page book."""
    page, base = browser_page
    page.set_viewport_size({"width": 320, "height": 480})
    page.goto(base + "/projects/websites/scribblescan")
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    assert "nb--phone" in page.locator("#notebook").get_attribute("class")
