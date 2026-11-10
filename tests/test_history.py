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


def test_turning_the_wheel_after_the_layout_switches_does_not_overwrite_the_previous_entry(browser_page) -> None:
    """Rotating a phone rebuilds the book with a new wheel that numbers its inputs from 1 again; that must not join the old wheel's entry."""
    page, base = browser_page
    first = open_at(page, base, DESKTOP)
    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")  # the old wheel's first input
    page.wait_for_timeout(1300)
    second = shown(page)
    assert second != first

    page.set_viewport_size(PHONE)  # the book is rebuilt in the phone layout, with a new wheel
    page.wait_for_selector("#notebook.nb--phone")
    page.wait_for_timeout(900)
    assert shown(page) == second
    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")  # the new wheel's first input
    page.wait_for_timeout(1300)
    third = shown(page)
    assert third != second

    page.go_back()
    page.wait_for_timeout(1000)
    assert shown(page) == second  # (written over, Back would have skipped this page)


def test_a_scroll_after_back_starts_its_own_entry_instead_of_overwriting_the_one_back_landed_on(browser_page) -> None:
    """Back ends a wheel input: turns the same scroll makes afterwards must not replace the entry Back just landed on."""
    page, base = browser_page
    first = open_at(page, base, DESKTOP)
    corner(page)
    page.wait_for_timeout(900)
    second = shown(page)
    assert second != first

    page.evaluate(
        """async () => {
          const dial = document.querySelector('.wheel-dial');
          const scroll = async (n) => { for (let i = 0; i < n; i++) {
            dial.dispatchEvent(new WheelEvent('wheel', { deltaY: 40, deltaMode: 0, bubbles: true, cancelable: true }));
            await new Promise((done) => setTimeout(done, 16)); } };
          await scroll(8);
          history.back(); // Back is pressed in the middle of one scroll; the scroll carries on
          await new Promise((done) => setTimeout(done, 80));
          await scroll(8);
        }"""
    )
    page.wait_for_timeout(2500)
    landed = shown(page)
    assert "left the notebook" not in landed

    page.go_back()  # the entry Back landed on is still there to go back to, not overwritten by the scroll that carried on
    page.wait_for_timeout(1000)
    assert shown(page) == second  # (written over, it would have skipped this page and gone to `first`)


SPIN_THEN_BACK = """async () => {
  const dial = document.querySelector('.wheel-dial');
  const scroll = async (n) => { for (let i = 0; i < n; i++) {
    dial.dispatchEvent(new WheelEvent('wheel', { deltaY: 14, deltaMode: 0, bubbles: true, cancelable: true }));
    await new Promise((done) => setTimeout(done, 16)); } };
  await scroll(25);
  history.back(); // Back pressed while the trackpad's momentum is still scrolling
  await new Promise((done) => setTimeout(done, 60));
  await scroll(25); // the same spin carries on (no pause long enough to end it)
}"""


def test_back_pressed_in_the_middle_of_a_spin_never_loses_the_history(browser_page) -> None:
    page, base = browser_page
    first = open_at(page, base, DESKTOP)
    corner(page)
    page.wait_for_timeout(900)
    cornered = shown(page)
    assert cornered != first

    page.evaluate(SPIN_THEN_BACK)
    page.wait_for_timeout(2500)
    assert "left the notebook" not in shown(page)

    # A guard, not a proof of the fix: whatever the timing, the spin that carries on after the Back leaves the history intact, so
    # one more Back still lands on a page of the notebook at or before the one the corner reached.
    page.go_back()
    page.wait_for_timeout(1000)
    assert "left the notebook" not in shown(page)
    assert order_index(page) <= order_index_of(page, cornered)


def test_a_key_press_while_the_wheel_glides_after_back_is_one_history_step(browser_page) -> None:
    """Notches earlier key presses aimed at must not be remembered: the wheel glides through them after Back and one press would write several entries."""
    page, base = browser_page
    first = open_at(page, base, DESKTOP)
    page.locator(".wheel-dial").focus()
    for _ in range(2):
        page.keyboard.press("ArrowRight")
        page.wait_for_timeout(1000)
    assert order_index(page) - order_index_of(page, first) == 2

    page.evaluate("history.go(-2)")  # back to where it began; the wheel starts gliding there
    page.wait_for_timeout(120)
    page.keyboard.press("ArrowLeft")
    page.wait_for_timeout(2300)
    landed = shown(page)
    assert order_index(page) == order_index_of(page, first) - 1

    page.go_back()
    page.wait_for_timeout(1000)
    assert shown(page) != landed
    assert order_index_of(page, shown(page)) - order_index_of(page, first) <= 0  # at or before the page it began on, not on one of the pages it had visited ahead of it


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
