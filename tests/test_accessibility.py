"""Keyboard, reduced motion and screen readers."""

from __future__ import annotations

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}


def open_notebook(browser_page, route="/jobs", viewport=PHONE, reduced=False):
    page, base = browser_page
    if reduced:
        page.emulate_media(reduced_motion="reduce")
    page.set_viewport_size(viewport)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(300)
    return page


def test_the_page_has_landmarks_and_one_h1(browser_page) -> None:
    page = open_notebook(browser_page)

    assert page.locator("h1").count() == 1
    assert page.locator('header h1').count() == 1
    assert page.locator('[role="main"]').count() == 1
    assert page.locator('nav[aria-label="Page wheel"]').count() == 1
    assert page.locator("#nb-status").get_attribute("role") == "status"


def test_sticker_labels_start_with_the_words_you_can_see(browser_page) -> None:
    # speech-input users say what they see (WCAG 2.5.3, label in name)
    page = open_notebook(browser_page, "/")

    pairs = page.locator(".cover-front > .wd[role=button]").evaluate_all(
        """els => els.map(e => [(e.getAttribute('aria-label') || '').toLowerCase(),
             (e.innerText || '').replace(/\\s+/g, ' ').trim().toLowerCase()])"""
    )
    checked = 0
    for label, seen in pairs:
        if seen:
            checked += 1
            assert label.startswith(seen), (label, seen)
    assert checked >= 3  # the name tag, the now pill and your sticker


def test_the_wheel_is_one_slider_with_no_controls_inside_it(browser_page) -> None:
    page = open_notebook(browser_page)

    dial = page.locator(".wheel-dial")
    assert dial.get_attribute("role") == "slider"
    assert dial.locator("button, a, input").count() == 0
    assert int(dial.get_attribute("aria-valuenow")) >= 1
    assert "page" in dial.get_attribute("aria-valuetext")


def test_pages_are_named_regions_a_keyboard_can_scroll(browser_page) -> None:
    page = open_notebook(browser_page, "/jobs", DESKTOP)

    names = page.locator('.nb-in[role="region"]').evaluate_all("els => els.map(e => e.getAttribute('aria-label'))")
    assert names == ["Work, left page", "Work, right page"]
    assert page.locator(".nb-in").first.get_attribute("tabindex") == "0"


def test_swipe_rows_can_be_focused_and_scrolled_by_keyboard(browser_page) -> None:
    page = open_notebook(browser_page, "/projects/websites/this_website/v1")

    row = page.locator(".nb-in .slides").first
    assert row.get_attribute("tabindex") == "0"
    row.focus()
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(500)
    assert row.evaluate("n => n.scrollLeft") > 0


def test_the_whole_book_can_be_driven_by_tab_and_enter(browser_page) -> None:
    page = open_notebook(browser_page, "/projects/websites/scribblescan", DESKTOP)

    page.locator('.nb-page.l a[data-open="nba"]').focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "nba"
    page.locator(".nb-ear.next").focus()
    page.keyboard.press("Enter")
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "planner"
    # the page that turned is announced to screen readers
    assert "Digital Planner" in page.locator("#nb-status").inner_text()


def test_with_reduced_motion_a_page_turn_has_no_flying_leaf(browser_page) -> None:
    page = open_notebook(browser_page, "/jobs", PHONE, reduced=True)

    page.locator(".nb-ear.next").click()
    assert page.locator("#notebook").get_attribute("data-page") == "school"  # at once, no wait
    assert page.locator(".nb-leaf.is-flying").count() == 0


def test_with_reduced_motion_the_cover_opens_without_a_swing(browser_page) -> None:
    page = open_notebook(browser_page, "/", PHONE, reduced=True)

    page.locator(".cover-open").click()
    assert page.locator(".nb-leaf.cover").count() == 0
    assert "is-closed" not in page.locator("#notebook").get_attribute("class")


def test_text_on_the_wheel_keeps_enough_contrast(browser_page) -> None:
    page = open_notebook(browser_page)

    def luminance(rgb):
        c = [v / 255 for v in rgb]
        c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
        return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]

    # the page number: white on a darker chip over the brand blue
    chip = page.locator(".wheel-name small")
    assert chip.inner_text().startswith("p.")
    assert chip.evaluate("n => getComputedStyle(n).backgroundColor") == "rgba(0, 28, 77, 0.55)"
    blue, dark, white = (0, 123, 255), (0, 28, 77), (255, 255, 255)
    blend = tuple(round(0.55 * d + 0.45 * b) for d, b in zip(dark, blue))
    ratio = (luminance(white) + 0.05) / (luminance(blend) + 0.05)
    assert ratio >= 4.5, ratio
