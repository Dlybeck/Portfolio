"""Validated discovery for declarative Portfolio Theme Packs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError


THEME_PACK_SCHEMA = "portfolio-theme-pack/v1"
CANONICAL_THEME = "canonical"
DEFAULT_THEME_ROOT = Path(__file__).parent.parent / "static" / "themes"


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)


class ThemeSelection(StrictModel):
    enabled: bool
    random_eligible: bool = Field(alias="randomEligible")
    random_weight: int = Field(alias="randomWeight", ge=1, le=100)


class ThemePackManifest(StrictModel):
    schema_id: Literal[THEME_PACK_SCHEMA] = Field(alias="$schema")
    id: str = Field(pattern=r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$", max_length=48)
    label: str = Field(min_length=1, max_length=64)
    version: Literal[1]
    selection: ThemeSelection


@dataclass(frozen=True, slots=True)
class ThemePackDiagnostic:
    pack_id: str
    message: str


@dataclass(frozen=True, slots=True)
class ThemePackRegistry:
    packs: tuple[ThemePackManifest, ...]
    diagnostics: tuple[ThemePackDiagnostic, ...] = ()

    @classmethod
    def discover(cls, root: Path = DEFAULT_THEME_ROOT) -> "ThemePackRegistry":
        manifests: list[ThemePackManifest] = []
        diagnostics: list[ThemePackDiagnostic] = []
        if root.is_dir():
            for pack_dir in sorted(path for path in root.iterdir() if path.is_dir()):
                manifest_path = pack_dir / "theme.json"
                if not manifest_path.is_file():
                    continue
                try:
                    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
                    manifest = ThemePackManifest.model_validate(raw)
                    if manifest.id != pack_dir.name:
                        raise ValueError(
                            f"manifest id {manifest.id!r} does not match directory "
                            f"{pack_dir.name!r}"
                        )
                    manifests.append(manifest)
                except (OSError, json.JSONDecodeError, ValidationError, ValueError) as error:
                    diagnostics.append(
                        ThemePackDiagnostic(pack_id=pack_dir.name, message=str(error))
                    )

        manifests.sort(key=lambda pack: (pack.id != CANONICAL_THEME, pack.id))
        if not manifests or manifests[0].id != CANONICAL_THEME:
            raise RuntimeError("A valid canonical Theme Pack is required")
        return cls(tuple(manifests), tuple(diagnostics))

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(pack.id for pack in self.packs)

    @property
    def random_candidates(self) -> tuple[ThemePackManifest, ...]:
        return tuple(
            pack
            for pack in self.packs
            if pack.selection.enabled
            and pack.selection.random_eligible
        )

    def resolve(self, requested: str | None, *, enabled: bool) -> ThemePackManifest:
        canonical = self.packs[0]
        if not enabled or not requested:
            return canonical
        selected = next((pack for pack in self.packs if pack.id == requested), None)
        if selected is None or not selected.selection.enabled:
            return canonical
        return selected

    def public_catalog(self) -> tuple[dict[str, str], ...]:
        return tuple(
            {"key": pack.id, "label": pack.label}
            for pack in self.packs
            if pack.selection.enabled
        )
