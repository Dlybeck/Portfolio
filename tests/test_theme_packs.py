import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

import pytest
from playwright.sync_api import Page, expect

from core.config import settings
from core.theme_packs import (
    BOARD_PRESENTATION_TOKENS,
    BOARD_LOCATIONS,
    DOCUMENT_PRESENTATION_TOKENS,
    InvalidThemeAsset,
    ThemePackRegistry,
    load_theme_pack,
    sanitized_svg_asset,
)
from scripts.audit_theme_variants import audit_theme_ids, audit_world
from scripts.capture_theme_matrix import review_theme_ids


BOARD_TITLES = (
    "Home", "Hobbies", "Projects", "Work Experience", "Education",
    "3D Printing", "Gaming", "Tennis", "Other Models", "Puzzles",
    "Programs", "Websites", "Digital Planner", "This website",
    "ScribbleScan", "College", "Early Education",
)


def write_pack(
    root: Path,
    pack_id: str,
    *,
    label: str | None = None,
    enabled: bool = True,
    random_eligible: bool = True,
    complete: bool = True,
    extra: dict[str, object] | None = None,
) -> None:
    pack_dir = root / pack_id
    pack_dir.mkdir(parents=True)
    manifest: dict[str, object] = {
        "$schema": "portfolio-theme-pack/v1",
        "id": pack_id,
        "label": label or pack_id.title(),
        "version": 1,
        **(
            {"tiles": "tiles.json", "presentation": "presentation.json"}
            if complete
            else {}
        ),
        "selection": {
            "enabled": enabled,
            "randomEligible": random_eligible,
            "randomWeight": 1,
        },
    }
    manifest.update(extra or {})
    (pack_dir / "theme.json").write_text(json.dumps(manifest), encoding="utf-8")
    if complete:
        write_compiled_tiles(root, pack_id)
        write_presentation(root, pack_id)


def write_compiled_tiles(
    root: Path,
    pack_id: str,
    *,
    unsafe: bool = False,
    titles: tuple[str, ...] = BOARD_TITLES,
) -> None:
    pack_dir = root / pack_id
    assets = pack_dir / "assets" / "tiles"
    assets.mkdir(parents=True)
    for state in ("base", "expanded"):
        markup = (
            '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
            if unsafe
            else (
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10">'
                f'<circle cx="5" cy="5" r="{1 if state == "base" else 2}"/>'
                '<rect data-theme-content-area="content" x="2" y="2" '
                'width="6" height="6"/></svg>'
            )
        )
        (assets / f"home-{state}.svg").write_text(markup, encoding="utf-8")
    assignments = {
        title: {
            "base": "assets/tiles/home-base.svg",
            "expanded": "assets/tiles/home-expanded.svg",
            "factors": {
                "silhouette": index,
                "palette": index % 3,
                "orientation": index % 9,
                "accent": index % 5,
                "detail": index % 7,
            },
            "transforms": {
                "base": {
                    "rotationDegrees": index % 9 - 4,
                    "offsetXPixels": index % 5 - 2,
                    "offsetYPixels": index % 7 - 3,
                },
                "expanded": {
                    "rotationDegrees": (index * 3) % 9 - 4,
                    "offsetXPixels": (index * 2) % 5 - 2,
                    "offsetYPixels": (index * 3) % 7 - 3,
                },
                "detailRotationDegrees": index % 11 - 5,
            },
            "motion": {
                "durationOffsetMilliseconds": index % 21 - 10,
                "rotationOffsetDegrees": index % 5 - 2,
                "offsetXPixels": index % 3 - 1,
                "offsetYPixels": (index * 2) % 3 - 1,
                "scaleOffset": 0,
            },
        }
        for index, title in enumerate(titles)
    }
    (pack_dir / "tiles.json").write_text(
        json.dumps(
            {"assignments": assignments}
        ),
        encoding="utf-8",
    )


