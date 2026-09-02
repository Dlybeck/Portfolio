from fastapi.testclient import TestClient
import pytest
from playwright.sync_api import Page, expect

from core.config import settings


def test_theme_laboratory_is_absent_and_canonical_by_default(
    client: TestClient,
) -> None:
    board = client.get("/?theme=lily")
    document = client.get("/_documents/projects/programs?theme=lily")

    assert board.status_code == 200
    assert '<html lang="en" class="main" data-board-theme="canonical">' in board.text
    assert 'data-theme-selector' not in board.text
    assert '/static/css/themes/' not in board.text
    assert '/static/scripts/themeLab.js' not in board.text

    assert document.status_code == 200
    assert '<html lang="en" data-board-theme="canonical">' in document.text
    assert '/static/css/themes/' not in document.text


def test_enabled_theme_laboratory_renders_known_themes_and_fails_closed(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)

    lily = client.get("/?theme=lily")
    unknown = client.get("/?theme=not-a-world")
    document = client.get("/_documents/projects/programs?theme=planets")

    assert '<html lang="en" class="main" data-board-theme="lily">' in lily.text
    assert 'select data-theme-selector' in lily.text
    assert lily.text.count('class="theme-selector-option"') == 5
    assert '<option class="theme-selector-option" value="canonical"' in lily.text
    assert '<option class="theme-selector-option" value="islands"' in lily.text
    assert '/static/css/themes/board.css' in lily.text
    assert '/static/scripts/themeLab.js' in lily.text

    assert '<html lang="en" class="main" data-board-theme="canonical">' in unknown.text
    assert '<html lang="en" data-board-theme="planets">' in document.text
    assert '/static/css/themes/documents.css' in document.text


