"""Section tabs on the edge of the notebook, in two trial placements (?tabs=a and ?tabs=b)."""

from __future__ import annotations

import pytest

PHONE = {"width": 390, "height": 844}
SMALL_PHONE = {"width": 320, "height": 568}
DESKTOP = {"width": 1280, "height": 800}
SECTIONS = ["About", "Projects", "Work", "School", "Hobbies", "Say hi"]


def visit(browser_page, route, viewport, tabs=None):
    page, base = browser_page
    page.set_viewport_size(viewport)
    suffix = f"?tabs={tabs}" if tabs else ""
    page.goto(base + route + suffix)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(300)
    return page


def classes(page) -> str:
    return page.locator("#notebook").get_attribute("class")


def test_a_is_the_default_and_unknown_values_fall_back_to_it(browser_page) -> None:
    assert "nb--tabs-a" in classes(visit(browser_page, "/jobs", PHONE))
    assert "nb--tabs-b" in classes(visit(browser_page, "/jobs", PHONE, "b"))
    assert "nb--tabs-a" in classes(visit(browser_page, "/jobs", PHONE, "z"))


@pytest.mark.parametrize("tabs", ["a", "b"])
@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_every_main_section_has_a_tab(browser_page, viewport, tabs) -> None:
    page = visit(browser_page, "/jobs", viewport, tabs)

    assert page.locator(".nb-tabs .nb-tab").all_inner_texts() == SECTIONS
    assert page.locator('nav[aria-label="Sections"]').count() == 1
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Work"


@pytest.mark.parametrize("tabs", ["a", "b"])
@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_a_tab_jumps_to_its_section_and_keeps_the_choice_in_the_address(browser_page, viewport, tabs) -> None:
    page = visit(browser_page, "/jobs", viewport, tabs)

    page.locator(".nb-tab", has_text="Hobbies").click()
    page.wait_for_timeout(900)
    expected = "hobbies" if viewport is PHONE else "printing"  # a desktop spread has no index page
    assert page.locator("#notebook").get_attribute("data-page") == expected
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"
    assert f"tabs={tabs}" in page.evaluate("location.search")

    page.locator(".nb-tab", has_text="Say hi").click()
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "say"
    assert page.evaluate("location.hash") == "#say-hi"
    page.go_back()
    page.wait_for_timeout(900)
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"


def test_the_current_tab_follows_the_wheel_and_the_corners(browser_page) -> None:
    page = visit(browser_page, "/jobs", PHONE)

    page.locator(".nb-ear.next").click()
    page.wait_for_timeout(900)
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "School"
    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(1500)
    assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"


def test_tabs_work_from_the_keyboard(browser_page) -> None:
    page = visit(browser_page, "/projects/programs", DESKTOP)

    page.locator(".nb-tab", has_text="Work").focus()
    assert page.locator(".nb-tab", has_text="Work").evaluate("n => getComputedStyle(n).outlineStyle") == "solid"
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "work"


def test_tabs_are_hidden_while_the_cover_is_shut_and_appear_when_it_opens(browser_page) -> None:
    page = visit(browser_page, "/", PHONE)

    assert not page.locator(".nb-tabs").is_visible()
    page.locator(".cover-open").click()
    page.wait_for_timeout(1100)
    assert page.locator(".nb-tabs").is_visible()


ROOMY = [PHONE, {"width": 414, "height": 896}]
NARROW = [SMALL_PHONE, {"width": 360, "height": 640}, {"width": 375, "height": 667}]


def every_label_fits(page) -> list:
    return page.locator(".nb-tab").evaluate_all(
        "els => els.filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.textContent)"
    )


@pytest.mark.parametrize("viewport", ROOMY, ids=lambda v: str(v["width"]))
def test_placement_a_on_a_phone_sits_on_the_top_edge_below_the_header(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport, "a")

    book, tabs = page.locator(".nb-book").bounding_box(), page.locator(".nb-tabs").bounding_box()
    header = page.locator(".nb-top").bounding_box()
    assert tabs["y"] + tabs["height"] <= book["y"] + 3
    assert tabs["y"] >= header["y"] + header["height"] - 2
    assert tabs["x"] >= 0 and tabs["x"] + tabs["width"] <= viewport["width"]
    widths = page.locator(".nb-tab").evaluate_all("els => els.map(e => e.getBoundingClientRect().width)")
    assert min(widths) >= 28  # wide enough to tap (24px is the minimum a finger needs)
    assert every_label_fits(page) == []  # no word is cut off
    assert "nb--tabs-a" in classes(page)


