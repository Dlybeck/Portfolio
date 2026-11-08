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


SMALLEST_TEXT = """() => {
  let min = 99, who = '';
  const walker = document.createTreeWalker(document.getElementById('notebook'), NodeFilter.SHOW_TEXT);
  while (walker.nextNode()) {
    const node = walker.currentNode, el = node.parentElement;
    if (!node.textContent.trim() || el.closest('.cover-front, .cover-inside, .sr-only, [hidden], script, style')) continue;
    const box = el.getBoundingClientRect();
    if (!box.width || !box.height || getComputedStyle(el).visibility === 'hidden') continue;
    const size = parseFloat(getComputedStyle(el).fontSize);
    if (size < min) { min = size; who = el.tagName + '.' + String(el.className).slice(0, 30) + ': ' + node.textContent.trim().slice(0, 20); }
  }
  return [min, who];
}"""


@pytest.mark.parametrize("width,height", VIEWPORTS)
def test_no_text_on_a_page_is_smaller_than_12px(browser_page, width, height) -> None:
    page, base = browser_page
    page.set_viewport_size({"width": width, "height": height})
    for route in ROUTES + ["/projects/nba_predictions", "/hobbies/gaming"]:
        page.goto(base + route)
        page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
        page.wait_for_timeout(250)
        smallest, who = page.evaluate(SMALLEST_TEXT)
        assert smallest >= 12, (route, smallest, who)  # the stickers on the cover and inside it are art, not text, and are left out


def test_a_portrait_tablet_reads_at_18px_while_phones_and_desktops_keep_16px(browser_page) -> None:
    page, base = browser_page
    sizes = {}
    for width, height in [(820, 1180), (768, 1024), (390, 844), (1180, 820), (1440, 900)]:
        page.set_viewport_size({"width": width, "height": height})
        page.goto(base + "/jobs")
        page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
        sizes[(width, height)] = page.evaluate("parseFloat(getComputedStyle(document.documentElement).fontSize)")
    assert sizes == {(820, 1180): 18, (768, 1024): 18, (390, 844): 16, (1180, 820): 16, (1440, 900): 16}