def write_presentation(root: Path, pack_id: str) -> None:
    board = {name: "initial" for name in BOARD_PRESENTATION_TOKENS}
    board["focus-motion"] = "cover"
    (root / pack_id / "presentation.json").write_text(
        json.dumps(
            {
                "board": board,
                "document": {
                    name: "initial" for name in DOCUMENT_PRESENTATION_TOKENS
                },
                "connectors": {
                    "color": "currentColor",
                    "strokeWidth": 2,
                    "opacity": 1,
                    "headStyle": "none",
                    "headPosition": "none",
                    "headLen": 0,
                    "headHalf": 0,
                    "wobble": 0,
                    "lineCap": "round",
                    "dashPattern": "none",
                    "curveStyle": "straight",
                    "texture": "none",
                    "textureColor": "currentColor",
                    "haloWidth": 1,
                    "haloOpacity": 0,
                    "insetFactor": 9,
                    "variation": {
                        "strokeWidth": 0,
                        "wobble": 0,
                        "dash": 0,
                        "opacity": 0,
                        "markerScale": 0,
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def test_registry_discovers_a_pack_from_files_only(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", label="Original", random_eligible=False)
    write_pack(tmp_path, "rain-garden", label="Rain Garden")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical", "rain-garden")
    assert registry.resolve("rain-garden", enabled=True).id == "rain-garden"
    assert registry.public_catalog() == (
        {"key": "canonical", "label": "Original"},
        {"key": "rain-garden", "label": "Rain Garden"},
    )
    assert registry.diagnostics == ()


def test_registry_removes_a_pack_when_its_directory_is_removed(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "temporary")
    assert ThemePackRegistry.discover(tmp_path).ids == ("canonical", "temporary")

    shutil.rmtree(tmp_path / "temporary")

    assert ThemePackRegistry.discover(tmp_path).ids == ("canonical",)


def test_invalid_pack_is_excluded_with_actionable_diagnostic(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "valid")
    write_pack(tmp_path, "wrong-directory", extra={"id": "different-id"})
    write_pack(tmp_path, "unknown-field", extra={"surprise": "ignored?"})

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical", "valid")
    assert {diagnostic.pack_id for diagnostic in registry.diagnostics} == {
        "unknown-field",
        "wrong-directory",
    }
    assert all(diagnostic.message for diagnostic in registry.diagnostics)


def test_pack_rejects_an_unknown_focus_motion_preset(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    presentation_path = tmp_path / "canonical" / "presentation.json"
    presentation = json.loads(presentation_path.read_text(encoding="utf-8"))
    presentation["board"]["focus-motion"] = "camera-zoom"
    presentation_path.write_text(json.dumps(presentation), encoding="utf-8")

    with pytest.raises(
        InvalidThemeAsset,
        match="must be cover, grow, or settle",
    ):
        load_theme_pack(tmp_path / "canonical")


def test_resolution_fails_closed_to_canonical(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "disabled", enabled=False)
    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.resolve("missing", enabled=True).id == "canonical"
    assert registry.resolve("disabled", enabled=True).id == "canonical"
    assert registry.resolve("disabled", enabled=False).id == "canonical"


def test_random_candidates_exclude_canonical_disabled_and_ineligible(
    tmp_path: Path,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "lily", random_eligible=True)
    write_pack(tmp_path, "draft", enabled=False)
    write_pack(tmp_path, "manual-only", random_eligible=False)

    registry = ThemePackRegistry.discover(tmp_path)

    assert tuple(pack.id for pack in registry.random_candidates) == ("lily",)


def test_unpinned_selection_is_weighted_while_an_explicit_pin_is_stable(
    tmp_path: Path,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "first", extra={"selection": {
        "enabled": True, "randomEligible": True, "randomWeight": 1,
    }})
    write_pack(tmp_path, "second", extra={"selection": {
        "enabled": True, "randomEligible": True, "randomWeight": 3,
    }})
    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.select_for_request(None, enabled=True, ticket=0).id == "first"
    assert registry.select_for_request(None, enabled=True, ticket=1).id == "second"
    assert registry.select_for_request(None, enabled=True, ticket=3).id == "second"
    assert (
        registry.select_for_request(
            None, enabled=True, ticket=0, exclude_id="first"
        ).id
        == "second"
    )
    assert registry.select_for_request("first", enabled=True, ticket=3).id == "first"
    assert registry.select_for_request(None, enabled=False, ticket=1).id == "canonical"


def test_repository_theme_catalog_is_discovered_from_pack_directories() -> None:
    registry = ThemePackRegistry.discover()

    assert registry.ids == (
        "canonical",
        "clouds",
        "islands",
        "lily",
        "planets",
    )
    assert registry.diagnostics == ()


def test_authoring_audits_discover_every_enabled_pack_from_the_registry() -> None:
    registry = ThemePackRegistry.discover()
    enabled_ids = tuple(
        pack.id for pack in registry.packs if pack.selection.enabled
    )

    assert audit_theme_ids(registry) == enabled_ids
    assert review_theme_ids(registry) == enabled_ids
    assert "clouds" not in enabled_ids


def test_machine_schemas_publish_the_exact_runtime_contract() -> None:
    root = Path(__file__).parent.parent
    schema_root = root / "schemas" / "theme-pack-v1"
    theme = json.loads(
        (schema_root / "theme.schema.json").read_text(encoding="utf-8")
    )
    presentation = json.loads(
        (schema_root / "presentation.schema.json").read_text(encoding="utf-8")
    )
    tiles = json.loads(
        (schema_root / "tiles.schema.json").read_text(encoding="utf-8")
    )

    assert set(presentation["properties"]["board"]["required"]) == BOARD_PRESENTATION_TOKENS
    assert set(presentation["properties"]["document"]["required"]) == DOCUMENT_PRESENTATION_TOKENS
    assert "variation" in presentation["properties"]["connectors"]["required"]
    assert set(tiles["properties"]["assignments"]["required"]) == BOARD_LOCATIONS
    assignment = tiles["properties"]["assignments"]["properties"]["Home"]
    assert {"transforms", "motion"} <= set(assignment["required"])
    background = theme["properties"]["background"]
    assert background["type"] == "array"
    assert background["maxItems"] == 4
    assert background["items"]["properties"]["depth"] == {
        "type": "number", "minimum": 0, "maximum": 1,
    }


def test_pack_background_layers_are_ordered_sanitized_and_bounded(
    tmp_path: Path,
) -> None:
    write_pack(
        tmp_path,
        "canonical",
        random_eligible=False,
        extra={"background": [
            {"asset": "assets/far.svg", "depth": 0.05},
            {"asset": "assets/near.svg", "depth": 0.2},
        ]},
    )
    assets = tmp_path / "canonical" / "assets"
    assets.mkdir(exist_ok=True)
    (assets / "far.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><circle cx="1" cy="1" r="1"/></svg>',
        encoding="utf-8",
    )
    (assets / "near.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0L2 2"/></svg>',
        encoding="utf-8",
    )

    payload = load_theme_pack(tmp_path / "canonical").client_payload()

    assert [layer["depth"] for layer in payload["backgroundLayers"]] == [0.05, 0.2]
    assert "<circle" in payload["backgroundLayers"][0]["svg"]
    assert "<path" in payload["backgroundLayers"][1]["svg"]


@pytest.mark.parametrize(
    "background",
    [
        [{"asset": "assets/layer.svg", "depth": -0.01}],
        [{"asset": "assets/layer.svg", "depth": 1.01}],
        [{"asset": "assets/layer.svg", "depth": 0.2}] * 5,
    ],
)
def test_pack_rejects_unbounded_or_excessive_depth_layers(
    tmp_path: Path,
    background: list[dict[str, object]],
) -> None:
    write_pack(
        tmp_path,
        "canonical",
        random_eligible=False,
        extra={"background": background},
    )

    with pytest.raises(InvalidThemeAsset, match="invalid Theme Pack manifest"):
        load_theme_pack(tmp_path / "canonical")


def test_scaffolded_pack_validates_without_engine_source_changes(tmp_path: Path) -> None:
    root = Path(__file__).parent.parent
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "scaffold_theme_pack.py"),
            "fixture-world",
            "Fixture World",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    result = subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "validate_theme_pack.py"),
            str(tmp_path / "fixture-world"),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    receipt = json.loads(result.stdout)

    assert receipt["valid"] is True
    assert receipt["id"] == "fixture-world"
    assert receipt["tileCount"] == len(BOARD_LOCATIONS)
    assert load_theme_pack(tmp_path / "fixture-world").id == "fixture-world"


def test_scaffolded_pack_passes_the_rendered_variation_baseline(
    tmp_path: Path,
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    root = Path(__file__).parent.parent
    write_pack(tmp_path, "canonical", random_eligible=False)
    subprocess.run(
        [
            sys.executable,
            str(root / "scripts" / "scaffold_theme_pack.py"),
            "fixture-world",
            "Fixture World",
            str(tmp_path),
        ],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
    )
    registry = ThemePackRegistry.discover(tmp_path)
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    monkeypatch.setattr(
        ThemePackRegistry,
        "discover",
        classmethod(lambda cls, root=None: registry),
    )
    page, origin = browser_page

    report = audit_world(page, origin, "fixture-world")

    assert report["locations"] == len(BOARD_LOCATIONS)
    assert report["axis_count"] == 6
    assert report["base_expanded_continuity"] is True
    assert report["visible_evidence_complete"] is True
    assert report["passed"] is True


def test_registry_bundles_validated_compiled_tile_assets(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "rain-garden",
        complete=False,
        extra={"tiles": "tiles.json", "presentation": "presentation.json"},
    )
    write_compiled_tiles(tmp_path, "rain-garden")
    write_presentation(tmp_path, "rain-garden")

    registry = ThemePackRegistry.discover(tmp_path)
    payload = registry.resolve("rain-garden", enabled=True).client_payload()

    assert payload["tiles"]["assignments"]["Home"]["factors"] == {
        "accent": 0,
        "detail": 0,
        "orientation": 0,
        "palette": 0,
        "silhouette": 0,
    }
    assert payload["tiles"]["assignments"]["Home"]["baseSvg"].startswith("<svg")
    assert "data-theme-content-area" in payload["tiles"]["assignments"]["Home"][
        "expandedSvg"
    ]


def test_pack_with_unsafe_compiled_asset_is_excluded(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "unsafe",
        complete=False,
        extra={"tiles": "tiles.json", "presentation": "presentation.json"},
    )
    write_compiled_tiles(tmp_path, "unsafe", unsafe=True)
    write_presentation(tmp_path, "unsafe")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert registry.diagnostics[0].pack_id == "unsafe"
    assert "not allowed" in registry.diagnostics[0].message


def test_pack_without_a_tile_content_safe_area_is_excluded(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "unsafe",
        complete=False,
        extra={"tiles": "tiles.json", "presentation": "presentation.json"},
    )
    write_compiled_tiles(tmp_path, "unsafe")
    write_presentation(tmp_path, "unsafe")
    (tmp_path / "unsafe" / "assets" / "tiles" / "home-base.svg").write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect width="10" height="10"/></svg>',
        encoding="utf-8",
    )

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert "content-safe area" in registry.diagnostics[0].message


@pytest.mark.parametrize(
    "markup",
    [
        '<g xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect data-theme-content-area="content" x="2" y="2" width="6" height="6"/></g>',
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 nan 10"><rect data-theme-content-area="content" x="2" y="2" width="6" height="6"/></svg>',
    ],
)
def test_compiled_tile_rejects_renderer_incompatible_geometry(
    tmp_path: Path,
    markup: str,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "unsafe")
    (tmp_path / "unsafe" / "assets" / "tiles" / "home-base.svg").write_text(
        markup,
        encoding="utf-8",
    )

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert registry.diagnostics[0].pack_id == "unsafe"


@pytest.mark.parametrize("factors", [{}, {"bad axis": 1}])
def test_compiled_tile_rejects_missing_or_invalid_variation_axes(
    tmp_path: Path,
    factors: dict[str, int],
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "unsafe")
    path = tmp_path / "unsafe" / "tiles.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    catalog["assignments"]["Home"]["factors"] = factors
    path.write_text(json.dumps(catalog), encoding="utf-8")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert registry.diagnostics[0].pack_id == "unsafe"


def test_compiled_tiles_require_real_variation_and_expansion_detail(
    tmp_path: Path,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "flat-world")
    catalog_path = tmp_path / "flat-world" / "tiles.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for assignment in catalog["assignments"].values():
        assignment["factors"]["detail"] = 0
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert "does not vary" in registry.diagnostics[0].message

    shutil.rmtree(tmp_path / "flat-world")
    write_pack(tmp_path, "flat-world")
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    for assignment in catalog["assignments"].values():
        assignment["expanded"] = assignment["base"]
    catalog_path.write_text(json.dumps(catalog), encoding="utf-8")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert "distinct base and expanded artwork" in registry.diagnostics[0].message


def test_visual_pack_missing_a_board_location_is_excluded(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "incomplete",
        complete=False,
        extra={"tiles": "tiles.json", "presentation": "presentation.json"},
    )
    write_compiled_tiles(tmp_path, "incomplete", titles=("Home",))
    write_presentation(tmp_path, "incomplete")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert "missing=" in registry.diagnostics[0].message


def test_every_repository_pack_has_the_complete_visual_contract() -> None:
    registry = ThemePackRegistry.discover()

    for pack_id in ("canonical", "lily", "planets", "clouds", "islands"):
        payload = registry.resolve(pack_id, enabled=True).client_payload()
        assert len(payload["tiles"]["assignments"]) == 17
        assert set(payload["variables"]["board"]) == BOARD_PRESENTATION_TOKENS
        assert set(payload["variables"]["document"]) == DOCUMENT_PRESENTATION_TOKENS
        assert payload["connectors"]["color"]
        assert "variation" in payload["connectors"]
        assert all(
            {"transforms", "motion"} <= set(assignment)
            for assignment in payload["tiles"]["assignments"].values()
        )


def test_repository_selection_excludes_disabled_cloudscape() -> None:
    registry = ThemePackRegistry.discover()

    assert registry.resolve("clouds", enabled=True).id == "canonical"
    assert "clouds" not in {pack.id for pack in registry.random_candidates}
    assert "clouds" not in {entry["key"] for entry in registry.public_catalog()}


def test_repository_background_art_is_pack_owned_and_irregular() -> None:
    registry = ThemePackRegistry.discover()
    payloads = {
        pack_id: registry.resolve(pack_id, enabled=True).client_payload()
        for pack_id in ("canonical", "planets", "islands", "lily")
    }

    assert "feTurbulence" in payloads["canonical"]["backgroundLayers"][0]["svg"]
    assert [
        layer["depth"] for layer in payloads["canonical"]["backgroundLayers"]
    ] == [1.0]
    planet_layers = payloads["planets"]["backgroundLayers"]
    assert [layer["depth"] for layer in planet_layers] == [0.10, 0.28]
    assert [layer["svg"].count("<circle") for layer in planet_layers] == [346, 174]
    assert sum(layer["svg"].count("<circle") for layer in planet_layers) == 520
    assert all("<pattern" not in layer["svg"] for layer in planet_layers)
    assert payloads["islands"]["backgroundLayers"][0]["svg"].count("<path") == 46
    assert [
        layer["depth"] for layer in payloads["islands"]["backgroundLayers"]
    ] == [1.0]
    lily = payloads["lily"]["backgroundLayers"][0]["svg"]
    assert lily.count("<ellipse") == 72
    assert "<pattern" not in lily
    assert [layer["depth"] for layer in payloads["lily"]["backgroundLayers"]] == [1.0]


def test_depth_runtime_contains_no_installed_theme_names() -> None:
    root = Path(__file__).parent.parent
    runtime = "\n".join(
        (root / path).read_text(encoding="utf-8")
        for path in (
            "static/scripts/themeEngine.js",
            "static/scripts/tileMovement.js",
            "static/css/theme-structure.css",
        )
    ).lower()

    for pack_id in ThemePackRegistry.discover().ids:
        assert pack_id not in runtime


def test_visual_pack_cannot_install_only_half_of_its_visual_language(
    tmp_path: Path,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "half-pack",
        complete=False,
        extra={"tiles": "tiles.json"},
    )
    write_compiled_tiles(tmp_path, "half-pack")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert "presentation" in registry.diagnostics[0].message


def test_manifest_only_pack_is_rejected_instead_of_partially_applying(
    tmp_path: Path,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "empty-world", complete=False)

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert registry.diagnostics[0].pack_id == "empty-world"
    assert "tiles" in registry.diagnostics[0].message
    assert "presentation" in registry.diagnostics[0].message


def test_presentation_rejects_executable_css_values(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "unsafe",
        complete=False,
        extra={"tiles": "tiles.json", "presentation": "presentation.json"},
    )
    write_compiled_tiles(tmp_path, "unsafe")
    write_presentation(tmp_path, "unsafe")
    path = tmp_path / "unsafe" / "presentation.json"
    presentation = json.loads(path.read_text(encoding="utf-8"))
    presentation["board"]["board-bg-image"] = "url(javascript:alert(1))"
    path.write_text(json.dumps(presentation), encoding="utf-8")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert "unsafe CSS" in registry.diagnostics[0].message


@pytest.mark.parametrize(
    "unsafe_value",
    ["red/* swallow following tokens", "red\nbackground: blue"],
)
def test_presentation_rejects_values_that_can_corrupt_following_tokens(
    tmp_path: Path,
    unsafe_value: str,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "unsafe")
    path = tmp_path / "unsafe" / "presentation.json"
    presentation = json.loads(path.read_text(encoding="utf-8"))
    presentation["board"]["ink"] = unsafe_value
    path.write_text(json.dumps(presentation), encoding="utf-8")

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert registry.diagnostics[0].pack_id == "unsafe"


def test_theme_engine_contains_no_installed_world_names_or_drawing_grammar() -> None:
    root = Path(__file__).parent.parent
    engine = (root / "static" / "scripts" / "themeEngine.js").read_text(
        encoding="utf-8"
    ).lower()
    shared_css = "\n".join(
        (root / "static" / "css" / "themes" / name).read_text(encoding="utf-8")
        for name in ("board.css", "documents.css")
    ).lower()

    for world in ("canonical", "lily", "planets", "clouds", "islands"):
        assert world not in engine
        assert world not in shared_css
    for implementation_detail in ("themeadapters", "silhouettes", "palettes"):
        assert implementation_detail not in engine


def test_shared_structure_has_no_world_palette_and_delegates_motion_style() -> None:
    root = Path(__file__).parent.parent
    structure = "\n".join(
        (root / "static" / "css" / name).read_text(encoding="utf-8")
        for name in ("theme-structure.css", "document-structure.css")
    )

    assert re.search(r"#[0-9a-fA-F]{3,8}|rgba?\(|hsla?\(", structure) is None
    for token in (
        "--theme-pack-navigation-transition-easing",
        "--theme-pack-cover-enter-rotation",
        "--theme-pack-cover-exit-scale",
        "--theme-pack-viewer-enter-rotation",
        "--theme-pack-viewer-exit-rotation",
        "--theme-pack-home-hover-transform",
        "--theme-pack-control-hover-transform",
    ):
        assert token in structure


def test_content_templates_cannot_reintroduce_legacy_theme_stylesheets() -> None:
    root = Path(__file__).parent.parent
    forbidden = (
        "/static/css/base.css",
        "/static/css/page.css",
        "/static/css/map.css",
    )

    for template in (root / "templates" / "pages").rglob("*.html"):
        source = template.read_text(encoding="utf-8")
        if template.name == "home.html":
            assert source.count("/static/css/map.css") == 1
            assert "{% if not theme_engine_enabled %}" in source
            source = source.replace("/static/css/map.css", "")
        for legacy_stylesheet in forbidden:
            assert legacy_stylesheet not in source, (
                f"{template.relative_to(root)} bypasses the Theme Pack shell with "
                f"{legacy_stylesheet}"
            )


def test_every_portfolio_page_inherits_one_of_the_themed_shells() -> None:
    root = Path(__file__).parent.parent

    for template in (root / "templates" / "pages").rglob("*.html"):
        source = template.read_text(encoding="utf-8")
        expected_shell = (
            '{% extends "shared/base.html" %}'
            if template.name == "home.html"
            else '{% extends "shared/page.html" %}'
        )
        assert source.startswith(expected_shell), (
            f"{template.relative_to(root)} bypasses the themed shell"
        )


def test_stable_styles_consume_every_published_presentation_token() -> None:
    root = Path(__file__).parent.parent

    def referenced_tokens(*paths: str) -> set[str]:
        source = "\n".join(
            (root / "static" / "css" / path).read_text(encoding="utf-8")
            for path in paths
        )
        return set(re.findall(r"--theme-pack-([a-z0-9-]+)", source))

    assert referenced_tokens(
        "theme-structure.css", "themes/board.css"
    ) == BOARD_PRESENTATION_TOKENS - {"focus-motion"}
    theme_engine = (
        root / "static" / "scripts" / "themeEngine.js"
    ).read_text(encoding="utf-8")
    assert 'pack.variables.board["focus-motion"]' in theme_engine
    assert referenced_tokens(
        "document-structure.css", "themes/documents.css"
    ) == DOCUMENT_PRESENTATION_TOKENS


def test_files_only_fixture_pack_renders_without_engine_changes(
    tmp_path: Path,
    browser_page: tuple[Page, str],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(
        tmp_path,
        "fixture-world",
        label="Fixture World",
        complete=False,
        extra={"tiles": "tiles.json", "presentation": "presentation.json"},
    )
    write_compiled_tiles(tmp_path, "fixture-world", titles=BOARD_TITLES)
    write_presentation(tmp_path, "fixture-world")
    registry = ThemePackRegistry.discover(tmp_path)
    monkeypatch.setattr(settings, "THEME_LAB_ENABLED", True)
    monkeypatch.setattr(
        ThemePackRegistry,
        "discover",
        classmethod(lambda cls, root=None: registry),
    )
    page, origin = browser_page

    page.goto(f"{origin}/?theme=fixture-world", wait_until="domcontentloaded")

    expect(page.locator("html")).to_have_attribute(
        "data-board-theme", "fixture-world"
    )
    expect(page.locator('[data-theme-object="fixture-world"]')).to_have_count(34)
    expect(page.locator("[data-theme-selector]")).to_have_value("fixture-world")
    assert page.locator("html").evaluate(
        "node => node.style.getPropertyValue('--theme-pack-font-navbar')"
    ) == "initial"


def test_svg_asset_accepts_declarative_slots_and_local_references(
    tmp_path: Path,
) -> None:
    asset = tmp_path / "assets" / "tiles" / "base.svg"
    asset.parent.mkdir(parents=True)
    asset.write_text(
        """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 160">
        <defs><clipPath id="shape"><path d="M0 0H200V160H0Z"/></clipPath></defs>
        <g clip-path="url(#shape)" data-theme-slot="silhouette">
          <path d="M10 10H190V150H10Z" fill="var(--tile-mid)"/>
          <rect data-theme-content-area="title" x="40" y="50" width="120" height="60"/>
        </g></svg>""",
        encoding="utf-8",
    )

    markup = sanitized_svg_asset(tmp_path, "assets/tiles/base.svg")

    assert 'data-theme-slot="silhouette"' in markup
    assert 'data-theme-content-area="title"' in markup


@pytest.mark.parametrize(
    "reference",
    ["../outside.svg", "/absolute.svg", "https://example.com/tile.svg"],
)
def test_svg_asset_rejects_paths_outside_the_pack(
    tmp_path: Path,
    reference: str,
) -> None:
    with pytest.raises(InvalidThemeAsset):
        sanitized_svg_asset(tmp_path, reference)


@pytest.mark.parametrize(
    "markup",
    [
        '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><foreignObject/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>',
        '<svg xmlns="http://www.w3.org/2000/svg"><use href="https://example.com/x.svg#x"/></svg>',
        '<svg xmlns="http://www.w3.org/2000/svg"><path style="fill:red"/></svg>',
        '<?xml-stylesheet href="https://example.com/theme.css"?><svg xmlns="http://www.w3.org/2000/svg"/>',
    ],
)
def test_svg_asset_rejects_executable_or_unbounded_markup(
    tmp_path: Path,
    markup: str,
) -> None:
    asset = tmp_path / "unsafe.svg"
    asset.write_text(markup, encoding="utf-8")

    with pytest.raises(InvalidThemeAsset):
        sanitized_svg_asset(tmp_path, "unsafe.svg")
