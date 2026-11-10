"""Section tabs down the right edge of the two-page spread (desktop layout only)."""

from __future__ import annotations

import pytest

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}
SECTIONS = ["Contents", "Projects", "Work", "School", "Hobbies", "Say hi"]
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


@pytest.mark.parametrize("viewport", SIZES, ids=lambda v: f"{v['width']}x{v['height']}")
def test_tabs_stay_inside_the_window_beside_the_book_and_the_book_does_not_move(browser_page, viewport) -> None:
    page = visit(browser_page, "/jobs", viewport)

    book, tabs = page.locator(".nb-book").bounding_box(), page.locator(".nb-tabs").bounding_box()
    assert tabs["x"] >= book["x"] + book["width"] - 1
    assert tabs["x"] + tabs["width"] <= viewport["width"]
    top_bar = 0 if viewport["height"] <= 520 else 60  # on a phone on its side the bar is only the small logo at the left
    assert tabs["y"] >= top_bar and tabs["y"] + tabs["height"] <= viewport["height"]
    # the open section's tab slides out: it must still be on screen
    current = page.locator('.nb-tab[aria-current="page"]').bounding_box()
    assert current["x"] + current["width"] <= viewport["width"]
    assert label_clipping(page) == []
    # the book sits where it always did: centred between the wheel column (300px, or 150px on a phone on its side) and 40px from the right edge
    column = 150 if viewport["height"] <= 520 else 300
    left, right = book["x"] - column, (viewport["width"] - 40) - (book["x"] + book["width"])
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

    page.locator(".nb-ear.next").click(position={"x": 44, "y": 44})  # on the drawn fold
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


PEEK = """() => [...document.querySelectorAll('.nb-tab')].map(t => { const r = t.getBoundingClientRect(); return [r.left, r.right]; })"""


def cover_edge(page) -> float:
    box = page.locator(".nb-leaf.cover").bounding_box()
    return box["x"] + box["width"]


@pytest.mark.parametrize("viewport", [{"width": 1024, "height": 700}, DESKTOP, {"width": 1920, "height": 1080}, {"width": 640, "height": 360}])
def test_while_the_cover_is_shut_the_tabs_peek_out_about_6px_and_show_no_words(browser_page, viewport) -> None:
    page = visit(browser_page, "/", viewport)

    edge = cover_edge(page)
    spans = page.evaluate(PEEK)
    assert len(spans) == 6 and page.locator(".nb-tabs").is_visible()
    for left, right in spans:
        assert abs((right - edge) - 6) < 1.5, (right - edge)  # an edge of colour, about 6px past the cover
        assert right <= viewport["width"]  # and it is not clipped by the window
    # the words sit under the cover, so none can be read
    assert all(t["x"] + t["width"] / 2 < edge - 4 for t in [page.locator(".nb-tab").nth(i).bounding_box() for i in range(6)])


def test_the_shut_tabs_are_hidden_from_keyboards_and_screen_readers_but_a_mouse_can_use_them(browser_page) -> None:
    page = visit(browser_page, "/", DESKTOP)

    assert page.locator(".nb-tabs").get_attribute("aria-hidden") == "true"
    assert page.locator(".nb-tab").evaluate_all("els => els.every(e => e.tabIndex === -1)")
    page.locator(".nb-tab").nth(2).click(position={"x": 22, "y": 40})  # the 6px edge
    page.wait_for_timeout(1100)
    assert page.locator("#notebook").get_attribute("data-page") == "work"
    assert page.locator(".nb-tabs").get_attribute("aria-hidden") is None
    assert page.locator(".nb-tab").evaluate_all("els => els.every(e => e.tabIndex === 0)")


