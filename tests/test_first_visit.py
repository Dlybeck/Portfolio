"""A first visit to "/" opens the notebook on its last page, spins the wheel back to the cover and points at the wheel.

It plays once per visitor, never for a deep link, not at all with reduced motion, and any touch, wheel or key takes over.
It writes nothing to the browser's history. (Every other test runs as a returning visitor: see `new_page` in conftest.py.)"""

from __future__ import annotations

import pytest

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1440, "height": 900}
VIEWPORTS = [pytest.param(PHONE, id="phone"), pytest.param(DESKTOP, id="desktop")]

# counts every write to the history, from the first script on the page
COUNT_HISTORY = """(() => {
  window.__writes = 0;
  for (const name of ['pushState', 'replaceState']) {
    const original = history[name];
    history[name] = function (...args) { window.__writes += 1; return original.apply(this, args); };
  }
})()"""
SEEN = "localStorage.getItem('nb-opening-seen')"
STATE = """() => {
  const root = document.getElementById('notebook');
  return { shut: root.classList.contains('is-closed'), page: root.dataset.page, path: location.pathname,
           tip: document.querySelector('.wheel-tip')?.textContent ?? null, writes: window.__writes };
}"""


def visit(new_page, base, viewport, route="/", **options):
    """A fresh visitor (nothing remembered) opening `route`."""
    touch = viewport["width"] < 600
    page = new_page(first_visit=True, viewport=viewport, is_mobile=touch, has_touch=touch, **options)
    page.add_init_script(COUNT_HISTORY)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    return page


def state(page) -> dict:
    return page.evaluate(STATE)


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_a_first_visit_opens_on_the_last_page_spins_back_and_ends_on_the_cover_with_a_tip(new_page, live_server_url, viewport) -> None:
    page = visit(new_page, live_server_url, viewport)
    page.wait_for_timeout(500)
    start = state(page)
    assert not start["shut"] and start["page"] == "say"  # the last page, with the book open
    assert page.evaluate(SEEN) == "1"  # remembered from the start, so a reload mid-spin does not replay it

    page.wait_for_selector(".wheel-tip", timeout=9000)
    end = state(page)
    assert end["shut"] and end["path"] == "/" and end["tip"] == "spin the wheel to open"
    assert page.locator(".wheel-name b").inner_text() == "Cover"
    assert end["writes"] == 0  # the spin's flips add no history entries, and the address never changes


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_back_after_the_opening_follows_the_page_turns_not_the_spin(new_page, live_server_url, viewport) -> None:
    page = visit(new_page, live_server_url, viewport)
    page.wait_for_selector(".wheel-tip", timeout=9000)
    page.locator(".cover-open").click()
    page.wait_for_timeout(1500)
    opened = state(page)
    assert not opened["shut"]

    page.go_back()
    page.wait_for_timeout(1500)
    assert state(page)["shut"]  # back to the shut cover at "/", not into the middle of a spin
    assert state(page)["path"] == "/"


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_a_returning_visitor_gets_the_plain_cover(new_page, live_server_url, viewport) -> None:
    page = visit(new_page, live_server_url, viewport)
    page.wait_for_selector(".wheel-tip", timeout=9000)
    page.goto(live_server_url + "/")
    page.wait_for_selector("#notebook.is-closed")
    page.wait_for_timeout(1200)
    assert state(page)["shut"] and state(page)["tip"] is None
    page.goto(live_server_url + "/?intro=1")  # ?intro=1 plays it again
    page.wait_for_timeout(600)
    assert not state(page)["shut"]


