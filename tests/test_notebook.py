"""Every public route opens the notebook at its own page, with its words in the HTML."""

from __future__ import annotations

import json
import re

from fastapi.testclient import TestClient
import pytest

from core import notebook
from core.portfolio import DOCUMENTS

PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}

# route -> the title of the page it opens, as it reads in the notebook
EXPECTED = {document.route: notebook.PAGES_BY_ID[document.page].title for document in DOCUMENTS}


def nb_data(html: str) -> dict:
    return json.loads(re.search(r'id="nb-data">(.*?)</script>', html, re.S).group(1))


# ---------- the server: every route answers, and writes every page into the HTML ----------

@pytest.mark.parametrize("route", ["/", *EXPECTED])
def test_every_route_returns_the_whole_notebook(client: TestClient, route: str) -> None:
    response = client.get(route)

    assert response.status_code == 200
    for page in notebook.PAGES:
        assert f'id="page-{page.id}"' in response.text, f"{page.id} missing from {route}"


def test_pages_are_server_rendered_with_their_words(client: TestClient) -> None:
    html = client.get("/jobs").text

    assert "Innovation AI Developer" in html
    assert "From coaching tennis to building AI tools." in html
    assert "ScribbleScan LLC" in html


def test_the_page_order_matches_the_notebook(client: TestClient) -> None:
    data = nb_data(client.get("/").text)

    assert len(data["phone"]) == 15
    assert len(data["desktop"]) == 12
    assert set(data["desktop"]) <= set(data["phone"])
    for route in data["routes"].values():
        assert route["page"] in data["phone"]


def test_old_board_routes_are_gone(client: TestClient) -> None:
    assert client.get("/_documents/jobs").status_code == 404
    assert client.get("/_theme-packs/original.json").status_code == 404
    assert client.get("/not-a-page").status_code == 404


def test_the_notebook_loads_no_third_party_assets(client: TestClient) -> None:
    html = client.get("/").text

    assert "fonts.googleapis.com" not in html
    # outbound links are <a> chips inside the pages; scripts and stylesheets must be local
    assert not re.search(r'<script[^>]+src="https?://', html)
    assert not re.search(r'<link[^>]+rel="(?:stylesheet|preload)"[^>]+href="https?://', html)


# ---------- the browser: each route opens the right page, with a clean console ----------

def watch_errors(page) -> list[str]:
    problems: list[str] = []
    page.on("pageerror", lambda error: problems.append(f"pageerror: {error}"))
    page.on("console", lambda m: problems.append(f"console {m.type}: {m.text}") if m.type == "error" else None)
    return problems


def open_route(page, base: str, route: str) -> list[str]:
    problems = watch_errors(page)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    page.wait_for_timeout(250)
    return problems


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
@pytest.mark.parametrize("route", list(EXPECTED))
def test_each_route_opens_its_page(browser_page, viewport: dict, route: str) -> None:
    page, base = browser_page
    page.set_viewport_size(viewport)
    problems = open_route(page, base, route)

    document = next(d for d in DOCUMENTS if d.route == route)
    root = page.locator("#notebook")
    assert root.get_attribute("data-page") == document.page
    assert "is-closed" not in (root.get_attribute("class") or "")
    shown = " ".join(page.locator(".nb-in .page h2, .nb-in .page h3").all_inner_texts()).lower()
    names = (EXPECTED[route].lower(), document.page_title.lower())
    if document.anchor:
        # the part of the page the route names is on screen, inside its scroller
        target = page.locator(f'.nb-in [data-id="{document.anchor}"]')
        assert target.count() == 1
        scroller = target.locator("xpath=ancestor::*[contains(@class,'nb-in')][1]").bounding_box()
        spot = target.bounding_box()
        assert scroller["y"] - 24 <= spot["y"] < scroller["y"] + scroller["height"], (spot, scroller)
    else:
        assert any(name in shown for name in names), shown
    assert problems == []


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_home_shows_the_closed_cover(browser_page, viewport: dict) -> None:
    page, base = browser_page
    page.set_viewport_size(viewport)
    problems = open_route(page, base, "/")

    assert "is-closed" in page.locator("#notebook").get_attribute("class")
    assert page.locator(".nb-leaf.cover").count() == 1
    assert problems == []


def test_the_cover_opens_and_the_address_follows(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    open_route(page, base, "/")

    page.locator(".cover-open").click()
    page.wait_for_timeout(1100)

    assert "is-closed" not in page.locator("#notebook").get_attribute("class")
    assert page.locator("#notebook").get_attribute("data-page") == "me"
    assert page.locator(".nb-leaf.cover").count() == 0


def test_a_link_turns_the_page_and_back_returns(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    open_route(page, base, "/projects/websites/scribblescan")

    page.locator('.nb-page.l a[data-open="nba"]').click()
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "nba"
    assert page.evaluate("location.pathname") == "/projects/nba_predictions"

    page.go_back()
    page.wait_for_timeout(900)
    assert page.locator("#notebook").get_attribute("data-page") == "scribblescan"


def test_contents_link_on_desktop_opens_the_first_spread(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    problems = open_route(page, base, "/#contents")

    assert page.locator("#notebook").get_attribute("data-page") == "me"
    assert page.locator(".nb-pn.rgt").inner_text() == "p.1"
    assert page.locator(".nb-page.r .toc").count() == 1
    assert problems == []


def test_going_back_to_a_route_without_a_part_resets_the_scroll(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(DESKTOP)
    open_route(page, base, "/education/early_education")
    assert page.locator(".nb-page.r .nb-in").evaluate("n => n.scrollTop") > 0

    page.evaluate("history.pushState({}, '', '/education/college'); dispatchEvent(new PopStateEvent('popstate'))")
    page.wait_for_timeout(300)
    assert page.locator(".nb-page.r .nb-in").evaluate("n => n.scrollTop") == 0


def test_the_covered_pages_are_not_reachable_until_the_cover_opens(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(PHONE)
    open_route(page, base, "/")

    assert page.locator(".nb-page").evaluate("n => n.inert") is True
    page.locator(".cover-open").click()
    page.wait_for_timeout(1100)
    assert page.locator(".nb-page").evaluate("n => n.inert") is False
    assert page.evaluate("location.hash") == "#about"


def test_the_wheel_turns_pages_with_the_keyboard(browser_page) -> None:
    page, base = browser_page
    page.set_viewport_size(PHONE)
    problems = open_route(page, base, "/")

    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowRight")  # open the cover
    page.wait_for_timeout(1300)
    page.keyboard.press("ArrowRight")  # page 2, the contents
    page.wait_for_timeout(1300)

    assert page.locator("#notebook").get_attribute("data-page") == "toc"
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowLeft")  # back past page 1: the book closes
    page.wait_for_timeout(1600)
    assert "is-closed" in page.locator("#notebook").get_attribute("class")
    assert problems == []


def test_a_visitor_without_scripts_reads_every_page(browser_page) -> None:
    page, base = browser_page
    context = page.context.browser.new_context(java_script_enabled=False)
    plain = context.new_page()
    plain.goto(base + "/projects/programs")

    assert plain.locator("article.page").count() == len(notebook.PAGES)
    assert plain.locator("#page-programs").is_visible()
    assert "Negamax Connect 4 bot" in plain.locator("#page-programs").inner_text()
    context.close()
