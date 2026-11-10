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
    assert after["writes"] <= 3


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