def test_intro_zero_skips_it_and_does_not_remember(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP, "/?intro=0")
    page.wait_for_timeout(800)
    assert state(page)["shut"] and page.evaluate(SEEN) is None


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_a_deep_link_shows_its_page_with_no_opening_and_is_not_remembered(new_page, live_server_url, viewport) -> None:
    page = visit(new_page, live_server_url, viewport, "/jobs")
    page.wait_for_timeout(1500)
    shown = state(page)
    assert not shown["shut"] and shown["page"] == "work" and shown["tip"] is None
    assert page.evaluate(SEEN) is None


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_reduced_motion_shows_the_cover_with_a_still_tip_and_no_spin(new_page, live_server_url, viewport) -> None:
    page = visit(new_page, live_server_url, viewport, reduced_motion="reduce")
    page.wait_for_selector(".wheel-tip")
    shown = state(page)
    assert shown["shut"] and shown["tip"] == "spin the wheel to open" and shown["writes"] == 0
    assert page.evaluate("getComputedStyle(document.querySelector('.wheel-tip')).animationName") == "none"
    page.locator(".cover-open").click()
    page.wait_for_timeout(1500)
    assert page.evaluate("getComputedStyle(document.querySelector('.nb-ear.next'), '::before').animationName") == "none"  # the corner does not lift


TAKE_OVER = {
    "wheel": lambda page: (page.mouse.move(120, 424), page.mouse.wheel(0, 60)),
    "key": lambda page: page.keyboard.press("ArrowDown"),
    "click": lambda page: page.mouse.click(900, 300),
}


@pytest.mark.parametrize("how", TAKE_OVER)
def test_a_wheel_key_or_click_takes_over_at_once(new_page, live_server_url, how) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2300)  # mid-spin
    TAKE_OVER[how](page)
    page.wait_for_timeout(500)
    stopped_on = state(page)["page"]
    page.wait_for_timeout(4500)
    after = state(page)
    assert not after["shut"] and after["page"] == stopped_on and after["tip"] is None  # it stayed where the visitor stopped it
    assert after["path"] != "/"  # and the address follows that page
    assert after["writes"] <= 2  # at most the address of the page it stopped on, and the one turn it settled with


def test_a_touch_takes_over_on_a_phone(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, PHONE)
    page.wait_for_timeout(2300)
    page.touchscreen.tap(195, 300)
    page.wait_for_timeout(500)
    stopped_on = state(page)["page"]
    page.wait_for_timeout(4500)
    assert not state(page)["shut"] and state(page)["page"] == stopped_on


def test_it_still_plays_when_storage_is_blocked(new_page, live_server_url) -> None:
    touch = False
    page = new_page(first_visit=True, viewport=DESKTOP, is_mobile=touch)
    errors: list[str] = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.add_init_script("Object.defineProperty(window, 'localStorage', { get() { throw new Error('blocked'); } });")
    page.goto(live_server_url + "/")
    page.wait_for_selector(".wheel-tip", timeout=9000)
    assert state(page)["shut"] and errors == []


@pytest.mark.parametrize("viewport", VIEWPORTS)
def test_the_page_corner_is_a_little_larger_and_lifts_once_on_a_first_visit(new_page, live_server_url, viewport) -> None:
    page = visit(new_page, live_server_url, viewport)
    page.wait_for_selector(".wheel-tip", timeout=9000)
    page.locator(".cover-open").click()
    page.wait_for_function("document.getElementById('notebook').classList.contains('nb--lift')", timeout=4000)
    assert page.evaluate("getComputedStyle(document.querySelector('.nb-ear.next')).width") == "56px"
    page.wait_for_function("!document.getElementById('notebook').classList.contains('nb--lift')", timeout=4000)  # one lift, then still


def test_a_returning_visitors_corner_does_not_lift(new_page, live_server_url) -> None:
    page = new_page(viewport=DESKTOP)
    page.goto(live_server_url + "/")
    page.wait_for_selector("#notebook.is-closed")
    page.locator(".cover-open").click()
    page.wait_for_timeout(2500)
    assert not page.evaluate("document.getElementById('notebook').classList.contains('nb--lift')")


@pytest.mark.parametrize("viewport", [{"width": 600, "height": 400}, {"width": 700, "height": 400}], ids=["600x400", "700x400"])
def test_the_tip_is_whole_and_readable_in_a_short_landscape_window(new_page, live_server_url, viewport) -> None:
    # the wheel is drawn at about half size here; the tip inside it must still be on screen and full size
    page = visit(new_page, live_server_url, viewport, reduced_motion="reduce")
    page.wait_for_selector(".wheel-tip")
    page.wait_for_timeout(300)
    box = page.locator(".wheel-tip").bounding_box()
    assert box["x"] >= 0 and box["x"] + box["width"] <= viewport["width"] and box["y"] >= 0
    assert box["height"] >= 30 and box["width"] >= 150


