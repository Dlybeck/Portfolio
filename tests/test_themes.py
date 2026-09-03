from fastapi.testclient import TestClient
import pytest
from playwright.sync_api import Page, expect

from core.config import settings
from core import theme_packs
from scripts.audit_theme_variants import (
    MINIMUM_AXIS_COUNT,
    audit_world,
)


VISUAL_THEMES = ["canonical", "lily", "planets", "clouds", "islands"]


def test_theme_laboratory_is_absent_and_canonical_by_default(
    client: TestClient,
) -> None:
    board = client.get("/?theme=lily")
    document = client.get("/_documents/projects/programs?theme=lily")

    assert board.status_code == 200
    assert '<html lang="en" class="main" data-board-theme="canonical">' in board.text
    assert 'data-theme-selector' not in board.text
    assert '/static/css/themes/' not in board.text
    assert '/static/scripts/themeEngine.js' not in board.text

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

    assert '<html lang="en" class="main" data-board-theme="lily" data-theme-pack-visual' in lily.text
    assert 'select data-theme-selector' in lily.text
    assert lily.text.count('class="theme-selector-option"') == 5
    assert '<option class="theme-selector-option" value="canonical"' in lily.text
    assert '<option class="theme-selector-option" value="islands"' in lily.text
    assert '/static/css/themes/board.css' in lily.text
    assert '/static/css/theme-structure.css' in lily.text
    assert '/static/css/base.css' not in lily.text
    assert '/static/css/map.css' not in lily.text
    assert '/static/scripts/themeEngine.js' in lily.text

    assert '<html lang="en" class="main" data-board-theme="canonical" data-theme-pack-visual' in unknown.text
    assert '<html lang="en" data-board-theme="planets" data-theme-pack-visual' in document.text
    assert '/static/css/themes/documents.css' in document.text
    assert '/static/css/document-structure.css' in document.text
    assert '/static/css/page.css' not in document.text


