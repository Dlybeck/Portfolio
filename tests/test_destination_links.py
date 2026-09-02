import json
import re

from fastapi.testclient import TestClient
from playwright.sync_api import Page
import pytest


DESTINATIONS = (
    ("/jobs", "Work Experience"),
    ("/education/college", "College"),
    ("/education/early_education", "Early Education"),
    ("/education/agile_report", "College"),
    ("/hobbies/tennis", "Tennis"),
    ("/hobbies/gaming", "Gaming"),
    ("/hobbies/3d_printing/puzzles", "Puzzles"),
    ("/hobbies/3d_printing/other_models", "Other Models"),
    ("/projects/programs", "Programs"),
    ("/projects/nba_predictions", "Programs"),
    ("/projects/websites/digital_planner", "Digital Planner"),
    ("/projects/websites/scribblescan", "ScribbleScan"),
    ("/projects/websites/this_website", "This website"),
    ("/projects/websites/this_website/v1", "This website"),
    ("/projects/websites/this_website/v2", "This website"),
    ("/projects/websites/this_website/v3", "This website"),
)

DIRECT_DESTINATION_HEADINGS = (
    ("/jobs", "Work Experience", "Professional History"),
    ("/education/college", "College", "College"),
    ("/education/early_education", "Early Education", "Early Education"),
    ("/education/agile_report", "College", "Agile Management Report"),
    ("/hobbies/tennis", "Tennis", "Tennis"),
    ("/hobbies/gaming", "Gaming", "Gaming"),
    ("/hobbies/3d_printing/puzzles", "Puzzles", "Puzzles"),
    ("/hobbies/3d_printing/other_models", "Other Models", "Other Models"),
    ("/projects/programs", "Programs", "Programs"),
    ("/projects/nba_predictions", "Programs", "NBA Prediction AI"),
    ("/projects/websites/digital_planner", "Digital Planner", "Digital Planner"),
    ("/projects/websites/scribblescan", "ScribbleScan", "ScribbleScan"),
    ("/projects/websites/this_website", "This website", "This Website"),
    ("/projects/websites/this_website/v1", "This website", "DavidLybeck.com Version 1"),
    ("/projects/websites/this_website/v2", "This website", "DavidLybeck.com Version 2"),
    ("/projects/websites/this_website/v3", "This website", "DavidLybeck.com Version 3"),
)


def portfolio_state(html: str) -> dict[str, object]:
    match = re.search(
        r'<script id="portfolio-state" type="application/json">(.*?)</script>',
        html,
        re.DOTALL,
    )
    assert match is not None
    return json.loads(match.group(1))


def test_destination_link_restores_its_document_inside_the_board(
    client: TestClient,
) -> None:
    destination = client.get("/projects/programs")

    assert destination.status_code == 200
    assert '<div class="map">' in destination.text
    assert 'id="portfolio-state"' in destination.text
    assert '"route": "/projects/programs"' in destination.text
    assert '"title": "Programs"' in destination.text

    document = client.get("/_documents/projects/programs")
    assert document.status_code == 200
    assert '<h2 id="location">Programs</h2>' in document.text
    assert '<div class="map">' not in document.text


@pytest.mark.parametrize(("route", "board_title"), DESTINATIONS)
def test_every_destination_has_one_board_and_document_representation(
    client: TestClient, route: str, board_title: str
) -> None:
    destination = client.get(route)
    document = client.get(f"/_documents{route}")

    assert destination.status_code == 200
    assert portfolio_state(destination.text)["initialDestination"] == {
        "route": route,
        "title": board_title,
    }
    assert '<div class="map">' in destination.text
    assert document.status_code == 200
    assert '<div class="map">' not in document.text


def test_home_is_the_board_root_and_unknown_documents_fail_closed(
    client: TestClient,
) -> None:
    home = client.get("/")

    assert home.status_code == 200
    assert portfolio_state(home.text)["initialDestination"] is None
    assert client.get("/_documents/not-a-document").status_code == 404


def test_direct_destination_opens_document_at_its_board_location(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page

    page.goto(f"{origin}/projects/programs", wait_until="domcontentloaded")

    page.locator(".mini-window-container.open").wait_for()
    assert page.url == f"{origin}/projects/programs"
    assert page.locator('.tile-container[data-title="Programs"].expanded').count() == 1
    assert page.frame_locator(".mini-window").locator("#location").inner_text() == "Programs"


def test_every_direct_destination_opens_at_the_expected_board_location(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page

    for route, board_title, heading in DIRECT_DESTINATION_HEADINGS:
        page.goto(f"{origin}{route}", wait_until="domcontentloaded")
        page.locator(".mini-window-container.open").wait_for()

        assert page.url == f"{origin}{route}"
        assert page.locator(
            f'.tile-container[data-title="{board_title}"].expanded'
        ).count() == 1
        assert page.frame_locator(".mini-window").locator("#location").inner_text() == heading


def test_document_controls_preserve_board_aware_destinations(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(f"{origin}/#Programs", wait_until="domcontentloaded")

    programs = page.locator('.tile-container[data-title="Programs"].expanded')
    programs.wait_for()
    programs.locator(".expanded-open").click()
    page.locator(".mini-window-container.open").wait_for()
    assert page.url == f"{origin}/projects/programs"

    document = page.frame_locator(".mini-window")
    document.locator("a", has_text="ScribbleScan").first.click()
    assert page.url == f"{origin}/projects/websites/scribblescan"
    assert page.locator('.tile-container[data-title="ScribbleScan"].expanded').count() == 1
    assert document.locator("#location").inner_text() == "ScribbleScan"

    page.locator(".close-button").click()
    assert page.url == f"{origin}/projects/programs"
    assert document.locator("#location").inner_text() == "Programs"

    page.locator(".close-button").click()
    page.locator(".mini-window-container:not(.open)").wait_for()
    assert page.url == f"{origin}/#Programs"

    page.locator(".home-button").click()
    assert page.url == f"{origin}/"
    assert page.locator('.tile-container[data-title="Home"].expanded').count() == 1
