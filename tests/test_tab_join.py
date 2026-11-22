"""The open section's tab is pulled out, but it must stay joined to the page: no gap opens behind it."""

from __future__ import annotations

import pytest

DESKTOP = dict(viewport={"width": 1440, "height": 900})
PHONES = [dict(viewport={"width": w, "height": h}, is_mobile=True, has_touch=True) for w, h in [(360, 740), (390, 844), (430, 932)]]
DEVICES = [DESKTOP, *PHONES]
IDS = ["desktop-1440", "phone-360", "phone-390", "phone-430"]

# Where each tab's coloured part starts. A phone tab keeps 10px of invisible touch room before its ::before strip.
DRAWN_LEFTS = """() => {
  const phone = !!document.querySelector('#notebook.nb--phone');
  return [...document.querySelectorAll('.nb-tab')].map((tab) =>
    tab.getBoundingClientRect().left + (phone ? parseFloat(getComputedStyle(tab, '::before').left) : 0));
}"""

# Sample the tabs on every frame for `ms`, and report the widest the spread of left edges ever got.
WORST_SPREAD = """(ms) => new Promise((done) => {
  const phone = !!document.querySelector('#notebook.nb--phone');
  const lefts = () => [...document.querySelectorAll('.nb-tab')].map((tab) =>
    tab.getBoundingClientRect().left + (phone ? parseFloat(getComputedStyle(tab, '::before').left) : 0));
  const start = performance.now();
  let worst = 0;
  const frame = () => {
    const l = lefts();
    worst = Math.max(worst, Math.max(...l) - Math.min(...l));
    if (performance.now() - start < ms) requestAnimationFrame(frame); else done(worst);
  };
  frame();
})"""


def open_page(new_page, base, route, device):
    page = new_page(**device)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(1500)
    return page


@pytest.mark.parametrize("device", DEVICES, ids=IDS)
def test_the_pulled_out_tab_starts_where_the_resting_tabs_do(new_page, live_server_url, device) -> None:
    page = open_page(new_page, live_server_url, "/jobs", device)

    lefts = page.evaluate(DRAWN_LEFTS)
    assert len(lefts) == 6
    assert max(lefts) - min(lefts) < 0.5, lefts  # the pulled-out tab reaches back to the page edge: no gap behind it


# How the visitor turns the page: a mouse click on a tab, a finger tap on it, or a trackpad scroll over the side wheel (desktop only). Playwright
# emulates all three; none of this runs on real hardware.
TURNS = [(d, how, i) for d, i in zip(DEVICES, IDS) for how in (["click", "wheel"] if d is DESKTOP else ["click", "tap"])]


@pytest.mark.parametrize("device, how", [(d, how) for d, how, _ in TURNS], ids=[f"{i}-{how}" for _, how, i in TURNS])
def test_no_gap_opens_while_the_tab_slides_out_on_a_page_turn(new_page, live_server_url, device, how) -> None:
    page = open_page(new_page, live_server_url, "/jobs", device)
    before = page.locator("#notebook").get_attribute("data-page")

    if how == "click":
        page.locator(".nb-tab", has_text="Hobbies").click()
    elif how == "tap":
        page.locator(".nb-tab", has_text="Hobbies").tap()
    else:
        box = page.locator(".wheel").bounding_box()
        page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2)
        page.mouse.wheel(0, 400)  # a trackpad scroll over the side wheel turns the page
    assert page.evaluate(WORST_SPREAD, 1500) < 0.5
    if how != "wheel":
        assert page.locator('.nb-tab[aria-current="page"]').inner_text() == "Hobbies"
    else:
        assert page.locator("#notebook").get_attribute("data-page") != before  # the page did turn


@pytest.mark.parametrize("device", DEVICES, ids=IDS)
def test_no_gap_opens_while_the_book_opens_and_shuts(new_page, live_server_url, device) -> None:
    page = open_page(new_page, live_server_url, "/", device)

    page.locator(".cover-open").click(no_wait_after=True)
    assert page.evaluate(WORST_SPREAD, 2000) < 0.5
    assert page.locator(".nb.is-closed").count() == 0


@pytest.mark.parametrize("device", DEVICES, ids=IDS)
def test_no_gap_opens_while_the_book_shuts_again(new_page, live_server_url, device) -> None:
    page = open_page(new_page, live_server_url, "/", device)
    page.locator(".cover-open").click()
    page.wait_for_timeout(1500)
    assert page.locator(".nb.is-closed").count() == 0

    page.go_back()  # back to the cover: the book swings shut
    assert page.evaluate(WORST_SPREAD, 2000) < 0.5
    page.wait_for_selector(".nb.is-closed")


def test_with_reduced_motion_the_phone_strip_does_not_ease_either(new_page, live_server_url) -> None:
    page = new_page(**PHONES[1], reduced_motion="reduce")
    page.goto(live_server_url + "/jobs")
    page.wait_for_selector("#notebook.nb--phone")
    page.wait_for_timeout(1500)

    assert page.locator(".nb-tab").first.evaluate("n => getComputedStyle(n, '::before').transitionDuration") in ("0s", "0.0s")
    assert page.locator(".nb-tab").first.evaluate("n => getComputedStyle(n).transitionDuration") in ("0s", "0.0s")
