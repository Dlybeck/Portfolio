"""Only the drawn fold of a page corner takes a tap: its 56px box is empty above the diagonal, so a link showing there stays reachable."""

from __future__ import annotations

import pytest

PAGE = "/projects/websites/scribblescan"  # a page with a page before it and a page after it
VIEWPORTS = [
    pytest.param({"width": 1440, "height": 900}, id="desktop"),
    pytest.param({"width": 390, "height": 844}, id="phone"),
]

# is the corner the topmost thing at a point `across` px in from its outer edge and `up` px above the book's bottom edge?
HIT = """({ side, across, up }) => {
  const ear = document.querySelector('.nb-ear.' + side).getBoundingClientRect();
  const x = side === 'next' ? ear.right - across : ear.left + across;
  return document.elementFromPoint(x, ear.bottom - up)?.classList.contains('nb-ear') === true;
}"""


@pytest.mark.parametrize("viewport", VIEWPORTS)
@pytest.mark.parametrize("side", ["next", "prev"])
def test_the_corner_takes_taps_on_the_fold_and_not_above_the_diagonal(new_page, live_server_url, viewport, side) -> None:
    page = new_page(viewport=viewport)
    page.goto(live_server_url + PAGE)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(1200)
    on_the_fold = page.evaluate(HIT, {"side": side, "across": 20, "up": 20})
    above_the_diagonal = page.evaluate(HIT, {"side": side, "across": 52, "up": 52})
    assert on_the_fold and not above_the_diagonal


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_a_tap_on_the_fold_still_turns_the_page(new_page, live_server_url, viewport) -> None:
    page = new_page(viewport=viewport)
    page.goto(live_server_url + PAGE)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(1200)
    start = page.evaluate("document.getElementById('notebook').dataset.page")
    box = page.locator(".nb-ear.next").bounding_box()
    page.mouse.click(box["x"] + box["width"] - 15, box["y"] + box["height"] - 15)
    page.wait_for_timeout(1600)
    assert page.evaluate("document.getElementById('notebook').dataset.page") != start
