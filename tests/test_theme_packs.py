import json
from pathlib import Path

import pytest

from core.theme_packs import (
    InvalidThemeAsset,
    ThemePackRegistry,
    sanitized_svg_asset,
)


def write_pack(
    root: Path,
    pack_id: str,
    *,
    label: str | None = None,
    enabled: bool = True,
    random_eligible: bool = True,
    extra: dict[str, object] | None = None,
) -> None:
    pack_dir = root / pack_id
    pack_dir.mkdir(parents=True)
    manifest: dict[str, object] = {
        "$schema": "portfolio-theme-pack/v1",
        "id": pack_id,
        "label": label or pack_id.title(),
        "version": 1,
        "selection": {
            "enabled": enabled,
            "randomEligible": random_eligible,
            "randomWeight": 1,
        },
    }
    manifest.update(extra or {})
    (pack_dir / "theme.json").write_text(json.dumps(manifest), encoding="utf-8")


def write_compiled_tiles(root: Path, pack_id: str, *, unsafe: bool = False) -> None:
    pack_dir = root / pack_id
    assets = pack_dir / "assets" / "tiles"
    assets.mkdir(parents=True)
    markup = (
        '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        if unsafe
        else '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><rect data-theme-content-area="content" x="2" y="2" width="6" height="6"/></svg>'
    )
    for state in ("base", "expanded"):
        (assets / f"home-{state}.svg").write_text(markup, encoding="utf-8")
    (pack_dir / "tiles.json").write_text(
        json.dumps(
            {
                "assignments": {
                    "Home": {
                        "base": "assets/tiles/home-base.svg",
                        "expanded": "assets/tiles/home-expanded.svg",
                        "factors": {"silhouette": 0, "palette": 0},
                    }
                }
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

    (tmp_path / "temporary" / "theme.json").unlink()
    (tmp_path / "temporary").rmdir()

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


def test_registry_bundles_validated_compiled_tile_assets(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "rain-garden", extra={"tiles": "tiles.json"})
    write_compiled_tiles(tmp_path, "rain-garden")

    registry = ThemePackRegistry.discover(tmp_path)
    payload = registry.resolve("rain-garden", enabled=True).client_payload()

    assert payload["tiles"]["assignments"]["Home"]["factors"] == {
        "palette": 0,
        "silhouette": 0,
    }
    assert payload["tiles"]["assignments"]["Home"]["baseSvg"].startswith("<svg")
    assert "data-theme-content-area" in payload["tiles"]["assignments"]["Home"][
        "expandedSvg"
    ]


def test_pack_with_unsafe_compiled_asset_is_excluded(tmp_path: Path) -> None:
    write_pack(tmp_path, "canonical", random_eligible=False)
    write_pack(tmp_path, "unsafe", extra={"tiles": "tiles.json"})
    write_compiled_tiles(tmp_path, "unsafe", unsafe=True)

    registry = ThemePackRegistry.discover(tmp_path)

    assert registry.ids == ("canonical",)
    assert registry.diagnostics[0].pack_id == "unsafe"
    assert "not allowed" in registry.diagnostics[0].message


def test_repository_alternate_packs_have_all_compiled_board_assets() -> None:
    registry = ThemePackRegistry.discover()

    for pack_id in ("lily", "planets", "clouds", "islands"):
        payload = registry.resolve(pack_id, enabled=True).client_payload()
        assert len(payload["tiles"]["assignments"]) == 17


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
