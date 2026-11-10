"""Turning a page is a step in the browser's history: Back undoes it and Forward redoes it, whichever way the page was turned."""

from __future__ import annotations

import pytest

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1440, "height": 900}
START = "/projects/websites/scribblescan"  # a page with a page before it and a page after it, on a phone and on desktop

# A trackpad flick, fired from the page at 60 Hz: deltas that swell and fade, summing to `total` (sign gives the direction).
FLICK = """async ({ total, sign, n }) => {
  const dial = document.querySelector('.wheel-dial');
  const weights = Array.from({ length: n }, (_, i) => Math.sin(Math.PI * (i + 0.5) / n) ** 1.5);
  const sum = weights.reduce((a, b) => a + b, 0);
  for (const w of weights) {
    dial.dispatchEvent(new WheelEvent('wheel', { deltaY: sign * total * w / sum, deltaMode: 0, bubbles: true, cancelable: true }));
    await new Promise((done) => setTimeout(done, 16));
  }
}"""


def shown(page) -> str:
    # a Back that leaves the notebook (to the cover, or off the site) reads as that, instead of waiting for a #notebook that is gone
    return page.evaluate("document.getElementById('notebook')?.dataset.page ?? `left the notebook: ${location.href}`")


def open_at(page, base: str, viewport: dict) -> str:
    page.set_viewport_size(viewport)
    page.goto(base + START)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(900)
    return shown(page)


def corner(page) -> None:
    page.locator(".nb-ear.next").click(force=True)


def swipe(page) -> None:
    box = page.locator(".nb-book").bounding_box()
    x, y = box["x"] + box["width"] / 2, box["y"] + box["height"] * 0.3
    page.mouse.move(x, y)
    page.mouse.down()
    page.mouse.move(x - 150, y, steps=6)
    page.mouse.up()


def flick(page) -> None:
    page.evaluate(FLICK, {"total": 150, "sign": 1, "n": 40})


def arrow_key(page) -> None:
    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
@pytest.mark.parametrize("turn", [corner, flick, arrow_key], ids=["corner", "wheel-flick", "dial-key"])
def test_browser_back_undoes_a_page_turn_and_forward_redoes_it(browser_page, viewport, turn) -> None:
    page, base = browser_page
    start = open_at(page, base, viewport)

    turn(page)
    page.wait_for_timeout(2300)
    turned = shown(page)
    assert turned != start

    page.go_back()
    page.wait_for_timeout(1300)
    assert shown(page) == start

    page.go_forward()
    page.wait_for_timeout(1300)
    assert shown(page) == turned


def test_browser_back_undoes_a_swipe(browser_page) -> None:
    page, base = browser_page
    start = open_at(page, base, DESKTOP)

    swipe(page)
    page.wait_for_timeout(1300)
    assert shown(page) != start

    page.go_back()
    page.wait_for_timeout(1300)
    assert shown(page) == start


def test_each_corner_turn_is_its_own_history_step(browser_page) -> None:
    page, base = browser_page
    first = open_at(page, base, PHONE)
    corner(page)
    page.wait_for_timeout(1000)
    second = shown(page)
    corner(page)
    page.wait_for_timeout(1000)
    assert len({first, second, shown(page)}) == 3

    page.go_back()
    page.wait_for_timeout(1000)
    assert shown(page) == second
    page.go_back()
    page.wait_for_timeout(1000)
    assert shown(page) == first
    assert "scribblescan" in page.evaluate("location.pathname")  # still in the notebook, not sent off the site


def test_a_wheel_spin_through_several_pages_is_one_history_step(browser_page) -> None:
    page, base = browser_page
    start = open_at(page, base, DESKTOP)

    page.evaluate(FLICK, {"total": 400, "sign": 1, "n": 60})
    page.wait_for_timeout(2500)
    assert shown(page) != start

    page.go_back()
    page.wait_for_timeout(1300)
    assert shown(page) == start


def test_going_back_keeps_the_forward_entries(browser_page) -> None:
    """Showing an entry that Back or Forward landed on must not push a new one on top (that would erase Forward)."""
    page, base = browser_page
    open_at(page, base, DESKTOP)
    corner(page)
    page.wait_for_timeout(1000)
    corner(page)
    page.wait_for_timeout(1000)
    last = shown(page)

    page.go_back()
    page.wait_for_timeout(1000)
    page.go_back()
    page.wait_for_timeout(1000)
    page.go_forward()
    page.wait_for_timeout(1000)
    page.go_forward()
    page.wait_for_timeout(1000)
    assert shown(page) == last
