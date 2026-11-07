"""Nothing is painted over the section tabs, and the page's own scroll bar stays off them."""

from __future__ import annotations

import pytest

PHONE = dict(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True, device_scale_factor=2)
DESKTOP = dict(viewport={"width": 1280, "height": 800})
ROUTES = ["/education/college", "/education/early_education", "/jobs"]  # School, a short School page, Work

# Hit-tests ignore anything with `pointer-events: none`, which is exactly how a decoration (the band) could sit over the
# tabs unseen. So switch every element back on first and ask what is topmost at several points of each tab's coloured part.
TOPMOST = """() => {
  const style = document.createElement('style');
  style.textContent = '* { pointer-events: auto !important; }';
  document.head.appendChild(style);
  const covered = [];
  for (const tab of document.querySelectorAll('.nb-tab')) {
    const r = tab.getBoundingClientRect();
    const inset = document.querySelector('#notebook.nb--phone') ? 10 : 0; // a phone tab's first 10px is invisible touch room
    for (const fx of [0.2, 0.5, 0.8]) for (const fy of [0.15, 0.5, 0.85]) {
      const x = r.left + inset + (r.width - inset) * fx, y = r.top + r.height * fy;
      const top = document.elementsFromPoint(x, y)[0];
      if (top !== tab && !tab.contains(top)) covered.push(`${tab.textContent.trim()} at ${Math.round(x)},${Math.round(y)}: ${top.className || top.tagName}`);
    }
  }
  style.remove();
  return covered;
}"""


def open_page(new_page, base, route, device):
    page = new_page(**device)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(1500)
    return page


@pytest.mark.parametrize("route", ROUTES)
@pytest.mark.parametrize("device", [PHONE, DESKTOP], ids=["phone-390", "desktop-1280"])
def test_the_tab_strip_is_not_covered_by_anything(new_page, live_server_url, route, device) -> None:
    page = open_page(new_page, live_server_url, route, device)

    assert page.locator(".nb-tab").count() == 6
    assert page.evaluate(TOPMOST) == []


def test_the_pages_own_scroll_bar_ends_before_the_first_tab_on_a_phone(new_page, live_server_url) -> None:
    page = open_page(new_page, live_server_url, "/education/college", PHONE)

    scroller_right = page.evaluate(
        "() => { const e = document.querySelector('.nb-page .nb-in'); return e.getBoundingClientRect().right; }"
    )
    tabs_left = min(
        page.locator(".nb-tab").evaluate_all("els => els.map(e => e.getBoundingClientRect().left + 10)")  # the coloured part starts 10px in
    )
    assert scroller_right <= tabs_left
