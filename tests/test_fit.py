"""Nothing is cut off at the page edge on a small portrait phone, and the desktop tab column stays inside the window."""

from __future__ import annotations

import pytest

ROUTES = ["/jobs", "/education/college", "/education/early_education", "/hobbies/tennis", "/projects/programs", "/projects/websites/scribblescan", "/#say-hi"]


def open_page(browser_page, route, viewport):
    page, base = browser_page
    page.set_viewport_size(viewport)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(500)
    return page


def overflow(page) -> list:
    return page.evaluate("() => [...document.querySelectorAll('.nb-in')].filter(e => e.scrollWidth > e.clientWidth + 1).map(e => e.scrollWidth - e.clientWidth)")


@pytest.mark.parametrize("route", ROUTES)
def test_no_page_is_cut_off_at_the_edge_on_the_smallest_phone(browser_page, route) -> None:
    page = open_page(browser_page, route, {"width": 320, "height": 568})

    assert overflow(page) == []


@pytest.mark.parametrize("size", [{"width": 900, "height": 700}, {"width": 900, "height": 600}, {"width": 960, "height": 700}])
def test_the_say_hi_rows_and_every_tab_stay_inside_a_window_just_wide_enough_for_the_spread(browser_page, size) -> None:
    page = open_page(browser_page, "/#say-hi", size)

    assert overflow(page) == []
    box = page.locator(".nb-tabs").bounding_box()
    assert box["y"] + box["height"] <= size["height"]
    assert page.locator(".nb-tab").evaluate_all(
        "els => els.filter(e => e.scrollWidth > e.clientWidth + 1 || e.scrollHeight > e.clientHeight + 1).map(e => e.textContent)"
    ) == []


def test_figure_captions_have_enough_contrast(browser_page) -> None:
    page = open_page(browser_page, "/education/early_education", {"width": 1280, "height": 800})

    ratio = page.evaluate("""() => {
      const c = document.querySelector('.page figcaption'), s = getComputedStyle(c);
      const parse = (v) => v.match(/[\\d.]+/g).map(Number);
      const lum = ([r, g, b]) => [r, g, b].map(x => { x /= 255; return x <= 0.03928 ? x / 12.92 : ((x + 0.055) / 1.055) ** 2.4; }).reduce((a, x, i) => a + x * [0.2126, 0.7152, 0.0722][i], 0);
      const fg = parse(s.color), alpha = fg.length > 3 ? fg[3] : 1, bg = [255, 255, 255];  // the page is white paper under the caption
      const mixed = fg.slice(0, 3).map((x, i) => x * alpha + bg[i] * (1 - alpha));
      const [a, b] = [lum(mixed), lum(bg)];
      return (Math.max(a, b) + 0.05) / (Math.min(a, b) + 0.05);
    }""")
    assert ratio >= 4.5, ratio
