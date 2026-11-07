"""Slim section tabs on a phone."""

from __future__ import annotations

import pytest

SIZES = [{"width": 360, "height": 740}, {"width": 390, "height": 844}, {"width": 430, "height": 932}, {"width": 320, "height": 568}]
IDS = lambda v: f"{v['width']}x{v['height']}"  # noqa: E731


def visit(browser_page, route, viewport):
    page, base = browser_page
    page.set_viewport_size(viewport)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone")
    page.wait_for_timeout(900)
    return page


@pytest.mark.parametrize("viewport", SIZES, ids=IDS)
def test_phone_tabs_are_tappable_inside_the_screen_and_do_not_narrow_the_page(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)

    boxes = [page.locator(".nb-tab").nth(i).bounding_box() for i in range(6)]
    assert len(boxes) == 6
    for box in boxes:
        assert box["width"] >= 26 and box["height"] >= 24, box  # WCAG 2.5.8 minimum target
        assert box["x"] + box["width"] <= viewport["width"] - 2  # at least 2px clear of the screen edge
        assert box["width"] - 10 >= 16  # the coloured part is at least 16px wide (the other 10px is invisible touch area)
    # the page keeps the width it had without tabs: the room came from the margin
    # (the layout rule is unchanged: a width of the screen less 34px, or less if the height cannot hold it)
    expected = min(viewport["width"] - 34, (viewport["height"] - 70 - 138) * 0.625)
    assert page.locator(".nb-page").bounding_box()["width"] == pytest.approx(expected, abs=1.5)
    assert not page.evaluate("document.documentElement.scrollWidth > innerWidth")
    assert page.locator(".nb-tab").evaluate_all("els => els.filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).length") == 0


def test_a_tap_on_a_phone_tab_goes_to_that_section_and_marks_it(browser_page) -> None:
    page = visit(browser_page, "/jobs", SIZES[0])

    page.locator(".nb-tab", has_text="Hobbies").click()
    page.wait_for_timeout(1200)
    assert page.locator("#notebook").get_attribute("data-page") == "hobbies"
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"


def test_shut_phone_tabs_peek_6px_past_the_cover_with_no_readable_words(browser_page) -> None:
    page = visit(browser_page, "/", SIZES[1])

    cover = page.locator(".nb-leaf.cover").bounding_box()
    edge = cover["x"] + cover["width"]
    for i in range(6):
        box = page.locator(".nb-tab").nth(i).bounding_box()
        assert box["x"] + box["width"] - edge == pytest.approx(6, abs=1.5)
    assert page.locator(".nb-tab").first.evaluate("n => getComputedStyle(n).color") == "rgba(0, 0, 0, 0)"
    assert page.locator(".nb-tabs").get_attribute("aria-hidden") == "true"


def test_a_swipe_that_starts_on_a_tab_does_not_turn_the_page_but_one_on_the_page_does(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(SIZES[1])
    page.goto(base + "/jobs")
    page.wait_for_selector("#notebook.nb--phone")
    page.wait_for_timeout(900)
    cdp = page.context.new_cdp_session(page)

    def swipe(x1, y, x2):
        cdp.send("Input.dispatchTouchEvent", {"type": "touchStart", "touchPoints": [{"x": x1, "y": y}]})
        for i in range(1, 7):
            cdp.send("Input.dispatchTouchEvent", {"type": "touchMove", "touchPoints": [{"x": x1 + (x2 - x1) * i / 6, "y": y}]})
            page.wait_for_timeout(15)
        cdp.send("Input.dispatchTouchEvent", {"type": "touchEnd", "touchPoints": []})
        page.wait_for_timeout(1000)

    tab = page.locator(".nb-tab").nth(1).bounding_box()
    swipe(tab["x"] + tab["width"] - 3, tab["y"] + 30, tab["x"] - 150)
    assert page.locator("#notebook").get_attribute("data-page") == "work"
    swipe(330, 400, 40)
    assert page.locator("#notebook").get_attribute("data-page") == "school"
