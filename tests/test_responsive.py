"""The notebook fits every window: no sideways page scroll, the tabs stay on screen, and the pages' words keep a readable width."""

from __future__ import annotations

import pytest

VIEWPORTS = [(1920, 1080), (1440, 900), (1280, 800), (1024, 768), (820, 1180), (1180, 820), (390, 844), (360, 740)]
ROUTES = ["/", "/#contents", "/jobs", "/education/college", "/hobbies/3d_printing/puzzles", "/#say-hi"]


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_no_sideways_scroll_and_the_tabs_stay_on_screen(browser_page, width, height) -> None:
    page, base = browser_page
    page.set_viewport_size({"width": width, "height": height})
    for route in ROUTES:
        page.goto(base + route)
        page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
        page.wait_for_timeout(250)
        overflow = page.evaluate("document.documentElement.scrollWidth - innerWidth")
        assert overflow <= 0, (route, overflow)
        tabs = page.locator(".nb-tabs").bounding_box()
        assert tabs["x"] + tabs["width"] <= width + 1, (route, tabs)


@pytest.mark.parametrize("width,height", [(1024, 768), (1180, 820)])
def test_the_school_clubs_keep_a_readable_text_column_on_a_small_desktop_window(browser_page, width, height) -> None:
    page, base = browser_page
    page.set_viewport_size({"width": width, "height": height})
    page.goto(base + "/education/college")
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(300)
    widths = page.evaluate("[...document.querySelectorAll('.nb-page.r .club > :not(figure)')].map((n) => n.getBoundingClientRect().width)")
    assert widths and min(widths) >= 160, widths  # was a 60px sliver beside the logo