@pytest.mark.parametrize("viewport", NARROW, ids=lambda v: str(v["width"]))
def test_placement_a_on_a_narrow_phone_moves_to_the_right_edge_so_words_fit(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport, "a")

    assert "nb--tabs-b" in classes(page)
    assert every_label_fits(page) == []
    book, tabs = page.locator(".nb-book").bounding_box(), page.locator(".nb-tabs").bounding_box()
    assert tabs["x"] >= book["x"] + book["width"] - 1 and tabs["x"] + tabs["width"] <= viewport["width"]


@pytest.mark.parametrize("viewport", [PHONE, SMALL_PHONE, {"width": 360, "height": 640}], ids=lambda v: str(v["width"]))
def test_placement_b_on_a_phone_sits_on_the_right_edge_inside_the_screen(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport, "b")

    book, tabs = page.locator(".nb-book").bounding_box(), page.locator(".nb-tabs").bounding_box()
    assert tabs["x"] >= book["x"] + book["width"] - 1
    assert tabs["x"] + tabs["width"] <= viewport["width"]
    assert tabs["y"] >= book["y"] and tabs["y"] + tabs["height"] <= book["y"] + book["height"] + 2
    assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
    heights = page.locator(".nb-tab").evaluate_all("els => els.map(e => e.getBoundingClientRect().height)")
    assert min(heights) >= 36
    assert every_label_fits(page) == []


@pytest.mark.parametrize("tabs", ["a", "b"])
@pytest.mark.parametrize("viewport", [DESKTOP, {"width": 1024, "height": 700}, {"width": 1920, "height": 1080}], ids=lambda v: str(v["width"]))
def test_on_desktop_tabs_sit_on_the_right_edge_inside_the_window(browser_page, viewport, tabs) -> None:
    page = visit(browser_page, "/jobs", viewport, tabs)

    book, box = page.locator(".nb-book").bounding_box(), page.locator(".nb-tabs").bounding_box()
    assert box["x"] >= book["x"] + book["width"] - 1
    assert box["x"] + box["width"] <= viewport["width"] - 8
    assert box["y"] + box["height"] <= viewport["height"]


def test_the_wheel_and_pages_still_fit_with_tabs_on(browser_page) -> None:
    page = visit(browser_page, "/jobs", PHONE, "a")

    book = page.locator(".nb-book").bounding_box()
    wheel = page.locator(".wheel").bounding_box()
    assert book["y"] + book["height"] <= wheel["y"] + 10  # the wheel starts below the book


@pytest.mark.parametrize("tabs", ["a", "b"])
@pytest.mark.parametrize("viewport", [{"width": 844, "height": 390}, {"width": 1000, "height": 520}, {"width": 700, "height": 420}], ids=lambda v: f"{v['width']}x{v['height']}")
def test_on_a_short_window_all_six_tabs_stay_on_screen_and_readable(browser_page, viewport, tabs) -> None:
    page = visit(browser_page, "/jobs", viewport, tabs)

    assert "nb--desktop" in classes(page)
    boxes = page.locator(".nb-tab").evaluate_all("els => els.map(e => { const r = e.getBoundingClientRect(); return [r.top, r.bottom, r.right]; })")
    assert len(boxes) == 6
    for top, bottom, right in boxes:
        assert top >= 0 and bottom <= viewport["height"], boxes
        assert right <= viewport["width"]
    assert every_label_fits(page) == []
    assert min(b - t for t, b, _ in boxes) >= 28


def test_tab_links_carry_the_placement_so_a_new_tab_keeps_it(browser_page) -> None:
    page = visit(browser_page, "/jobs", PHONE, "b")

    hrefs = page.locator(".nb-tab").evaluate_all("els => els.map(e => e.getAttribute('href'))")
    assert hrefs == ["/?tabs=b#about", "/?tabs=b#projects", "/jobs?tabs=b", "/education/college?tabs=b", "/?tabs=b#hobbies", "/?tabs=b#say-hi"]
