"""Turning a page on desktop never puts a page corner or a folio on a bare inside cover, before or while the leaf lands."""

from __future__ import annotations

import pytest

DESKTOP = {"width": 1440, "height": 900}

# every animation frame for a while: which page corners and folios are showing, and are any of them on an inside cover?
WATCH = """() => {
  window.__stray = [];
  const t0 = performance.now();
  const shown = (n) => { const r = n.getBoundingClientRect(), cs = getComputedStyle(n);
    return r.width > 0 && r.height > 0 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.05; };
  const tick = () => {
    const covers = [...document.querySelectorAll('.nb-book > .nb-page')].filter((p) => p.querySelector('.cover-inside') && shown(p)).map((p) => p.getBoundingClientRect());
    for (const n of document.querySelectorAll('.nb-book > .nb-ear, .nb-book > .nb-pn, .nb-book > .nb-hint-flip')) {
      if (!shown(n)) continue;
      const r = n.getBoundingClientRect(), x = (r.left + r.right) / 2, y = (r.top + r.bottom) / 2;
      if (covers.some((c) => x > c.left && x < c.right && y > c.top && y < c.bottom)) window.__stray.push([Math.round(performance.now() - t0), n.className]);
    }
    if (performance.now() - t0 < 1500) requestAnimationFrame(tick);
  };
  tick();
}"""


def watch_while(browser_page, route, action):
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(900)
    page.evaluate(WATCH)
    page.evaluate(action)
    page.wait_for_timeout(1700)
    return page.evaluate("window.__stray")


@pytest.mark.parametrize(
    "route,action",
    [
        ("/#contents", "document.querySelector('.nb-ear.next').click()"),  # first spread, forward: the left is the inside front cover until the leaf lands
        ("/projects/websites/scribblescan", "document.querySelector('.nb-ear.prev').click()"),  # back onto the first spread
        ("/hobbies/tennis", "document.querySelector('.nb-ear.next').click()"),  # forward onto the last spread
        ("/#say-hi", "document.querySelector('.nb-ear.prev').click()"),  # back off the last spread: the right is the inside back cover until the leaf lands
    ],
    ids=["first-forward", "first-back", "last-forward", "last-back"],
)
def test_no_page_corner_or_folio_shows_on_an_inside_cover_during_a_turn(browser_page, route, action) -> None:
    assert watch_while(browser_page, route, action) == []
