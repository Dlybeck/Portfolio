"""Touch: a clear sideways swipe turns one page; rows, scrolling and taps behave as before."""

from __future__ import annotations


def open_with_touch(mobile_browser_page, route):
    page, base = mobile_browser_page
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone")
    page.wait_for_timeout(400)
    return page, page.context.new_cdp_session(page)


def swipe(cdp, x0, y0, x1, y1, steps=8, step_ms=0):
    """A finger drag, sent as real touch events."""
    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x0, "y": y0}]})
    for i in range(1, steps + 1):
        x = x0 + (x1 - x0) * i / steps
        y = y0 + (y1 - y0) * i / steps
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x, "y": y}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})


def current(page) -> str:
    return page.locator("#notebook").get_attribute("data-page")


def test_swiping_left_turns_to_the_next_page_and_right_turns_back(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/jobs")

    swipe(cdp, 300, 400, 120, 410)
    page.wait_for_timeout(900)
    assert current(page) == "school"
    swipe(cdp, 120, 400, 300, 395)
    page.wait_for_timeout(900)
    assert current(page) == "work"


def test_one_swipe_turns_exactly_one_page(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/jobs")

    swipe(cdp, 330, 400, 40, 400, steps=14)
    page.wait_for_timeout(1000)
    assert current(page) == "school"


def test_swiping_up_and_down_scrolls_and_never_turns_the_page(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/jobs")

    swipe(cdp, 200, 560, 190, 200, steps=10)
    page.wait_for_timeout(600)
    assert current(page) == "work"
    assert page.locator(".nb-in").evaluate("n => n.scrollTop") > 100


def test_a_slanted_stroke_is_not_a_swipe(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/jobs")

    swipe(cdp, 300, 300, 180, 480)  # more down than sideways would allow
    page.wait_for_timeout(700)
    assert current(page) == "work"
    swipe(cdp, 300, 300, 230, 420)  # short and steep
    page.wait_for_timeout(700)
    assert current(page) == "work"


def test_a_short_sideways_nudge_is_not_a_swipe(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/jobs")

    swipe(cdp, 250, 400, 220, 400)
    page.wait_for_timeout(600)
    assert current(page) == "work"


def test_a_swipe_on_a_picture_row_moves_the_row_and_not_the_page(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/projects/websites/this_website/v1")

    row = page.locator(".nb-in .slides").first.bounding_box()
    y = row["y"] + 60
    swipe(cdp, row["x"] + 260, y, row["x"] + 40, y)
    page.wait_for_timeout(900)
    assert current(page) == "site"
    assert page.locator(".nb-in .slides").first.evaluate("n => n.scrollLeft") > 50


def test_a_swipe_on_the_cover_still_opens_it(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/")

    front = page.locator(".cover-front").bounding_box()
    swipe(cdp, front["x"] + front["width"] - 12, front["y"] + front["height"] * 0.56, front["x"] + 50, front["y"] + front["height"] * 0.56)
    page.wait_for_timeout(1200)
    assert "is-closed" not in page.locator("#notebook").get_attribute("class")


def test_a_tap_does_not_flash_a_highlight_and_the_keyboard_ring_remains(mobile_browser_page) -> None:
    page, _ = open_with_touch(mobile_browser_page, "/jobs")

    for selector in ("body", ".nb-in", ".nb-ear.next", ".nb-tab", ".wheel-dial"):
        color = page.locator(selector).first.evaluate("n => getComputedStyle(n).webkitTapHighlightColor")
        assert color in ("rgba(0, 0, 0, 0)", "transparent"), (selector, color)
    page.locator(".nb-ear.next").focus()
    page.keyboard.press("Tab")
    page.keyboard.press("Shift+Tab")
    assert page.locator(".nb-ear.next").evaluate("n => getComputedStyle(n).outlineStyle") == "solid"


def test_two_fingers_spreading_sideways_is_not_a_swipe(mobile_browser_page) -> None:
    page, cdp = open_with_touch(mobile_browser_page, "/jobs")

    cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": 190, "y": 400, "id": 1}, {"x": 200, "y": 400, "id": 2}]})
    for i in range(1, 9):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": 190 - 12 * i, "y": 400, "id": 1}, {"x": 200 + 12 * i, "y": 400, "id": 2}]})
    cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
    page.wait_for_timeout(800)

    assert current(page) == "work"
    swipe(cdp, 300, 400, 120, 410)  # and a one-finger swipe still works afterwards
    page.wait_for_timeout(900)
    assert current(page) == "school"
