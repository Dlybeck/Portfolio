import re

from fastapi.testclient import TestClient


HISTORICAL_ROUTES = (
    "/projects/websites/this_website/v1",
    "/projects/websites/this_website/v2",
    "/projects/websites/this_website/v3",
)

DOCUMENT_ROUTES = (
    "/jobs",
    "/education/college",
    "/education/early_education",
    "/education/agile_report",
    "/hobbies/tennis",
    "/hobbies/gaming",
    "/hobbies/3d_printing/puzzles",
    "/hobbies/3d_printing/other_models",
    "/projects/programs",
    "/projects/nba_predictions",
    "/projects/websites/digital_planner",
    "/projects/websites/scribblescan",
    "/projects/websites/this_website",
    *HISTORICAL_ROUTES,
)


def document_response(client: TestClient, route: str):
    return client.get(f"/_documents{route}")


def test_historical_work_has_no_missing_local_media(client: TestClient) -> None:
    missing: list[tuple[str, str, int]] = []

    for route in HISTORICAL_ROUTES:
        page = document_response(client, route)
        assert page.status_code == 200

        sources = re.findall(r'<(?:img|source)[^>]+src="(/static/[^"#?]+)', page.text)
        for source in sources:
            response = client.get(source)
            if response.status_code != 200:
                missing.append((route, source, response.status_code))

    assert missing == []


def test_work_history_uses_confirmed_technology_services_end_date(
    client: TestClient,
) -> None:
    page = document_response(client, "/jobs")

    assert page.status_code == 200
    assert "August 2022 - May 2025" in page.text
    assert "August 2022 - Present" not in page.text


def test_other_models_document_has_its_own_title(client: TestClient) -> None:
    page = document_response(client, "/hobbies/3d_printing/other_models")

    assert page.status_code == 200
    assert "<title>Other Models | David Lybeck</title>" in page.text


def test_3d_model_documents_do_not_repeat_element_ids(client: TestClient) -> None:
    for route in (
        "/hobbies/3d_printing/puzzles",
        "/hobbies/3d_printing/other_models",
    ):
        page = document_response(client, route)
        assert page.status_code == 200

        identifiers = re.findall(r'\sid="([^"]+)"', page.text)
        assert len(identifiers) == len(set(identifiers)), route


def test_confirmed_mechanical_copy_errors_are_absent(client: TestClient) -> None:
    checks = {
        "/projects/websites/this_website/v1": (
            " just rying ",
            " aswell ",
            "expirimenting",
            " meny ",
        ),
        "/projects/websites/this_website/v2": (
            "habing",
            "noticible",
            "the the sleek",
            "a windows",
        ),
        "/projects/websites/digital_planner": ("aswell", "calander"),
        "/projects/programs": (">onvolutional",),
        "/hobbies/3d_printing/puzzles": ("downlaods",),
    }

    for route, mistakes in checks.items():
        page = document_response(client, route)
        assert page.status_code == 200
        copy = page.text.lower()
        for mistake in mistakes:
            assert mistake not in copy, (route, mistake)


def test_board_copy_uses_calendar_and_mario_kart_spellings(
    client: TestClient,
) -> None:
    script = client.get("/static/scripts/tileData.js")

    assert script.status_code == 200
    assert "calander" not in script.text.lower()
    assert "Mariokart" not in script.text
    assert "calendar and to-do list" in script.text
    assert "Mario Kart Wii" in script.text


def test_scribblescan_is_labeled_as_a_preserved_demo(client: TestClient) -> None:
    for route in (
        "/jobs",
        "/projects/programs",
        "/projects/websites/scribblescan",
    ):
        page = document_response(client, route)
        assert page.status_code == 200
        assert "preserved demo" in page.text.lower(), route

    work_history = document_response(client, "/jobs").text.lower()
    assert "you can try it now" not in work_history


def test_documents_avoid_known_invalid_markup(client: TestClient) -> None:
    for route in DOCUMENT_ROUTES:
        page = document_response(client, route)
        assert page.status_code == 200

        identifiers = re.findall(r'\sid="([^"]+)"', page.text)
        assert len(identifiers) == len(set(identifiers)), route
        assert not re.search(
            r"<a\b[^>]*\btarget=([^ >]+)[^>]*\btarget=",
            page.text,
            re.IGNORECASE,
        ), route
        assert len(re.findall(r"<div\b", page.text, re.IGNORECASE)) == len(
            re.findall(r"</div>", page.text, re.IGNORECASE)
        ), route


def test_visible_local_document_links_resolve(client: TestClient) -> None:
    failures: list[tuple[str, str, int]] = []

    for route in DOCUMENT_ROUTES:
        page = document_response(client, route)
        assert page.status_code == 200
        local_links = re.findall(r'<a\b[^>]+href="(/[^"]+)', page.text)
        for link in local_links:
            response = client.get(link)
            if response.status_code != 200:
                failures.append((route, link, response.status_code))

    assert failures == []