def test_the_tabs_ride_with_the_book_and_slide_out_in_step_with_the_cover_swing(browser_page) -> None:
    page = visit(browser_page, "/", DESKTOP)
    # `tab` below is the far (right) edge: the current tab grows out rather than sliding, so only that edge travels.
    page.evaluate("""() => {
      window.__s = [];
      const t0 = performance.now();
      const tick = () => {
        const tab = document.querySelector('.nb-tab'), book = document.querySelector('.nb-book');
        window.__s.push({ t: performance.now() - t0, tab: tab.getBoundingClientRect().right, book: book.getBoundingClientRect().left,
                          opacity: getComputedStyle(document.querySelector('.nb-tabs')).opacity, shown: getComputedStyle(document.querySelector('.nb-tabs')).display });
        if (performance.now() - t0 < 1400) requestAnimationFrame(tick);
      };
      tick();
    }""")
    page.locator(".cover-open").click(no_wait_after=True)
    page.wait_for_timeout(1500)
    s = page.evaluate("window.__s")

    rel = [x["tab"] - x["book"] for x in s]
    assert all(x["opacity"] == "1" and x["shown"] != "none" for x in s)  # no fade-in and no pop
    steps = [b - a for a, b in zip(rel, rel[1:])]
    assert max(steps) < 24  # a slide, not a jump (a stalled frame on a slow machine can double a step)
    assert rel[-1] - rel[0] > 18  # it travels about 22px to its full place
    assert all(b >= a - 0.01 for a, b in zip(rel, rel[1:]))  # monotonic out


def test_closing_tucks_the_tabs_back_to_the_peek(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)
    page.evaluate("document.querySelector('[data-home]').click()")
    page.wait_for_timeout(1100)

    spans = page.evaluate(PEEK)
    assert all(abs(right - cover_edge(page) - 6) < 1.5 for _, right in spans)
    assert page.locator(".nb-tabs").get_attribute("aria-hidden") == "true"


def test_with_reduced_motion_the_tabs_do_not_slide(browser_page) -> None:
    page, base = browser_page
    page.emulate_media(reduced_motion="reduce")
    page.set_viewport_size(DESKTOP)
    page.goto(base + "/")
    page.wait_for_selector("#notebook.nb--desktop")
    page.wait_for_timeout(300)
    assert page.locator(".nb-tab").first.evaluate("n => getComputedStyle(n).transitionDuration") in ("0s", "0.0s")
    page.locator(".cover-open").click()
    page.wait_for_timeout(500)
    assert page.locator(".nb-tabs").get_attribute("aria-hidden") is None


def test_tabs_come_and_go_when_the_window_changes_between_phone_and_desktop(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)
    assert page.locator(".nb-tab").count() == 6
    page.set_viewport_size(PHONE)
    page.wait_for_selector("#notebook.nb--phone")
    assert page.locator(".nb-tab").count() == 6  # a phone has slim tabs too
    page.set_viewport_size(DESKTOP)
    page.wait_for_selector("#notebook.nb--desktop")
    assert page.locator(".nb-tab").count() == 6


def test_the_shut_peek_starts_at_the_board_top_in_a_tall_window(browser_page) -> None:
    page = visit(browser_page, "/", {"width": 1920, "height": 1200})

    board = page.locator(".nb-back").bounding_box()
    assert page.locator(".nb-tabs").bounding_box()["y"] >= board["y"] - 0.5  # no tab hangs above the book


def test_turning_pages_while_open_moves_the_current_tab_quickly_not_at_the_opening_speed(browser_page) -> None:
    page = visit(browser_page, "/jobs", DESKTOP)
    page.wait_for_timeout(1000)  # past the opening

    duration = page.locator(".nb-tab").first.evaluate("n => getComputedStyle(n).transitionDuration").split(",")[0]
    assert float(duration.strip("s ")) < 0.4, duration


def test_after_a_shut_tab_is_clicked_focus_lands_on_the_new_page(browser_page) -> None:
    page = visit(browser_page, "/", DESKTOP)

    page.locator(".nb-tab").nth(2).click(position={"x": 22, "y": 40})
    page.wait_for_timeout(1100)
    assert page.evaluate("document.activeElement.closest('.nb-page')?.classList.contains('r')")
