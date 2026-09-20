from pathlib import Path

from fastapi.testclient import TestClient


ROOT = Path(__file__).resolve().parents[1]


def test_programs_leads_with_projects_and_preserves_coursework(
    client: TestClient,
) -> None:
    html = client.get("/_documents/projects/programs").text

    assert html.index("Current projects") < html.index("Earlier projects")
    assert html.index("Earlier projects") < html.index("Coursework archive")
    assert "<details class=\"coursework-archive\">" in html
    for project in (
        "ScribbleScan",
        "This portfolio",
        "NBA Prediction AI",
        "Digital Planner",
    ):
        assert project in html

    for preserved_item in (
        "Negamax Connect 4 bot",
        "Red-Black Tree Binary Search",
        "A* Sliding Puzzle Solver",
        "Heap Sort",
        "Representative voting history by K-Means",
        "Evil Hangman file",
        "Mass Covid Test Process",
        "Selection Sort",
        "Bubble Sort",
    ):
        assert preserved_item in html


def test_scribblescan_claim_is_scoped_and_current_direction_is_qualified(
    client: TestClient,
) -> None:
    html = client.get("/_documents/projects/websites/scribblescan").text
    lower = html.lower()

    assert "five sample pages" in html
    assert "95.10%" in html
    assert "83.46%" in html
    assert "74.39%" in html
    assert "not a general benchmark" in html
    assert "offline, privacy-first mobile reader" in html
    assert "active R&amp;D, not a finished product" in html
    assert "industry-leading" not in lower
    assert "industry leading" not in lower


def test_work_uses_the_same_scoped_scribblescan_result(client: TestClient) -> None:
    html = client.get("/_documents/jobs").text

    assert "Work History" not in html
    assert "five sample pages" in html
    assert "not a general benchmark" in html
    assert "industry-leading" not in html.lower()


def test_board_descriptions_match_the_approved_copy(client: TestClient) -> None:
    script = client.get("/static/scripts/tileData.js").text

    assert "Software projects, experiments, and selected coursework." in script
    assert "From coaching tennis to building AI tools." in script
    assert (
        "Handwriting digitization, from a hosted product to an offline, "
        "privacy-first experiment."
    ) in script


def test_v3_history_includes_the_authentic_seven_theme_evidence(
    client: TestClient,
) -> None:
    html = client.get("/_documents/projects/websites/this_website/v3").text

    assert "September 8th 2026" in html
    assert "seven switchable worlds" in html
    for asset in (
        "original.webp",
        "clouds.webp",
        "islands.webp",
        "lily-pads.webp",
        "planets.webp",
        "postcards.webp",
        "vinyl.webp",
    ):
        path = ROOT / "static/images/projects/this_website/v3/themes" / asset
        assert path.is_file()
        assert path.stat().st_size > 20_000


def test_refresh_does_not_publish_job_search_or_resume_language(
    client: TestClient,
) -> None:
    public_copy = "\n".join(
        client.get(route).text
        for route in (
            "/",
            "/_documents/jobs",
            "/_documents/projects/programs",
            "/_documents/projects/websites/scribblescan",
        )
    ).lower()

    assert "open to work" not in public_copy
    assert "job search" not in public_copy
    assert "resume" not in public_copy
