from html.parser import HTMLParser
import os

from fastapi.testclient import TestClient
from playwright.sync_api import sync_playwright

from core.portfolio import DOCUMENTS


class MediaAuditParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.media: list[tuple[str, dict[str, str | None]]] = []

    def handle_starttag(
        self, tag: str, attrs: list[tuple[str, str | None]]
    ) -> None:
        if tag in {"img", "iframe", "model-viewer"}:
            self.media.append((tag, dict(attrs)))


def parsed_media(html: str) -> list[tuple[str, dict[str, str | None]]]:
    parser = MediaAuditParser()
    parser.feed(html)
    return parser.media


def test_every_document_media_element_has_an_accessible_description(
    client: TestClient,
) -> None:
    failures: list[tuple[str, str, str | None]] = []

    for document in DOCUMENTS:
        response = client.get(f"/_documents{document.route}")
        assert response.status_code == 200
        for tag, attrs in parsed_media(response.text):
            if tag == "img" and not (attrs.get("alt") or "").strip():
                failures.append((document.route, tag, attrs.get("src")))
            elif tag == "iframe" and not (attrs.get("title") or "").strip():
                failures.append((document.route, tag, attrs.get("src")))
            elif tag == "model-viewer" and not (
                attrs.get("aria-label") or ""
            ).strip():
                failures.append((document.route, tag, attrs.get("src")))

    assert failures == []


def test_board_media_classifies_meaningful_and_decorative_images(
    client: TestClient,
) -> None:
    response = client.get("/")
    media = parsed_media(response.text)

    assert ("img", {"src": "/static/images/Logo.webp", "alt": "David Lybeck logo", "class": "navbar-logo"}) in media
    home_images = [attrs for tag, attrs in media if attrs.get("src") == "/static/images/home.webp"]
    assert home_images == [{"src": "/static/images/home.webp", "alt": ""}]
    assert all((attrs.get("title") or "").strip() for tag, attrs in media if tag == "iframe")


def test_reduced_motion_shortens_board_and_document_transitions(
    live_server_url: str,
) -> None:
    endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
    with sync_playwright() as playwright:
        browser = (
            playwright.chromium.connect(endpoint)
            if endpoint
            else playwright.chromium.launch(headless=True)
        )
        try:
            default_context = browser.new_context()
            default_page = default_context.new_page()
            # Pin the pack: an unqualified load chooses a random theme. Original
            # Home has an existing -10ms variation on its 800ms cover preset.
            default_page.goto(f"{live_server_url}/?theme=canonical", wait_until="networkidle")
            assert default_page.locator(".tile-layer").evaluate(
                "element => getComputedStyle(element).transitionDuration"
            ) == "0.45s"
            assert default_page.locator(
                '.tile-container[data-title="Home"] .tile-expanded'
            ).evaluate(
                "element => getComputedStyle(element).animationDuration"
            ) == "0.79s"
            default_page.goto(
                f"{live_server_url}/_documents/hobbies/3d_printing/puzzles",
                wait_until="domcontentloaded",
            )
            assert default_page.locator("model-viewer[auto-rotate]").count() == 10
            default_context.close()

            reduced_context = browser.new_context(reduced_motion="reduce")
            reduced_page = reduced_context.new_page()
            reduced_page.goto(f"{live_server_url}/?theme=canonical", wait_until="networkidle")
            assert reduced_page.locator(".tile-layer").evaluate(
                "element => parseFloat(getComputedStyle(element).transitionDuration)"
            ) <= 0.001
            assert reduced_page.locator(
                '.tile-container[data-title="Home"] .tile-expanded'
            ).evaluate(
                "element => parseFloat(getComputedStyle(element).animationDuration)"
            ) <= 0.001
            reduced_page.goto(
                f"{live_server_url}/_documents/hobbies/3d_printing/puzzles",
                wait_until="domcontentloaded",
            )
            assert reduced_page.locator("model-viewer[auto-rotate]").count() == 0
            reduced_context.close()
        finally:
            browser.close()
