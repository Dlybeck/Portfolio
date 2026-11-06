"""How files are sent (compression, caching) and what search engines are told."""

from __future__ import annotations

import re
from pathlib import Path

from fastapi.testclient import TestClient

from core.discovery import SITE_URL
from core.portfolio import DOCUMENTS

ROOT = Path(__file__).resolve().parent.parent


def test_pages_and_code_are_compressed_and_always_revalidated(client: TestClient) -> None:
    for path in ("/", "/jobs", "/static/css/notebook/notebook.css", "/static/js/notebook/book.js"):
        response = client.get(path, headers={"accept-encoding": "gzip"})
        assert response.headers["content-encoding"] == "gzip", path
        assert response.headers["cache-control"] == "no-cache", path


def test_pictures_fonts_and_video_are_sent_as_they_are_and_kept_for_a_week(client: TestClient) -> None:
    for path in ("/static/img/scribblescan/jul1.webp", "/static/fonts/caveat-latin-700-normal.woff2", "/static/PDF/David-Lybeck-Resume.pdf"):
        response = client.get(path, headers={"accept-encoding": "gzip"})
        assert "content-encoding" not in response.headers, path
        assert response.headers["cache-control"] == "public, max-age=604800", path


def test_video_still_answers_byte_ranges(client: TestClient) -> None:
    response = client.get("/static/img/planner/old.mp4", headers={"range": "bytes=0-99", "accept-encoding": "gzip"})

    assert response.status_code == 206
    assert len(response.content) == 100
    assert "content-encoding" not in response.headers


def test_robots_and_sitemap_list_every_public_address(client: TestClient) -> None:
    robots = client.get("/robots.txt").text
    sitemap = client.get("/sitemap.xml")

    assert f"Sitemap: {SITE_URL}/sitemap.xml" in robots and "Disallow" not in robots
    assert sitemap.headers["content-type"].startswith("application/xml")
    listed = re.findall(r"<loc>([^<]+)</loc>", sitemap.text)
    assert listed == [f"{SITE_URL}/", *(f"{SITE_URL}{d.route}" for d in DOCUMENTS)]


def test_every_route_has_its_own_title_description_and_canonical(client: TestClient) -> None:
    seen = set()
    for document in DOCUMENTS:
        html = client.get(document.route).text
        title = re.search(r"<title>([^<]+)</title>", html).group(1)
        canonical = re.search(r'<link rel="canonical" href="([^"]+)"', html).group(1)
        assert document.page_title in title
        assert canonical == f"{SITE_URL}{document.route}"
        assert (title, canonical) not in seen
        seen.add((title, canonical))
        assert '<meta name="theme-color"' in html


def test_the_old_social_picture_of_the_board_is_gone() -> None:
    assert not (ROOT / "static" / "images" / "social").exists()
    assert (ROOT / "static" / "img" / "social" / "home-notebook.webp").stat().st_size > 20_000


def test_nothing_of_the_old_board_is_left_to_serve() -> None:
    for old in ("static/scripts", "static/themes", "static/css/themes", "core/themes.py", "core/theme_packs.py", "schemas"):
        assert not (ROOT / old).exists(), old
    assert sorted(p.name for p in (ROOT / "static" / "css").iterdir()) == ["notebook"]