def test_resizing_across_the_phone_breakpoint_mid_opening_still_ends_on_the_cover_with_the_tip(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)  # mid-spin
    page.set_viewport_size(PHONE)
    page.wait_for_selector(".wheel-tip", timeout=4000)
    shown = state(page)
    assert shown["shut"] and shown["path"] == "/"


def test_a_new_address_mid_opening_takes_over_and_the_page_matches_it(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)  # mid-spin
    page.evaluate("location.hash = '#hobbies'")
    page.wait_for_timeout(5000)
    shown = state(page)
    other = new_page(viewport=DESKTOP)  # what that address shows to anyone loading it
    other.goto(live_server_url + "/#hobbies")
    other.wait_for_selector("#notebook.nb--desktop")
    other.wait_for_timeout(1200)
    assert not shown["shut"] and shown["page"] == state(other)["page"] and shown["tip"] is None
    assert page.evaluate("location.pathname + location.hash") == other.evaluate("location.pathname + location.hash")  # the address is that page's


def test_a_modifier_key_or_shortcut_does_not_end_the_opening(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)
    page.keyboard.press("Shift")
    page.keyboard.press("Control+l")
    page.wait_for_selector(".wheel-tip", timeout=9000)
    assert state(page)["shut"]  # it ran on to the cover


def test_the_tip_survives_a_resize_across_the_phone_breakpoint(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_selector(".wheel-tip", timeout=9000)
    page.set_viewport_size(PHONE)
    page.wait_for_selector(".wheel-tip", timeout=4000)
    assert state(page)["shut"]


LINK = """(attribute) => {
  const a = document.createElement('a');
  a.setAttribute(attribute.name, attribute.value); a.href = '/'; a.textContent = 'link';
  a.style.cssText = 'position: fixed; left: 20px; top: 120px; z-index: 99; padding: 12px; background: white';
  document.getElementById('notebook').append(a);
}"""


def test_pressing_the_home_link_mid_opening_takes_over_and_adds_no_entry(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)  # mid-spin
    page.evaluate(LINK, {"name": "data-home", "value": ""})
    page.mouse.click(30, 130)  # a real press, so pointerdown comes before the click
    page.wait_for_timeout(3000)
    shown = state(page)
    assert shown["shut"] and shown["path"] == "/" and shown["writes"] == 0
    assert page.evaluate("history.length") == 2


def test_pressing_a_page_link_mid_opening_goes_there_with_one_entry(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)
    page.evaluate(LINK, {"name": "data-open", "value": "tennis"})
    page.mouse.click(30, 130)
    page.wait_for_timeout(3000)
    shown = state(page)
    assert not shown["shut"] and shown["page"] == "tennis"
    assert page.evaluate("history.length") == 3  # the "/" it began on, and the page it went to


def test_a_key_other_than_enter_takes_over_even_from_a_focused_link(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)
    page.evaluate(LINK, {"name": "data-open", "value": "tennis"})
    page.focus("#notebook > a[data-open]")
    page.keyboard.press("ArrowDown")
    page.wait_for_timeout(4500)
    assert not state(page)["shut"]  # the spin stopped under the keyboard visitor


def test_a_press_on_a_link_that_becomes_a_drag_takes_over(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP)
    page.wait_for_timeout(2000)
    page.evaluate(LINK, {"name": "data-open", "value": "tennis"})
    page.mouse.move(30, 130)
    page.mouse.down()
    page.mouse.move(120, 130, steps=5)
    page.mouse.up()
    page.wait_for_timeout(4500)
    assert not state(page)["shut"]


def test_touching_the_wheel_before_the_tip_appears_cancels_it(new_page, live_server_url) -> None:
    page = visit(new_page, live_server_url, DESKTOP, reduced_motion="reduce")
    page.mouse.click(120, 424)  # on the wheel, within the half second before the tip would show
    page.wait_for_timeout(1500)
    assert state(page)["tip"] is None
