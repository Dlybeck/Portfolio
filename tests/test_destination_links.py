import json
import re

from fastapi.testclient import TestClient
from playwright.sync_api import Page, expect
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
    assert page.locator(".mini-window").get_attribute("title") == "Programs portfolio document"

    page.reload(wait_until="domcontentloaded")
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
    expect(
        page.locator('.tile-container[data-title="ScribbleScan"]')
    ).to_have_class(re.compile(r"\bexpanded\b"))
    expect(document.locator("#location")).to_have_text("ScribbleScan")

    page.locator(".close-button").click()
    assert page.url == f"{origin}/projects/programs"
    expect(document.locator("#location")).to_have_text("Programs")

    page.locator(".close-button").click()
    page.locator(".mini-window-container:not(.open)").wait_for()
    assert page.url == f"{origin}/#Programs"

    page.locator(".home-button").click()
    assert page.url == f"{origin}/"
    assert page.locator('.tile-container[data-title="Home"].expanded').count() == 1


def test_internal_document_handoff_reveals_the_board_between_documents(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(
        f"{origin}/projects/programs?theme=canonical",
        wait_until="domcontentloaded",
    )
    document = page.frame_locator(".mini-window")
    expect(document.locator("#location")).to_have_text("Programs")

    # Hold each motion phase until the test advances it. This verifies the
    # rendered handoff through the same DOM/events a Viewer experiences.
    page.evaluate(
        """() => {
            const root = document.documentElement;
            root.style.setProperty('--theme-pack-viewer-exit-duration', '10s');
            root.style.setProperty('--theme-pack-navigation-transition-duration', '10s');
            root.style.setProperty('--theme-pack-viewer-enter-duration', '10s');
            const viewer = document.querySelector('.mini-window-container');
            viewer.style.setProperty('--document-handoff-exit-duration', '10s');
            viewer.style.setProperty('--document-handoff-enter-duration', '10s');
        }"""
    )

    document.get_by_role(
        "link",
        name="View the ScribbleScan project history",
    ).click()

    expect(page).to_have_url(
        f"{origin}/projects/websites/scribblescan?theme=canonical"
    )
    viewer = page.locator(".mini-window-container")
    expect(viewer).to_have_class(re.compile(r"\bhandoff-leaving\b"))
    expect(document.locator("#location")).to_have_text("Programs")
    expect(page.locator(".close-button")).to_be_disabled()
    assert page.locator(
        '.tile-container[data-title="Programs"].expanded'
    ).count() == 1

    viewer.evaluate(
        """node => node.dispatchEvent(new AnimationEvent(
            'animationend', {animationName: 'viewer-exit', bubbles: true}
        ))"""
    )
    expect(viewer).to_have_class(re.compile(r"\bhandoff-moving\b"))
    expect(viewer).to_be_hidden()
    assert page.locator(
        '.tile-container[data-title="ScribbleScan"].expanded'
    ).count() == 1

    page.locator(".tile-layer").evaluate(
        """node => node.dispatchEvent(new TransitionEvent(
            'transitionend', {propertyName: 'transform', bubbles: true}
        ))"""
    )
    expect(viewer).to_have_class(re.compile(r"\bopen\b.*\bhandoff-entering\b"))
    expect(document.locator("#location")).to_have_text("ScribbleScan")

    viewer.evaluate(
        """node => node.dispatchEvent(new AnimationEvent(
            'animationend', {animationName: 'viewer-enter', bubbles: true}
        ))"""
    )
    expect(viewer).to_have_class(re.compile(r"\bopen\b"))
    expect(viewer).not_to_have_class(re.compile(r"\bhandoff-"))
    expect(page.get_by_role("button", name="Go back to previous document")).to_be_enabled()


def test_document_handoff_browser_reversal_keeps_the_latest_destination(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(
        f"{origin}/projects/programs?theme=canonical",
        wait_until="domcontentloaded",
    )
    document = page.frame_locator(".mini-window")
    expect(document.locator("#location")).to_have_text("Programs")
    page.evaluate(
        """() => {
            const root = document.documentElement;
            root.style.setProperty('--theme-pack-navigation-transition-duration', '10s');
            const viewer = document.querySelector('.mini-window-container');
            viewer.style.setProperty('--document-handoff-exit-duration', '10s');
            viewer.style.setProperty('--document-handoff-enter-duration', '10s');
        }"""
    )

    document.get_by_role(
        "link",
        name="View the ScribbleScan project history",
    ).click()
    viewer = page.locator(".mini-window-container")
    expect(viewer).to_have_class(re.compile(r"\bhandoff-leaving\b"))
    viewer.evaluate(
        """node => node.dispatchEvent(new AnimationEvent(
            'animationend', {animationName: 'viewer-exit', bubbles: true}
        ))"""
    )
    expect(viewer).to_have_class(re.compile(r"\bhandoff-moving\b"))
    expect(
        page.locator('.tile-container[data-title="ScribbleScan"]')
    ).to_have_class(re.compile(r"\bexpanded\b"))

    page.evaluate("history.back()")
    expect(page).to_have_url(f"{origin}/projects/programs?theme=canonical")
    expect(
        page.locator('.tile-container[data-title="Programs"]')
    ).to_have_class(re.compile(r"\bexpanded\b"))
    page.locator(".tile-layer").evaluate(
        """node => node.dispatchEvent(new TransitionEvent(
            'transitionend', {propertyName: 'transform', bubbles: true}
        ))"""
    )
    expect(viewer).to_have_class(re.compile(r"\bopen\b.*\bhandoff-entering\b"))
    expect(document.locator("#location")).to_have_text("Programs")
    viewer.evaluate(
        """node => node.dispatchEvent(new AnimationEvent(
            'animationend', {animationName: 'viewer-enter', bubbles: true}
        ))"""
    )

    expect(viewer).not_to_have_class(re.compile(r"\bhandoff-"))
    expect(document.locator("#location")).to_have_text("Programs")


def test_reduced_motion_swaps_documents_without_handoff_animation(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.emulate_media(reduced_motion="reduce")
    page.goto(
        f"{origin}/projects/programs?theme=canonical",
        wait_until="domcontentloaded",
    )
    document = page.frame_locator(".mini-window")
    expect(document.locator("#location")).to_have_text("Programs")

    document.get_by_role(
        "link",
        name="View the ScribbleScan project history",
    ).click()

    expect(page).to_have_url(
        f"{origin}/projects/websites/scribblescan?theme=canonical"
    )
    expect(document.locator("#location")).to_have_text("ScribbleScan")
    viewer = page.locator(".mini-window-container")
    expect(viewer).to_have_class(re.compile(r"\bopen\b"))
    expect(viewer).not_to_have_class(re.compile(r"\bhandoff-"))
    expect(page.locator("body")).not_to_have_class(
        re.compile(r"\bdocument-transitioning\b")
    )


@pytest.mark.parametrize(
    ("link_name", "destination_route", "destination_heading", "board_title"),
    (
        (
            "View the ScribbleScan project history",
            "/projects/websites/scribblescan",
            "ScribbleScan",
            "ScribbleScan",
        ),
        (
            "See how it evolved",
            "/projects/websites/this_website",
            "This Website",
            "This website",
        ),
        (
            "Try the demo",
            "/projects/nba_predictions",
            "NBA Prediction AI",
            "Programs",
        ),
        (
            "View the sprint history",
            "/projects/websites/digital_planner",
            "Digital Planner",
            "Digital Planner",
        ),
    ),
)
def test_browser_history_keeps_internal_document_url_and_content_in_sync(
    browser_page: tuple[Page, str],
    link_name: str,
    destination_route: str,
    destination_heading: str,
    board_title: str,
) -> None:
    page, origin = browser_page
    page.goto(
        f"{origin}/projects/programs?theme=canonical",
        wait_until="domcontentloaded",
    )
    document = page.frame_locator(".mini-window")
    expect(document.locator("#location")).to_have_text("Programs")

    document.get_by_role("link", name=link_name).click()
    expect(page).to_have_url(
        f"{origin}{destination_route}?theme=canonical"
    )
    expect(document.locator("#location")).to_have_text(destination_heading)
    assert page.locator(
        f'.tile-container[data-title="{board_title}"].expanded'
    ).count() == 1

    page.evaluate("history.back()")
    expect(page).to_have_url(f"{origin}/projects/programs?theme=canonical")
    expect(document.locator("#location")).to_have_text("Programs")
    assert page.locator(
        '.tile-container[data-title="Programs"].expanded'
    ).count() == 1

    page.evaluate("history.forward()")
    expect(page).to_have_url(
        f"{origin}{destination_route}?theme=canonical"
    )
    expect(document.locator("#location")).to_have_text(destination_heading)
    assert page.locator(
        f'.tile-container[data-title="{board_title}"].expanded'
    ).count() == 1

    page.get_by_role("button", name="Go back to previous document").click()
    expect(page).to_have_url(f"{origin}/projects/programs?theme=canonical")
    expect(document.locator("#location")).to_have_text("Programs")

    page.get_by_role("button", name="Close document").click()
    expect(page).to_have_url(f"{origin}/?theme=canonical#Programs")
    page.locator(".mini-window-container:not(.open)").wait_for()
    page.wait_for_timeout(500)

    page.evaluate("history.back()")
    expect(page).to_have_url(f"{origin}/projects/programs?theme=canonical")
    expect(document.locator("#location")).to_have_text("Programs")


def test_reopened_nested_document_preserves_escape_history(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(
        f"{origin}/projects/programs?theme=canonical",
        wait_until="domcontentloaded",
    )
    document = page.frame_locator(".mini-window")
    document.get_by_role(
        "link",
        name="View the ScribbleScan project history",
    ).click()
    expect(page).to_have_url(
        f"{origin}/projects/websites/scribblescan?theme=canonical"
    )
    expect(document.locator("#location")).to_have_text("ScribbleScan")

    page.get_by_role("button", name="Home").click()
    expect(page).to_have_url(f"{origin}/?theme=canonical")
    page.locator(".mini-window-container:not(.open)").wait_for()

    page.evaluate("history.back()")
    expect(page).to_have_url(
        f"{origin}/projects/websites/scribblescan?theme=canonical"
    )
    expect(document.locator("#location")).to_have_text("ScribbleScan")
    expect(
        page.get_by_role("button", name="Go back to previous document")
    ).to_be_visible()

    page.keyboard.press("Escape")
    expect(page).to_have_url(f"{origin}/projects/programs?theme=canonical")
    expect(document.locator("#location")).to_have_text("Programs")
    expect(page.get_by_role("button", name="Close document")).to_be_visible()


def focused_control_name(page: Page) -> str | None:
    return page.evaluate(
        """() => document.activeElement?.getAttribute('aria-label')
            || document.activeElement?.textContent?.trim()
            || null"""
    )


def test_keyboard_cycle_contains_only_the_visible_home_neighborhood(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(origin, wait_until="domcontentloaded")

    names = []
    for _ in range(4):
        page.keyboard.press("Tab")
        names.append(focused_control_name(page))

    assert names == [
        "Go to Hobbies",
        "Go to Projects",
        "Go to Work Experience",
        "Go to Education",
    ]
    assert page.locator('.tile-base[tabindex="0"], .expanded-open[tabindex="0"]').count() == 4
    page.keyboard.press("Shift+Tab")
    assert focused_control_name(page) == "Go to Work Experience"


def test_keyboard_activation_and_focus_order_follow_the_parent_child_model(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(f"{origin}/#Hobbies", wait_until="domcontentloaded")

    names = []
    for _ in range(5):
        page.keyboard.press("Tab")
        names.append(focused_control_name(page))
    assert names == [
        "Home",
        "Go to Home",
        "Go to 3D Printing",
        "Go to Gaming",
        "Go to Tennis",
    ]

    page.keyboard.press("Enter")
    assert page.url == f"{origin}/#Tennis"
    assert page.locator('.tile-container[data-title="Tennis"].expanded').count() == 1
    assert focused_control_name(page) == "Open Tennis"

    page.goto(f"{origin}/#Tennis", wait_until="domcontentloaded")
    page.reload(wait_until="domcontentloaded")
    page.keyboard.press("Tab")
    assert focused_control_name(page) == "Home"
    page.keyboard.press("Tab")
    assert focused_control_name(page) == "Go to Hobbies"
    page.keyboard.press("Tab")
    assert focused_control_name(page) == "Open Tennis"
    page.keyboard.press("Space")
    page.locator(".mini-window-container.open").wait_for()
    assert page.url == f"{origin}/hobbies/tennis"


def test_keyboard_hub_activation_moves_focus_to_visible_center_title(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(f"{origin}/#Hobbies", wait_until="domcontentloaded")

    for _ in range(3):
        page.keyboard.press("Tab")
    assert focused_control_name(page) == "Go to 3D Printing"

    page.keyboard.press("Enter")
    assert page.url == f"{origin}/#3D%20Printing"
    assert focused_control_name(page) == "3D Printing"
    assert page.locator(
        '.tile-container[data-title="3D Printing"] .expanded-title'
    ).evaluate("element => getComputedStyle(element).outlineStyle") != "none"


def test_escape_moves_one_level_toward_home(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page

    page.goto(f"{origin}/#Gaming", wait_until="domcontentloaded")
    page.get_by_role("button", name="Go to Hobbies").focus()
    page.keyboard.press("Escape")
    assert page.url == f"{origin}/#Hobbies"
    assert page.locator('.tile-container[data-title="Hobbies"].expanded').count() == 1
    assert focused_control_name(page) == "Hobbies"

    page.keyboard.press("Escape")
    assert page.url == f"{origin}/"
    assert focused_control_name(page) == "Home"
    page.keyboard.press("Escape")
    assert page.url == f"{origin}/"
    assert focused_control_name(page) == "Home"

    page.goto(f"{origin}/hobbies/gaming", wait_until="domcontentloaded")
    page.locator(".mini-window-container.open").wait_for()
    page.keyboard.press("Escape")
    assert page.url == f"{origin}/#Gaming"
    assert focused_control_name(page) == "Open Gaming"

    page.goto(f"{origin}/#Programs", wait_until="domcontentloaded")
    page.locator('.tile-container[data-title="Programs"] .expanded-open').click()
    document = page.frame_locator(".mini-window")
    assert document.locator("#location").inner_text() == "Programs"
    document.locator("a", has_text="ScribbleScan").first.evaluate(
        "element => element.click()"
    )
    assert page.url == f"{origin}/projects/websites/scribblescan"
    expect(document.locator("#location")).to_have_text("ScribbleScan")
    document.locator("body").press("Escape")
    assert page.url == f"{origin}/projects/programs"
    expect(document.locator("#location")).to_have_text("Programs")


def test_reopening_a_document_cancels_the_previous_delayed_teardown(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page

    page.goto(f"{origin}/#Gaming", wait_until="domcontentloaded")
    page.get_by_role("link", name="Open Gaming").click()
    page.locator(".mini-window-container.open").wait_for()
    page.keyboard.press("Escape")

    # A hash-only destination change keeps the same MiniWindow instance alive.
    # Reopening before its close animation finishes must retire that close's
    # delayed iframe/history cleanup.
    page.goto(f"{origin}/#Programs", wait_until="domcontentloaded")
    page.get_by_role("link", name="Open Programs").click()
    document = page.frame_locator(".mini-window")
    expect(document.locator("#location")).to_have_text("Programs")
    page.wait_for_timeout(500)

    expect(page.locator(".mini-window-container")).to_have_class(
        re.compile(r"\bopen\b")
    )
    expect(document.locator("#location")).to_have_text("Programs")
    expect(page.get_by_role("button", name="Close document")).to_be_visible()


def test_primary_controls_are_semantic_named_and_visibly_focusable(
    browser_page: tuple[Page, str],
) -> None:
    page, origin = browser_page
    page.goto(f"{origin}/#Programs", wait_until="domcontentloaded")

    home = page.get_by_role("button", name="Home")
    assert home.evaluate("element => element.tagName") == "BUTTON"

    tile = page.get_by_role("button", name="Go to Projects")
    tile.focus()
    assert tile.evaluate(
        """element => (
            getComputedStyle(element).outlineStyle !== 'none'
            || getComputedStyle(element.querySelector('.theme-object')).filter !== 'none'
        )"""
    )

    page.get_by_role("link", name="Open Programs").click()
    close = page.get_by_role("button", name="Close document")
    assert close.evaluate("element => element.tagName") == "BUTTON"

    document = page.frame_locator(".mini-window")
    document.locator("a", has_text="ScribbleScan").first.click()
    page.get_by_role("button", name="Go back to previous document").wait_for()
    assert page.locator(".mini-window").get_attribute("title") == "ScribbleScan portfolio document"


def test_phone_touch_navigation_preserves_the_board_experience(
    mobile_browser_page: tuple[Page, str],
) -> None:
    page, origin = mobile_browser_page
    page.goto(origin, wait_until="domcontentloaded")

    page.get_by_role("button", name="Go to Hobbies").tap()
    assert page.url == f"{origin}/#Hobbies"
    page.get_by_role("button", name="Go to Gaming").tap()
    assert page.url == f"{origin}/#Gaming"
    page.get_by_role("link", name="Open Gaming").tap()

    page.locator(".mini-window-container.open").wait_for()
    assert page.url == f"{origin}/hobbies/gaming"
    assert page.frame_locator(".mini-window").locator("#location").inner_text() == "Gaming"
