import json
from pathlib import Path

from core.theme_packs import ThemePackRegistry


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
