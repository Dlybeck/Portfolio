"""The inside of the notebook: pictures, links, swipe rows, the predictor, videos and 3D models."""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from pathlib import Path

from fastapi.testclient import TestClient
import pytest

from core import notebook_content as content

ROOT = Path(__file__).resolve().parent.parent
PHONE = {"width": 390, "height": 844}
DESKTOP = {"width": 1280, "height": 800}


class Collector(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.assets: list[str] = []
        self.links: list[tuple[str, str]] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        for name in ("src", "poster", "data-src", "data-alt-src"):
            if values.get(name):
                self.assets.append(values[name])
        if tag == "a":
            self.links.append((values.get("href") or "", values.get("class") or ""))


def collected(client: TestClient) -> Collector:
    parser = Collector()
    parser.feed(client.get("/").text)
    return parser


def test_every_picture_video_and_model_in_the_pages_exists(client: TestClient) -> None:
    assets = [a for a in collected(client).assets if a.startswith("/static/")]

    assert len(assets) > 80
    for asset in sorted(set(assets)):
        assert client.get(asset).status_code == 200, asset


def test_every_page_picture_reserves_its_space(client: TestClient) -> None:
    html = client.get("/").text

    for tag in re.findall(r"<img[^>]*>", html):
        if "/static/img/" in tag:
            assert re.search(r'width="\d+"', tag) and re.search(r'height="\d+"', tag), tag
            assert 'alt="' in tag, tag


def test_pictures_are_phone_sized() -> None:
    for path in (ROOT / "static" / "img").rglob("*"):
        if path.suffix == ".webp":
            assert path.stat().st_size < 200_000, f"{path} is {path.stat().st_size} bytes"
        if path.suffix == ".mp4":
            assert path.stat().st_size < 2_000_000, path


def test_no_link_is_a_placeholder(client: TestClient) -> None:
    for href, _ in collected(client).links:
        assert href and href != "#", href


def test_outbound_links_are_real_and_safe(client: TestClient) -> None:
    html = client.get("/").text

    external = re.findall(r'<a [^>]*href="(https?://[^"]+)"[^>]*>', html)
    assert len(external) > 60  # courses, coursework, 3D model sites, tennis profiles, repositories
    for tag in re.findall(r'<a [^>]*href="https?://[^>]*>', html):
        assert 'rel="noopener"' in tag, tag
    assert 'href="https://scribblescan.app"' in html
    assert 'href="https://github.com/mattzou1/NBA-predictor"' in html
    assert "/static/PDF/ScribbleScan_Proposal.pdf" in html
    assert "/static/PDF/AgileManagement_Report_David.pdf" in html


def test_every_model_site_link_from_the_old_pages_is_kept(client: TestClient) -> None:
    html = client.get("/").text
    expected = [href for group in content.MODELS.values() for m in group for _, href in m["links"]]

    assert len(expected) == 20
    for href in expected:
        assert f'href="{href}"' in html, href


def test_the_old_wording_around_the_models_is_kept(client: TestClient) -> None:
    html = client.get("/").text

    assert "45,000+ downloads" in html
    assert "The sliding puzzle box" in html and "Private for now" in html
    assert "I bet you can't solve them" in html


# ---------- in a browser ----------

def open_page(browser_page, route: str, viewport: dict):
    page, base = browser_page
    page.set_viewport_size(viewport)
    requests: list[str] = []
    page.on("request", lambda r: requests.append(r.url))
    problems: list[str] = []
    page.on("pageerror", lambda e: problems.append(str(e)))
    page.on("console", lambda m: problems.append(m.text) if m.type == "error" else None)
    page.goto(base + route)
    page.wait_for_selector("#notebook.nb--phone, #notebook.nb--desktop")
    return page, base, requests, problems


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_the_nba_predictor_answers_from_results_json(browser_page, viewport: dict) -> None:
    page, base, _, problems = open_page(browser_page, "/projects/nba_predictions", viewport)
    data = json.loads((ROOT / "static" / "json" / "results.json").read_text())

    page.wait_for_function("document.querySelector('.nb-in .team-home').options.length > 5")
    assert page.locator(".nb-in .team-home option").count() == len(data)
    page.select_option(".nb-in .team-home", "ATL")
    page.select_option(".nb-in .team-away", "BKN")
    page.locator(".nb-in .predict-go").click()

    assert page.locator(".nb-in .predict-result").inner_text() == data["ATL"]["BKN"]
    page.select_option(".nb-in .team-away", "ATL")
    page.locator(".nb-in .predict-go").click()
    assert page.locator(".nb-in .predict-result").inner_text() == "Pick two different teams."
    assert problems == []


def test_a_swipe_row_counts_and_steps(browser_page) -> None:
    page, *_ = open_page(browser_page, "/projects/websites/this_website/v1", PHONE)

    count = page.locator(".nb-in .slides-count").first
    assert count.inner_text() == "1 of 8"
    page.locator(".nb-in .slides-next").first.click()
    page.wait_for_function("document.querySelector('.nb-in .slides-count').textContent === '2 of 8'")
    page.locator(".nb-in .slides-prev").first.click()
    page.wait_for_function("document.querySelector('.nb-in .slides-count').textContent === '1 of 8'")


def test_swiping_a_row_does_not_turn_the_page(browser_page) -> None:
    page, *_ = open_page(browser_page, "/projects/websites/this_website/v2", PHONE)
    row = page.locator(".nb-in .slides").first
    box = row.bounding_box()
    y = box["y"] + 60

    page.mouse.move(box["x"] + 280, y)
    page.mouse.down()
    page.mouse.move(box["x"] + 60, y, steps=8)
    page.mouse.up()
    page.wait_for_timeout(900)

    assert page.locator("#notebook").get_attribute("data-page") == "site"


def test_the_seven_themes_are_a_swipe_row(browser_page) -> None:
    page, *_ = open_page(browser_page, "/projects/websites/this_website/v3", DESKTOP)

    assert page.locator('.nb-in .slides[aria-label="The seven themes"] .slide').count() == 7


def test_models_turn_open_and_come_from_this_site(browser_page) -> None:
    page, base, requests, problems = open_page(browser_page, "/hobbies/3d_printing/puzzles", DESKTOP)

    page.wait_for_function("document.querySelector('.nb-in model-viewer')?.getAttribute('src')", timeout=15000)
    assert page.evaluate("!!customElements.get('model-viewer')")
    model = page.locator(".nb-in model-viewer").first
    assert model.get_attribute("src").endswith("FirstPuzzle.glb")

    page.locator(".nb-in .model-toggle").first.click()
    assert model.get_attribute("src").endswith("FirstPuzzle_Open.glb")
    assert page.locator(".nb-in .model-toggle").first.inner_text() == "Close it"
    page.locator(".nb-in .model-toggle").first.click()
    assert model.get_attribute("src").endswith("FirstPuzzle.glb")

    outside = [url for url in requests if not url.startswith(base) and not url.startswith("data:") and not url.startswith("blob:")]
    assert outside == [], outside
    assert problems == []


def test_spinning_through_the_printing_page_does_not_load_models(browser_page) -> None:
    page, base, requests, _ = open_page(browser_page, "/hobbies/gaming", DESKTOP)

    page.locator(".wheel-dial").focus()
    page.keyboard.press("ArrowLeft")
    page.keyboard.press("ArrowRight")
    page.keyboard.press("ArrowRight")
    page.wait_for_timeout(250)

    assert not any(url.endswith(".glb") for url in requests)


@pytest.mark.parametrize("viewport", [PHONE, DESKTOP], ids=["phone", "desktop"])
def test_games_and_work_show_their_pictures(browser_page, viewport: dict) -> None:
    page, *_ = open_page(browser_page, "/hobbies/gaming", viewport)
    assert page.locator(".nb-in .covers img").count() == 20

    page.goto(page.url.replace("/hobbies/gaming", "/jobs"))
    page.wait_for_selector("#notebook[data-page=work]")
    page.wait_for_function("[...document.querySelectorAll('.nb-in .job-mark img')].every(i => i.complete)", timeout=8000)
    assert page.locator(".nb-in .job-mark img").first.evaluate("i => i.naturalWidth") > 0


# ---------- review follow-ups ----------

def test_models_stay_uncompressed_so_the_viewer_never_calls_a_cdn() -> None:
    import struct

    for glb in (ROOT / "static" / "3Dmodels").rglob("*.glb"):
        blob = glb.read_bytes()
        header = json.loads(blob[20 : 20 + struct.unpack("<I", blob[12:16])[0]])
        assert not header.get("extensionsUsed"), f"{glb.name} uses {header.get('extensionsUsed')}"


def test_the_haskell_file_and_the_demo_are_both_linked(client: TestClient) -> None:
    html = client.get("/").text

    assert 'href="/static/programs/Haskell/EvilHangman.hs"' in html
    assert re.search(r'href="/static/programs/Assignments/Evilhangman.html"[^>]*target="_blank"', html)


def test_pdfs_open_outside_the_book(client: TestClient) -> None:
    html = client.get("/").text

    for pdf in ("ScribbleScan_Proposal.pdf", "AgileManagement_Report_David.pdf"):
        assert re.search(rf'href="/static/PDF/{pdf}"[^>]*target="_blank"', html), pdf


def test_snapshots_have_descriptive_alts(client: TestClient) -> None:
    html = client.get("/").text

    assert 'alt="Version 2 sand background and navbar Home button"' in html
    assert "Version 1, January" not in html


def test_each_poster_matches_its_video() -> None:
    sizes = json.loads((ROOT / "static" / "img" / "manifest.json").read_text())

    for name in ("old", "new"):
        video, poster = sizes[f"planner/{name}.mp4"], sizes[f"planner/{name}-poster.webp"]
        assert abs(video[0] / video[1] - poster[0] / poster[1]) < 0.03, (name, video, poster)


def test_say_hi_lists_contacts_and_no_resume_is_offered(client: TestClient) -> None:
    html = client.get("/").text

    assert 'href="https://www.linkedin.com/in/davidlybeck"' in html
    assert 'href="mailto:Dlybeck383@gmail.com"' in html
    assert 'href="https://github.com/Dlybeck"' in html
    # the resume is held off the site: no link, no button and nothing to download
    assert "Resume" not in html and "Lybeck-Resume" not in html
    assert client.get("/static/PDF/David-Lybeck-Resume.pdf").status_code == 404
    assert "Lybeck-Resume" not in client.get("/sitemap.xml").text


def test_the_scribblescan_page_says_what_comes_next_in_one_plain_line(client: TestClient) -> None:
    html = client.get("/projects/websites/scribblescan").text

    assert "<p>I'm still working on what comes next.</p>" in html
    assert "What I&#39;m exploring now" not in html
    assert "from capstone to hosted product." in html


def test_the_scribblescan_job_says_where_things_stand_now(client: TestClient) -> None:
    html = client.get("/jobs").text

    assert "February 2025 to now" in html
    assert "The hosted service is retired and the site remains as a demo, while I keep working on what comes next." in html
    assert "February 2025 to April 2026" not in html
    assert "have since closed" not in html


def test_the_three_tennis_jobs_are_one_work_entry(client: TestClient) -> None:
    html = client.get("/jobs").text

    assert html.count("Tennis coach") == 1
    assert "June 2022 to August 2023" in html
    for place in ("Tacoma Country and Golf Club", "Galbraith Tennis Center", "Portland Tennis Center"):
        assert place in html
    assert "Work · 6 entries" in html and "8 roles" not in html


def test_the_website_page_leads_with_version_four_and_lists_its_snapshots(client: TestClient) -> None:
    html = client.get("/projects/websites/this_website/v4").text

    assert "Version 4, November 2026" in html
    assert 'id="v4"' in html and "/static/img/site/v4-1.webp" in html and "/static/img/site/v4-3.webp" in html
    assert "Version 3, April 2026" not in html


def test_the_reviewed_wording_fixes_are_in(client: TestClient) -> None:
    assert "about three years, 2021 to 2024" in client.get("/education/college").text
    assert "Here are some 3D models" in client.get("/hobbies/3d_printing/other_models").text
    assert "Most link to their code or a demo." in client.get("/projects/programs").text


def test_programs_show_five_picks_and_keep_every_other_item_behind_show_all(client: TestClient) -> None:
    html = client.get("/projects/programs").text
    picks, rest = html.split('<details class="all">')

    for name in ("Negamax Connect 4 bot", "A* sliding puzzle solver", "Mini shell", "Parallel matrix multiplication", "CNN cat vs dog detector", "Evil Hangman"):
        assert name in picks and name not in rest, name
    assert picks.index("Negamax") < picks.index("A* sliding") < picks.index("Mini shell") < picks.index("Parallel") < picks.index("CNN") < picks.index("Evil Hangman")
    assert "alpha-beta" not in html  # the bot is plain negamax
    assert "<summary>Show all" in rest
    for kept in ("K-Means", "Red-black tree", "Mass Covid test process", "Bubble sort", "Hash map"):
        assert kept in rest, kept


def test_say_hi_points_to_the_website_page_instead_of_explaining_it(client: TestClient) -> None:
    html = client.get("/").text

    assert "How it's made" not in html and "About this notebook" not in html
    assert re.search(r'The story is on the <a href="/projects/websites/this_website"[^>]*data-open="site"', html)


def test_the_digital_planner_is_out_of_the_notebook_but_its_old_address_still_leads_somewhere(client: TestClient) -> None:
    response = client.get("/projects/websites/digital_planner", follow_redirects=False)

    assert response.status_code == 301 and response.headers["location"] == "/#projects"
    assert "/projects/websites/digital_planner" not in client.get("/sitemap.xml").text
    home = client.get("/").text
    assert 'id="page-planner"' not in home and "Digital Planner" not in home
    assert "4 entries" in home and "5 entries" not in home
