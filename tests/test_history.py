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
    assert order_index(page) - order_index_of(page, start) >= 3  # it crossed several pages, so one Back undoing it means they share an entry

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


ORDER = """(id) => { const d = JSON.parse(document.getElementById('nb-data').textContent);
  const order = document.querySelector('.nb--phone') ? d.phone : d.desktop;
  return order.indexOf(id ?? document.getElementById('notebook').dataset.page); }"""


def order_index(page) -> int:
    return page.evaluate(ORDER, None)


def order_index_of(page, page_id: str) -> int:
    return page.evaluate(ORDER, page_id)


def test_a_wheel_spin_started_right_after_a_corner_turn_keeps_that_turns_entry(browser_page) -> None:
    page, base = browser_page
    open_at(page, base, DESKTOP)
    corner(page)
    page.wait_for_timeout(300)  # well inside any timer a spin might use to join the entry before it
    cornered = shown(page)
    page.evaluate(FLICK, {"total": 150, "sign": 1, "n": 40})
    page.wait_for_timeout(2300)
    assert shown(page) != cornered

    page.go_back()
    page.wait_for_timeout(1300)
    assert shown(page) == cornered


def test_each_dial_key_press_is_its_own_history_step(browser_page) -> None:
    page, base = browser_page
    first = open_at(page, base, DESKTOP)
    page.locator(".wheel-dial").focus()
    seen = [first]
    for _ in range(3):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(1000)
        seen.append(shown(page))
    assert len(set(seen)) == 4

    for expected in reversed(seen[:-1]):
        page.go_back()
        page.wait_for_timeout(1000)
        assert shown(page) == expected


def test_one_wheel_spin_from_the_shut_cover_is_one_history_step(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    page.goto(base + "/")
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(900)
    assert "is-closed" in page.locator("#notebook").get_attribute("class")

    page.evaluate(FLICK, {"total": 260, "sign": 1, "n": 50})
    page.wait_for_timeout(2800)
    assert "is-closed" not in page.locator("#notebook").get_attribute("class")
    assert order_index(page) >= 2  # the spin opened the book and carried on through pages

    page.go_back()
    page.wait_for_timeout(1500)
    assert "is-closed" in page.locator("#notebook").get_attribute("class")


NUDGE = """async (deltas) => {
  const dial = document.querySelector('.wheel-dial');
  for (const d of deltas) {
    dial.dispatchEvent(new WheelEvent('wheel', { deltaY: d, deltaMode: 0, bubbles: true, cancelable: true }));
    await new Promise((done) => setTimeout(done, 120));
  }
}"""


def test_a_scroll_that_goes_forward_and_back_in_one_go_leaves_no_extra_entry(browser_page) -> None:
    """With reduced motion each 70px of scroll is one notch, so +80 then -80 within a pause is one input that ends where it began."""
    page, base = browser_page
    page.emulate_media(reduced_motion="reduce")
    first = open_at(page, base, DESKTOP)
    corner(page)
    page.wait_for_timeout(800)
    second = shown(page)
    assert second != first

    page.evaluate(NUDGE, [80, -80])
    page.wait_for_timeout(800)
    assert shown(page) == second  # it came back to where it started

    page.go_back()
    page.wait_for_timeout(800)
    assert shown(page) == first  # one Back undoes the corner turn; the scroll left nothing in between


def test_two_quick_dial_key_presses_are_two_history_steps(browser_page) -> None:
    page, base = browser_page
    first = open_at(page, base, DESKTOP)
    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(60)  # the second press comes before the first page has flipped
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(2300)
    assert order_index(page) - order_index_of(page, first) == 2

    page.go_back()
    page.wait_for_timeout(1300)
    assert order_index(page) - order_index_of(page, first) == 1  # one press undone, not both