def test_runtime_themes_can_be_enabled_without_exposing_the_developer_selector(
    client: TestClient,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", False)
    monkeypatch.setattr(settings, "THEMES_ENABLED", True)
    monkeypatch.setattr(settings, "THEME_SELECTOR_ENABLED", False)
    monkeypatch.setattr(theme_packs.secrets, "randbelow", lambda total: 1)

    board = client.get("/")

    assert 'data-board-theme="clouds"' in board.text
    assert 'data-theme-selector' not in board.text
    assert 'id="theme-pack-catalog"' in board.text
    assert '/static/scripts/themeEngine.js' in board.text


def test_theme_switch_replaces_world_and_preserves_it_in_navigation(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page

    page.goto(f"{origin}/?theme=lily", wait_until="domcontentloaded")

    expect(page.locator("html")).to_have_attribute("data-board-theme", "lily")
    expect(page.locator("html")).to_have_attribute("data-theme-focus-motion", "grow")
    expect(page.locator('[data-theme-object="lily"]')).to_have_count(34)
    expect(page.locator('[data-theme-ambient][aria-hidden="true"]')).to_have_count(1)

    page.locator("[data-theme-selector]").select_option("planets")

    expect(page.locator("html")).to_have_attribute("data-board-theme", "planets")
    expect(page.locator("html")).to_have_attribute("data-theme-focus-motion", "grow")
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


@pytest.mark.parametrize(
    ("theme", "recipe", "enter_animation"),
    [
        ("canonical", "cover", "cover-enter"),
        ("lily", "grow", "focus-grow-enter"),
        ("planets", "grow", "focus-grow-enter"),
        ("clouds", "settle", "focus-settle-enter"),
        ("islands", "settle", "focus-settle-enter"),
    ],
)
def test_each_theme_selects_its_declared_focus_motion(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
    recipe: str,
    enter_animation: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page

    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")

    expect(page.locator("html")).to_have_attribute("data-theme-focus-motion", recipe)
    assert page.locator(
        '.tile-container[data-title="Home"] .tile-expanded'
    ).evaluate("node => getComputedStyle(node).animationName") == enter_animation
    expected_base_opacity = "1" if recipe == "cover" else "0"
    assert page.locator(
        '.tile-container[data-title="Home"] .tile-base'
    ).evaluate("node => getComputedStyle(node).opacity") == expected_base_opacity


@pytest.mark.parametrize(
    ("theme", "exit_animation"),
    [
        ("canonical", "cover-sweep"),
        ("lily", "focus-grow-exit"),
        ("planets", "focus-grow-exit"),
        ("clouds", "focus-settle-exit"),
        ("islands", "focus-settle-exit"),
    ],
)
def test_focus_exit_finishes_once_and_keeps_neighbors_actionable(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
    exit_animation: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")
    home_cover = page.locator('.tile-container[data-title="Home"] .tile-expanded')

    page.get_by_role("button", name="Go to Projects").click()

    expect(page.get_by_role("button", name="Go to Programs")).to_be_visible()
    expect(page.get_by_role("button", name="Go to Websites")).to_be_visible()
    expect(page.get_by_role("button", name="Go to Home")).to_be_visible()
    expect(page.get_by_role("button", name="Go to Programs")).to_be_enabled()
    assert exit_animation in home_cover.evaluate(
        "node => getComputedStyle(node).animationName"
    )
    # This is a real pointer action while the former center is exiting; it
    # proves the motion layer does not steal the neighboring destination.
    page.get_by_role("button", name="Go to Websites").click()
    expect(page).to_have_url(f"{origin}/?theme={theme}#Websites")
    home_cover.evaluate(
        "node => node.dispatchEvent(new AnimationEvent('animationend', {bubbles: true}))"
    )
    expect(home_cover).to_be_hidden()
    page.wait_for_timeout(100)
    expect(home_cover).to_be_hidden()


def test_unpinned_refresh_selects_a_new_world_while_a_query_pin_is_stable(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    tickets = iter((1, 2, 3))
    monkeypatch.setattr(theme_packs.secrets, "randbelow", lambda total: next(tickets))
    page, origin = browser_page

    page.goto(origin, wait_until="domcontentloaded")
    first = page.locator("html").get_attribute("data-board-theme")
    assert first == "clouds"
    expect(page).to_have_url(f"{origin}/")

    page.reload(wait_until="domcontentloaded")
    second = page.locator("html").get_attribute("data-board-theme")
    assert second == "lily"
    assert second != first
    expect(page).to_have_url(f"{origin}/")

    page.goto(f"{origin}/?theme=lily", wait_until="domcontentloaded")
    page.reload(wait_until="domcontentloaded")
    expect(page.locator("html")).to_have_attribute("data-board-theme", "lily")
    expect(page).to_have_url(f"{origin}/?theme=lily")


@pytest.mark.parametrize("theme", VISUAL_THEMES)
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
                    neighborVariants: neighbors.map((title) =>
                        document.querySelector(
                            `.tile-container[data-title="${title}"] .tile-base [data-theme-variant]`
                        ).dataset.themeVariant
                    ),
                };
            }"""
        )

    first = home_profile()
    programs_identity = page.locator(
        '.tile-container[data-title="Programs"]'
    ).get_attribute("data-theme-identity")
    assert first["identity"] == first["baseIdentity"] == first["expandedIdentity"]
    assert len(set(first["neighborVariants"])) == 4

    page.reload(wait_until="domcontentloaded")
    assert home_profile() == first

    page.get_by_role("button", name="Go to Projects").click()
    expect(page).to_have_url(f"{origin}/?theme={theme}#Projects")
    page.keyboard.press("Escape")
    expect(page).to_have_url(f"{origin}/?theme={theme}")
    assert home_profile() == first

    page.set_viewport_size({"width": 390, "height": 844})
    assert home_profile() == first

    page.goto(
        f"{origin}/projects/programs?theme={theme}",
        wait_until="domcontentloaded",
    )
    page.locator(".mini-window-container.open").wait_for()
    assert page.locator(
        '.tile-container[data-title="Programs"]'
    ).get_attribute("data-theme-identity") == programs_identity
    expect(page.frame_locator(".mini-window").locator("#location")).to_have_text(
        "Programs"
    )


def test_relationship_paths_belong_to_the_world_and_restore_canonical(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme=planets", wait_until="domcontentloaded")

    expect(page.locator('.chalk-arrows path[stroke="#b7d9ff"]')).not_to_have_count(0)
    expect(page.locator('.chalk-arrows .arrows-group')).to_have_attribute(
        "filter", "url(#relationship-glow)"
    )
    assert page.locator('.chalk-arrows path[stroke="#b7d9ff"]').first.get_attribute(
        "stroke-dasharray"
    )
    assert page.locator(".chalk-arrows .arrows-group > g > path").first.evaluate(
        "node => node.parentElement.querySelectorAll('path').length"
    ) == 2

    page.locator("[data-theme-selector]").select_option("islands")
    expect(page.locator('.chalk-arrows path[stroke="#bce8e2"]')).not_to_have_count(0)
    assert page.locator('.chalk-arrows .arrows-group').get_attribute("filter") is None
    assert page.locator('.chalk-arrows path[stroke="#bce8e2"]').first.get_attribute(
        "stroke-dasharray"
    )

    page.locator("[data-theme-selector]").select_option("canonical")
    expect(page.locator('.chalk-arrows path[stroke="#f3efe2"]')).not_to_have_count(0)
    expect(page.locator('.chalk-arrows .arrows-group')).to_have_attribute(
        "filter", "url(#relationship-rough)"
    )
    expect(page.locator('[data-theme-object="canonical"]')).to_have_count(34)
    expect(page.locator("[data-theme-ambient]")).to_have_count(1)


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
    expect(document.locator("html")).to_have_attribute("data-theme-pack-visual", "")
    assert document.locator("html").evaluate(
        "node => node.style.getPropertyValue('--theme-pack-font-body')"
    ) == "'Kalam', cursive"

    page.locator("[data-theme-selector]").select_option("canonical")
    expect(document.locator("html")).to_have_attribute("data-board-theme", "canonical")
    expect(document.locator("html")).to_have_attribute("data-theme-pack-visual", "")


@pytest.mark.parametrize("theme", VISUAL_THEMES)
@pytest.mark.parametrize(
    ("route", "heading", "content_selector"),
    [
        ("/projects/programs", "Programs", "a.link"),
        (
            "/projects/websites/this_website/v3",
            "DavidLybeck.com Version 3",
            "img.media",
        ),
    ],
)
def test_document_grammar_covers_text_and_media_pages_in_every_world(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
    route: str,
    heading: str,
    content_selector: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}{route}?theme={theme}", wait_until="domcontentloaded")
    page.locator(".mini-window-container.open").wait_for()
    document = page.frame_locator(".mini-window")

    expect(document.locator("html")).to_have_attribute("data-board-theme", theme)
    expect(document.locator("#location")).to_have_text(heading)
    expect(document.locator(content_selector).first).to_be_visible()
    assert document.locator(".section").first.evaluate(
        "node => getComputedStyle(node).backgroundColor"
    ) not in {"rgba(0, 0, 0, 0)", "transparent"}


def test_each_world_has_a_distinct_native_document_grammar(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    signatures = {}
    for theme in VISUAL_THEMES:
        page.goto(
            f"{origin}/projects/websites/this_website/v3?theme={theme}",
            wait_until="domcontentloaded",
        )
        page.locator(".mini-window-container.open").wait_for()
        document = page.frame_locator(".mini-window")
        expect(document.locator("html")).to_have_attribute(
            "data-theme-pack-visual", ""
        )
        signatures[theme] = document.locator(".section").first.evaluate(
            """section => {
                const root = getComputedStyle(document.documentElement);
                const style = getComputedStyle(section);
                const media = document.querySelector('img, video, iframe, model-viewer');
                return [
                    root.backgroundImage,
                    style.backgroundColor,
                    style.borderRadius,
                    style.fontFamily,
                    media ? getComputedStyle(media).borderRadius : '',
                ];
            }"""
        )

    assert len({tuple(signature) for signature in signatures.values()}) == 5


@pytest.mark.parametrize("theme", VISUAL_THEMES)
def test_document_text_and_component_roles_are_owned_by_each_pack(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/projects/programs?theme={theme}", wait_until="domcontentloaded")
    page.locator(".mini-window-container.open").wait_for()
    document = page.frame_locator(".mini-window")

    for selector, property_name, token in (
        ("html", "backgroundColor", "--theme-pack-page-bg"),
        ("#location", "fontFamily", "--theme-pack-font-title"),
        (".section span", "color", "--theme-pack-ink"),
        ("a.link", "color", "--theme-pack-link"),
        (".external-btn", "backgroundColor", "--theme-pack-button-bg"),
        (".section", "borderRadius", "--theme-pack-panel-radius"),
    ):
        assert document.locator(selector).first.evaluate(
            r"""(node, [propertyName, token]) => {
                const root = getComputedStyle(document.documentElement);
                const probe = document.createElement('span');
                const cssProperty = propertyName.replace(
                    /[A-Z]/g,
                    (letter) => `-${letter.toLowerCase()}`
                );
                probe.style.setProperty(
                    cssProperty,
                    root.getPropertyValue(token),
                    'important'
                );
                document.body.appendChild(probe);
                const expected = getComputedStyle(probe)[propertyName];
                probe.remove();
                const actual = getComputedStyle(node)[propertyName];
                const normalize = (value) => propertyName === 'fontFamily'
                    ? value.replace(/["']/g, '').replace(/\s+/g, ' ').toLowerCase()
                    : value;
                return normalize(actual) === normalize(expected);
            }""",
            [property_name, token],
        ), f"{theme} did not apply {token} to {selector}"


@pytest.mark.parametrize("theme", VISUAL_THEMES)
def test_interactive_document_controls_use_the_active_pack(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(
        f"{origin}/projects/nba_predictions?theme={theme}",
        wait_until="domcontentloaded",
    )
    page.locator(".mini-window-container.open").wait_for()
    document = page.frame_locator(".mini-window")

    for selector, token in (
        ("#predictBtn", "--theme-pack-button-bg"),
        ("#team1", "--theme-pack-field-bg"),
        ("#result", "--theme-pack-result-bg"),
    ):
        assert document.locator(selector).evaluate(
            """(node, token) => {
                const actual = getComputedStyle(node).backgroundColor;
                const probe = document.createElement('span');
                probe.style.backgroundColor = getComputedStyle(document.documentElement)
                    .getPropertyValue(token);
                document.body.appendChild(probe);
                const expected = getComputedStyle(probe).backgroundColor;
                probe.remove();
                return actual === expected;
            }""",
            token,
        )


@pytest.mark.parametrize("theme", VISUAL_THEMES)
def test_keyboard_hierarchy_is_unchanged_in_each_world(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme={theme}#Hobbies", wait_until="domcontentloaded")

    names = []
    for _ in range(5):
        page.keyboard.press("Tab")
        names.append(
            page.evaluate(
                "document.activeElement.getAttribute('aria-label')"
                " || document.activeElement.textContent.trim()"
            )
        )
    assert names == [
        "Home",
        "Go to Home",
        "Go to 3D Printing",
        "Go to Gaming",
        "Go to Tennis",
    ]
    page.keyboard.press("Shift+Tab")
    expect(page.get_by_role("button", name="Go to Gaming")).to_be_focused()
    page.keyboard.press("Enter")
    expect(page).to_have_url(f"{origin}/?theme={theme}#Gaming")
    expect(page.get_by_role("link", name="Open Gaming")).to_be_focused()

    page.keyboard.press("Space")
    page.locator(".mini-window-container.open").wait_for()
    expect(page).to_have_url(f"{origin}/hobbies/gaming?theme={theme}")
    page.keyboard.press("Escape")
    expect(page).to_have_url(f"{origin}/?theme={theme}#Gaming")


@pytest.mark.parametrize("theme", VISUAL_THEMES)
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


@pytest.mark.parametrize("page_fixture", ["browser_page", "mobile_browser_page"])
@pytest.mark.parametrize("theme", VISUAL_THEMES)
def test_every_tile_uses_a_fitted_content_safe_area(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
    page_fixture: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = request.getfixturevalue(page_fixture)
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")
    expect(page.locator('[data-theme-content-fit="true"]')).to_have_count(17)

    violations = page.locator(".paper-body[data-theme-content-area]").evaluate_all(
        """bodies => bodies.flatMap((body) => {
            const style = getComputedStyle(body);
            const left = parseFloat(style.paddingLeft);
            const top = parseFloat(style.paddingTop);
            const right = body.clientWidth - parseFloat(style.paddingRight);
            const bottom = body.clientHeight - parseFloat(style.paddingBottom);
            const textNodes = [...body.querySelectorAll(
                '.scrap-title, .expanded-title, .expanded-text, .expanded-open'
            )];
            const textFailures = textNodes.filter((node) =>
                node.offsetLeft < left - 1
                || node.offsetTop < top - 1
                || node.offsetLeft + node.offsetWidth > right + 1
                || node.offsetTop + node.offsetHeight > bottom + 1
                || (node.matches('.expanded-text') && (
                        // Handwriting fonts can report glyph overhang beyond
                        // their line box. Four pixels catches real clipping
                        // without failing on that harmless font metric.
                        node.scrollWidth > node.clientWidth + 4
                        || node.scrollHeight > node.clientHeight + 4
                ))
            ).map((node) => JSON.stringify({
                title: body.closest('.tile-container').dataset.title,
                className: node.className,
                node: [node.offsetLeft, node.offsetTop, node.offsetWidth, node.offsetHeight],
                safe: [left, top, right, bottom],
                scroll: [node.scrollWidth, node.scrollHeight, node.clientWidth, node.clientHeight],
                typography: [getComputedStyle(node).fontSize, getComputedStyle(node).lineHeight, getComputedStyle(node).wordBreak, getComputedStyle(node).whiteSpace],
            }));

            const svg = body.querySelector('[data-theme-size]');
            const marker = svg.querySelector('[data-theme-content-area="content"]');
            const silhouette = svg.querySelector('[data-visual-axis~="silhouette"]');
            if (!silhouette?.isPointInFill) return [...textFailures, 'missing-silhouette'];
            const x = Number(marker.getAttribute('x'));
            const y = Number(marker.getAttribute('y'));
            const width = Number(marker.getAttribute('width'));
            const height = Number(marker.getAttribute('height'));
            const corners = [
                [x + 1, y + 1], [x + width - 1, y + 1],
                [x + 1, y + height - 1], [x + width - 1, y + height - 1],
            ];
            const artFailure = corners.every(([pointX, pointY]) =>
                silhouette.isPointInFill(new DOMPoint(pointX, pointY))
            ) ? [] : [`${body.closest('.tile-container').dataset.title}:safe-area-art`];
            return [...textFailures, ...artFailure];
        })"""
    )
    assert violations == []


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


def test_development_selector_has_an_explicit_keyboard_shortcut(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme=lily", wait_until="domcontentloaded")

    page.keyboard.press("Alt+t")
    selector = page.locator("[data-theme-selector]")
    expect(selector).to_be_focused()
    selector.select_option("clouds")
    expect(page).to_have_url(f"{origin}/?theme=clouds")


@pytest.mark.parametrize("theme", VISUAL_THEMES)
def test_phone_theme_laboratory_keeps_the_personal_mark_visible(
    mobile_browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = mobile_browser_page
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")

    logo = page.locator(".navbar-logo")
    expect(logo).to_be_visible()
    assert logo.evaluate(
        """node => {
            const rect = node.getBoundingClientRect();
            return rect.left >= 0 && rect.right <= innerWidth && rect.height > 0;
        }"""
    )


def test_cloudscape_renders_deterministic_density_underside_and_wisp_axes(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    page.goto(f"{origin}/?theme=clouds", wait_until="domcontentloaded")

    rendered_axes = page.locator('[data-theme-size="base"]').evaluate_all(
        """nodes => nodes.map((node) => ({
            density: node.dataset.variantDensity,
            underside: node.dataset.variantUnderside,
            wisp: node.dataset.variantWisp,
        }))"""
    )
    assert len({axis["density"] for axis in rendered_axes}) >= 3
    assert len({axis["underside"] for axis in rendered_axes}) >= 3
    assert len({axis["wisp"] for axis in rendered_axes}) >= 4


@pytest.mark.parametrize("theme", VISUAL_THEMES)
def test_each_world_reaches_eighty_percent_of_canonical_variant_depth(
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
    theme: str,
) -> None:
    """Rendered worlds must rival the six-axis canonical paper grammar."""
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    page, origin = browser_page
    report = audit_world(page, origin, theme)

    assert report["locations"] == 17
    assert report["axis_count"] >= MINIMUM_AXIS_COUNT
    assert report["visible_evidence_complete"]
    assert all(count >= 2 for count in report["factor_values"].values())
    assert all(count >= 2 for count in report["visible_factor_values"].values())
    assert (
        report["visible_distinct_combinations"]
        >= report["minimum_distinct_combinations"]
    )
    assert report["base_expanded_continuity"]
    assert report["passed"]


@pytest.mark.parametrize("theme", VISUAL_THEMES)
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


@pytest.mark.parametrize("theme", VISUAL_THEMES)
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
