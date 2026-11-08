"""The desktop book reads like a real notebook, and the cover opens as one move on one curve."""

from __future__ import annotations

from pathlib import Path

import pytest

from core import notebook

ROOT = Path(__file__).resolve().parent.parent
DESKTOP = {"width": 1280, "height": 800}


def test_contents_is_the_first_page_on_both_layouts_and_the_intro_page_is_gone() -> None:
    assert "me" not in notebook.PAGES_BY_ID
    assert notebook.PHONE_ORDER[:2] == ("toc", "projects")
    assert notebook.DESKTOP_ORDER[0] == "toc"
    assert len(notebook.PHONE_ORDER) == 13 and len(notebook.DESKTOP_ORDER) == 11
    assert notebook.SECTIONS[0].id == "toc" and notebook.SECTIONS[0].tab == "Contents"
    assert not (ROOT / "templates/notebook/pages/me.html").exists()


def test_the_first_page_sits_right_of_the_inside_front_cover_and_the_last_left_of_the_back() -> None:
    assert notebook.PAGES_BY_ID[notebook.DESKTOP_ORDER[0]].layout == "front"
    assert notebook.PAGES_BY_ID[notebook.DESKTOP_ORDER[-1]].layout == "back"
    assert notebook.PAGES_BY_ID["say"].id == notebook.PHONE_ORDER[-1]


def test_the_old_about_address_opens_the_contents() -> None:
    assert notebook.client_data()["hashAliases"] == {"about": "toc"}
    assert notebook.HASHES["toc"] == "contents"


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
    # the book's slide and the back board's clip are not CSS transitions: one frame loop (swing.js) sets them with the cover
    assert "transition: transform var(--nb-open-ms)" not in css and "transition: clip-path" not in css
    band = css.split(".nb-band {")[1].split("}")[0]
    assert "0.5s" not in band and "var(--nb-open-ease)" in band
    assert "var(--nb-open-ease" in tabs
    # the cover reads the same values from the page instead of repeating them
    assert "--nb-open-ease" in js and "cubic-bezier(0.22" not in js
    assert "createSwing" in js


@pytest.mark.browser
@pytest.mark.parametrize("address", ["/#contents", "/#about"])
def test_the_first_and_last_spreads_have_bare_inside_covers(browser_page, address) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    page.goto(base + address)
    page.wait_for_selector(".nb-page.l .cover-inside--front")

    assert page.locator("#notebook").get_attribute("data-page") == "toc"
    assert page.locator(".nb-page.r .toc").count() == 1
    assert page.locator(".nb-page.l .toc").count() == 0
    assert page.locator(".cover-inside--front > *").count() == 0  # bare, ready for stickers
    assert page.locator(".cover-inside--front").evaluate("n => getComputedStyle(n).containerType") == "size"
    assert page.evaluate("location.hash") == "#contents"

    page.goto(base + "/#say-hi")
    page.wait_for_selector(".nb-page.r .cover-inside--back")
    page.wait_for_selector(".nb-page.l .contact")  # lands when the turning page does
    assert page.locator(".cover-inside--back > *").count() == 0
    assert page.locator(".nb-page.r .toc").count() == 0
