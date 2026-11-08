"""The desktop book reads like a real notebook, and the cover opens as one move on one curve."""

from __future__ import annotations

from pathlib import Path

import pytest

from core import notebook

ROOT = Path(__file__).resolve().parent.parent
DESKTOP = {"width": 1280, "height": 800}


def test_the_first_page_sits_right_of_the_inside_front_cover_and_the_last_left_of_the_back() -> None:
    first, last = notebook.PAGES_BY_ID[notebook.DESKTOP_ORDER[0]], notebook.PAGES_BY_ID[notebook.DESKTOP_ORDER[-1]]

    assert (first.id, first.layout, first.pair) == ("me", "front", "toc")
    assert (last.id, last.layout, last.pair) == ("say", "back", None)


def test_the_contents_is_not_a_desktop_page_of_its_own_and_the_phone_order_is_unchanged() -> None:
    assert "toc" not in notebook.DESKTOP_ORDER
    assert notebook.PHONE_ORDER[:3] == ("me", "toc", "projects")
    assert notebook.PHONE_ORDER[-1] == "say"


def test_school_gives_each_side_of_its_spread_real_content() -> None:
    page = notebook.PAGES_BY_ID["school"]

    assert page.layout == "split" and page.split == 2
    assert notebook.client_data()["pages"]["school"]["split"] == 2


def test_opening_and_closing_share_one_ease_in_out_curve_and_duration() -> None:
    css = (ROOT / "static/css/notebook/notebook.css").read_text()
    js = (ROOT / "static/js/notebook/cover.js").read_text()
    tabs = (ROOT / "static/css/notebook/tabs.css").read_text()

    assert "--nb-open-ease: cubic-bezier(0.65, 0, 0.35, 1);" in css
    assert "--nb-open-ms: 800ms;" in css
    # the book, the back board and the band all use the shared values; none keeps a timing of its own
    assert "transition: transform var(--nb-open-ms) var(--nb-open-ease)" in css
    assert "transition: clip-path var(--nb-open-ms) var(--nb-open-ease)" in css
    band = css.split(".nb-band {")[1].split("}")[0]
    assert "0.5s" not in band and "var(--nb-open-ease)" in band
    assert "var(--nb-open-ease" in tabs
    # the cover reads the same values from the page instead of repeating them
    assert "--nb-open-ease" in js and "cubic-bezier(0.22" not in js


@pytest.mark.browser
def test_the_first_and_last_spreads_have_an_inside_cover(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    page.goto(base + "/#about")
    page.wait_for_selector(".nb-page.l .cover-inside--front")

    assert page.locator(".nb-page.l .cover-inside--front .toc").count() == 1
    assert page.locator(".nb-page.r .toc").count() == 0
    assert page.locator(".cover-inside--front").evaluate("n => getComputedStyle(n).containerType") == "size"

    page.goto(base + "/#say-hi")
    page.wait_for_selector(".nb-page.r .cover-inside--back")
    page.wait_for_selector(".nb-page.l .contact")  # lands when the turning page does
    assert page.locator(".nb-page.r .toc").count() == 0
