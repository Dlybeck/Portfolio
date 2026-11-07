"""Section tabs down the right edge of the two-page spread (desktop layout only)."""

from __future__ import annotations

import pytest

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}
SECTIONS = ["About", "Projects", "Work", "School", "Hobbies", "Say hi"]
SIZES = [{"width": 1024, "height": 700}, DESKTOP, {"width": 1920, "height": 1080}, {"width": 1100, "height": 1000}, {"width": 844, "height": 390}]


def visit(browser_page, route, viewport):
    page, base = browser_page
    page.set_viewport_size(viewport)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(300)
    return page


def label_clipping(page) -> list:
    return page.locator(".nb-tab").evaluate_all(
        "els => els.filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.textContent)"
    )


def test_every_main_section_has_a_tab_on_the_spread(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)

    assert page.locator(".nb-tabs .nb-tab").all_inner_texts() == SECTIONS
    assert page.locator('nav[aria-label="Sections"]').count() == 1
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Work"


@pytest.mark.parametrize("viewport", [PHONE, {"width": 320, "height": 568}, {"width": 768, "height": 1024}], ids=lambda v: str(v["width"]))
def test_a_phone_or_narrow_window_has_no_tabs(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)

    assert "nb--phone" in page.locator("#notebook").get_attribute("class")
    assert page.locator(".nb-tabs, .nb-tab").count() == 0


@pytest.mark.parametrize("viewport", SIZES, ids=lambda v: f"{v['width']}x{v['height']}")
def test_tabs_stay_inside_the_window_beside_the_book_and_the_book_does_not_move(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)

    book, tabs = page.locator(".nb-book").bounding_box(), page.locator(".nb-tabs").bounding_box()
    assert tabs["x"] >= book["x"] + book["width"] - 1
    assert tabs["x"] + tabs["width"] <= viewport["width"]
    assert tabs["y"] >= 60 and tabs["y"] + tabs["height"] <= viewport["height"]
    # the open section's tab slides out: it must still be on screen
    current = page.locator('.nb-tab[aria-current="page"]').bounding_box()
    assert current["x"] + current["width"] <= viewport["width"]
    assert label_clipping(page) == []
    # the book sits where it always did: centred between the wheel column (300px) and 40px from the right edge
    left, right = book["x"] - 300, (viewport["width"] - 40) - (book["x"] + book["width"])
    assert abs(left - right) <= 2, (left, right)
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")


def test_a_tab_jumps_to_its_section_the_current_one_follows_and_back_works(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)

    page.locator(".nb-tab", has_text="Hobbies").click()
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "printing"  # a spread has no index page
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"
    page.locator(".nb-tab", has_text="Say hi").click()
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "say"
    assert page.evaluate("location.hash") == "#say-hi"
    page.go_back()
    page.wait_for_timeout(900)
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"


def test_the_current_tab_follows_the_wheel_and_the_corners(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)

    page.locator(".nb-ear.next").click()
    page.wait_for_timeout(900)
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "School"
    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(1500)
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"


def test_tabs_work_from_the_keyboard_and_open_in_a_new_tab(browser_page) -> None:
    page = visit(browser_page, "/projects/programs", DESKTOP)

    assert page.locator(".nb-tab", has_text="School").get_attribute("href") == "/education/college"
    page.locator(".nb-tab", has_text="Work").focus()
    assert page.locator(".nb-tab", has_text="Work").evaluate("n => getComputedStyle(n).outlineStyle") == "solid"
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "work"


def test_tabs_are_hidden_while_the_cover_is_shut_and_appear_when_it_opens(browser_page) -> None:
    page = visit(browser_page, "/", DESKTOP)

    assert not page.locator(".nb-tabs").is_visible()
    page.locator(".cover-open").click()
    page.wait_for_timeout(1100)
    assert page.locator(".nb-tabs").is_visible()


def test_tabs_come_and_go_when_the_window_changes_between_phone_and_desktop(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)
    assert page.locator(".nb-tab").count() == 6
    page.set_viewport_size(PHONE)
    page.wait_for_selector("#notebook.nb--phone")
    assert page.locator(".nb-tab").count() == 0
    page.set_viewport_size(DESKTOP)
    page.wait_for_selector("#notebook.nb--desktop")
    assert page.locator(".nb-tab").count() == 6