def test_theme_switch_replaces_world_and_preserves_it_in_navigation(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page

    page.goto(f"{origin}/?theme=lily", wait_until="domcontentloaded")

    expect(page.locator("html")).to_have_attribute("data-board-theme", "lily")
    expect(page.locator('[data-theme-object="lily"]')).to_have_count(34)
    expect(page.locator('[data-theme-ambient][aria-hidden="true"]')).to_have_count(1)

    page.locator("[data-theme-selector]").select_option("planets")

    expect(page.locator("html")).to_have_attribute("data-board-theme", "planets")
    expect(page).to_have_url(f"{origin}/?theme=planets")
    expect(page.locator('[data-theme-object="lily"]')).to_have_count(0)
    expect(page.locator('[data-theme-object="planets"]')).to_have_count(34)

    page.get_by_role("button", name="Go to Projects").click()
    assert page.url == f"{origin}/?theme=planets#Projects"
    page.get_by_role("button", name="Go to Programs").click()
    page.get_by_role("link", name="Open Programs").click()

    assert page.url == f"{origin}/projects/programs?theme=planets"
    document = page.frame_locator(".mini-window")
    expect(document.locator("html")).to_have_attribute("data-board-theme", "planets")


@pytest.mark.parametrize("theme", ["lily", "planets", "clouds", "islands"])
def test_theme_objects_are_stable_varied_and_matched_across_tile_states(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")

    def home_profile() -> dict[str, str | list[str]]:
        return page.evaluate(
            """() => {
                const home = document.querySelector('.tile-container[data-title="Home"]');
                const neighbors = ['Hobbies', 'Projects', 'Work Experience', 'Education'];
                return {
                    identity: home.dataset.themeIdentity,
                    baseIdentity: home.querySelector('.tile-base [data-theme-identity]').dataset.themeIdentity,
                    expandedIdentity: home.querySelector('.tile-expanded [data-theme-identity]').dataset.themeIdentity,
                    neighborShapes: neighbors.map((title) =>
                        document.querySelector(`.tile-container[data-title="${title}"]`).dataset.themeShape
                    ),
                };
            }"""
        )

    first = home_profile()
    assert first["identity"] == first["baseIdentity"] == first["expandedIdentity"]
    assert len(set(first["neighborShapes"])) == 4

    page.reload(wait_until="domcontentloaded")
    assert home_profile() == first

    page.set_viewport_size({"width": 390, "height": 844})
    assert home_profile() == first


def test_relationship_paths_belong_to_the_world_and_restore_canonical(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme=planets", wait_until="domcontentloaded")

    expect(page.locator('.chalk-arrows path[stroke="#b7d9ff"]')).not_to_have_count(0)
    assert page.locator(".chalk-arrows .arrows-group > g > path").first.evaluate(
        "node => node.parentElement.querySelectorAll('path').length"
    ) == 2

    page.locator("[data-theme-selector]").select_option("islands")
    expect(page.locator('.chalk-arrows path[stroke="#bce8e2"]')).not_to_have_count(0)

    page.locator("[data-theme-selector]").select_option("canonical")
    expect(page.locator('.chalk-arrows path[stroke="#f3efe2"]')).not_to_have_count(0)
    expect(page.locator("[data-theme-object]")).to_have_count(0)
    expect(page.locator("[data-theme-ambient]")).to_have_count(0)


def test_open_document_rethemes_in_place_without_stale_world_state(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/projects/programs?theme=lily", wait_until="domcontentloaded")
    page.locator(".mini-window-container.open").wait_for()
    document = page.frame_locator(".mini-window")
    expect(document.locator("html")).to_have_attribute("data-board-theme", "lily")

    page.locator("[data-theme-selector]").select_option("clouds")
    expect(page).to_have_url(f"{origin}/projects/programs?theme=clouds")
    expect(document.locator("html")).to_have_attribute("data-board-theme", "clouds")
    expect(document.locator("style[data-theme-runtime='clouds']")).to_have_count(1)
    expect(document.locator("[data-theme-runtime='lily']")).to_have_count(0)

    page.locator("[data-theme-selector]").select_option("canonical")
    expect(document.locator("html")).to_have_attribute("data-board-theme", "canonical")
    expect(document.locator("[data-theme-runtime]")).to_have_count(0)


@pytest.mark.parametrize("theme", ["lily", "planets", "clouds", "islands"])
def test_keyboard_hierarchy_is_unchanged_in_each_world(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme={theme}#Hobbies", wait_until="domcontentloaded")

    page.get_by_role("button", name="Go to Gaming").focus()
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{origin}/?theme={theme}#Gaming")
    expect(page.get_by_role("link", name="Open Gaming")).to_be_focused()

    page.keyboard.press("Space")
    page.locator(".mini-window-container.open").wait_for()
    expect(page).to_have_url(f"{origin}/hobbies/gaming?theme={theme}")
    page.keyboard.press("Escape")
    expect(page).to_have_url(f"{origin}/?theme={theme}#Gaming")


@pytest.mark.parametrize("theme", ["lily", "planets", "clouds", "islands"])
def test_phone_objects_keep_home_and_nested_copy_inside_their_layout_box(
    mobile_browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = mobile_browser_page

    for destination in ("Home", "This website"):
        hash_part = "" if destination == "Home" else "#This%20website"
        page.goto(
            f"{origin}/?theme={theme}{hash_part}",
            wait_until="domcontentloaded",
        )
        body = page.locator(
            f'.tile-container[data-title="{destination}"] .tile-expanded .paper-body'
        )
        expect(body).to_be_visible()
        assert body.evaluate(
            """node => {
                const bounds = node.getBoundingClientRect();
                return [...node.querySelectorAll('.expanded-title, .expanded-text, .expanded-open')]
                    .every((content) => {
                        const rect = content.getBoundingClientRect();
                        return rect.top >= bounds.top - 1 && rect.bottom <= bounds.bottom + 1;
                    });
            }"""
        )


def test_development_selector_does_not_enter_the_viewer_neighborhood_focus_cycle(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme=lily", wait_until="domcontentloaded")

    page.keyboard.press("Tab")
    assert page.evaluate(
        "document.activeElement.getAttribute('aria-label')"
    ) == "Go to Hobbies"


@pytest.mark.parametrize("theme", ["lily", "planets", "clouds", "islands"])
def test_neighbor_focus_follows_the_active_object_silhouette(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")
    tile = page.get_by_role("button", name="Go to Projects")
    tile.focus()

    assert tile.evaluate("node => getComputedStyle(node).outlineStyle") == "none"
    assert tile.locator(".theme-object").evaluate(
        "node => getComputedStyle(node).filter"
    ) != "none"


@pytest.mark.parametrize("theme", ["lily", "planets", "clouds", "islands"])
def test_phone_touch_navigation_preserves_each_world(
    mobile_browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = mobile_browser_page
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")

    page.get_by_role("button", name="Go to Hobbies").tap()
    page.get_by_role("button", name="Go to Gaming").tap()
    page.get_by_role("link", name="Open Gaming").tap()

    page.locator(".mini-window-container.open").wait_for()
    expect(page).to_have_url(f"{origin}/hobbies/gaming?theme={theme}")
    expect(page.frame_locator(".mini-window").locator("html")).to_have_attribute(
        "data-board-theme", theme
    )
