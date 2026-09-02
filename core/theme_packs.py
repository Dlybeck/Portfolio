"""Validated discovery for declarative Portfolio Theme Packs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
from typing import Any, Literal
from xml.etree import ElementTree

from pydantic import BaseModel, ConfigDict, Field, ValidationError


THEME_PACK_SCHEMA = "portfolio-theme-pack/v1"
CANONICAL_THEME = "canonical"
DEFAULT_THEME_ROOT = Path(__file__).parent.parent / "static" / "themes"
MAX_SVG_BYTES = 256 * 1024

SVG_TAGS = frozenset(
    {
        "circle",
        "clipPath",
        "defs",
        "desc",
        "ellipse",
        "g",
        "line",
        "linearGradient",
        "mask",
        "path",
        "pattern",
        "polygon",
        "polyline",
        "radialGradient",
        "rect",
        "stop",
        "svg",
        "title",
        "use",
    }
)
SVG_ATTRIBUTES = frozenset(
    {
        "aria-hidden",
        "class",
        "clip-path",
        "clipPathUnits",
        "cx",
        "cy",
        "d",
        "fill",
        "fill-opacity",
        "focusable",
        "gradientTransform",
        "gradientUnits",
        "height",
        "href",
        "id",
        "mask",
        "maskUnits",
        "offset",
        "opacity",
        "orient",
        "pathLength",
        "points",
        "preserveAspectRatio",
        "r",
        "role",
        "rx",
        "ry",
        "spreadMethod",
        "stop-color",
        "stop-opacity",
        "stroke",
        "stroke-dasharray",
        "stroke-dashoffset",
        "stroke-linecap",
        "stroke-linejoin",
        "stroke-miterlimit",
        "stroke-opacity",
        "stroke-width",
        "transform",
        "viewBox",
        "width",
        "x",
        "x1",
        "x2",
        "y",
        "y1",
        "y2",
    }
)
LOCAL_URL = re.compile(r"^url\(#[A-Za-z_][A-Za-z0-9_.:-]*\)$")


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
    tiles: str | None = None


class TileAssignment(StrictModel):
    base: str
    expanded: str
    factors: dict[str, int]


class TileCatalog(StrictModel):
    assignments: dict[str, TileAssignment]


class InvalidThemeAsset(ValueError):
    """A Theme Pack asset crossed the declarative safety boundary."""


def _local_name(qualified_name: str) -> str:
    return qualified_name.rsplit("}", 1)[-1]


def sanitized_svg_asset(pack_root: Path, reference: str) -> str:
    """Validate and return one local, declarative SVG Theme Pack asset."""
    if "\\" in reference or "://" in reference:
        raise InvalidThemeAsset("SVG reference must be a local POSIX path")
    relative = PurePosixPath(reference)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise InvalidThemeAsset("SVG reference escapes its Theme Pack")
    if relative.suffix.lower() != ".svg":
        raise InvalidThemeAsset("Theme SVG assets must use the .svg extension")

    root = pack_root.resolve()
    candidate = (root / Path(*relative.parts)).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise InvalidThemeAsset("Theme SVG asset is missing or outside its pack")
    if candidate.stat().st_size > MAX_SVG_BYTES:
        raise InvalidThemeAsset("Theme SVG asset exceeds the 256 KiB limit")

    markup = candidate.read_text(encoding="utf-8")
    if "<!DOCTYPE" in markup.upper() or "<!ENTITY" in markup.upper():
        raise InvalidThemeAsset("Theme SVG assets cannot declare entities")
    try:
        root_element = ElementTree.fromstring(markup)
    except ElementTree.ParseError as error:
        raise InvalidThemeAsset(f"Theme SVG is not well formed: {error}") from error

    if _local_name(root_element.tag) not in {"svg", "g"}:
        raise InvalidThemeAsset("Theme SVG root must be svg or g")
    for element in root_element.iter():
        tag = _local_name(element.tag)
        if tag not in SVG_TAGS:
            raise InvalidThemeAsset(f"Theme SVG element {tag!r} is not allowed")
        for qualified_name, value in element.attrib.items():
            name = _local_name(qualified_name)
            if name.lower().startswith("on"):
                raise InvalidThemeAsset("Theme SVG event handlers are not allowed")
            if name == "style":
                raise InvalidThemeAsset("Theme SVG style attributes are not allowed")
            if (
                not name.startswith(("data-theme-", "data-variant-", "data-visual-"))
                and name not in SVG_ATTRIBUTES
            ):
                raise InvalidThemeAsset(f"Theme SVG attribute {name!r} is not allowed")
            normalized = value.strip().lower()
            if any(
                marker in normalized
                for marker in ("javascript:", "data:", "http:", "https:", "@import", "expression(")
            ):
                raise InvalidThemeAsset("Theme SVG contains an external or executable value")
            if name == "href" and value and not value.startswith("#"):
                raise InvalidThemeAsset("Theme SVG href values must be local fragments")
            if "url(" in normalized and not LOCAL_URL.fullmatch(value.strip()):
                raise InvalidThemeAsset("Theme SVG URL values must be local fragments")
    return markup


@dataclass(frozen=True, slots=True)
class ThemePackDiagnostic:
    pack_id: str
    message: str


@dataclass(frozen=True, slots=True)
class CompiledTileAssignment:
    base_svg: str
    expanded_svg: str
    factors: tuple[tuple[str, int], ...]

    def client_payload(self) -> dict[str, object]:
        return {
            "baseSvg": self.base_svg,
            "expandedSvg": self.expanded_svg,
            "factors": dict(self.factors),
        }


@dataclass(frozen=True, slots=True)
class LoadedThemePack:
    """A complete Theme Pack after every referenced asset has been validated."""

    manifest: ThemePackManifest
    tiles: tuple[tuple[str, CompiledTileAssignment], ...] = ()

    @property
    def id(self) -> str:
        return self.manifest.id

    @property
    def label(self) -> str:
        return self.manifest.label

    @property
    def selection(self) -> ThemeSelection:
        return self.manifest.selection

    def client_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "$schema": self.manifest.schema_id,
            "id": self.id,
            "label": self.label,
            "version": self.manifest.version,
            "selection": self.selection.model_dump(by_alias=True),
        }
        if self.tiles:
            payload["tiles"] = {
                "assignments": {
                    title: assignment.client_payload()
                    for title, assignment in self.tiles
                }
            }
        return payload


def _local_json_asset(pack_root: Path, reference: str) -> Path:
    if "\\" in reference or "://" in reference:
        raise InvalidThemeAsset("JSON reference must be a local POSIX path")
    relative = PurePosixPath(reference)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise InvalidThemeAsset("JSON reference escapes its Theme Pack")
    if relative.suffix.lower() != ".json":
        raise InvalidThemeAsset("Theme data assets must use the .json extension")
    root = pack_root.resolve()
    candidate = (root / Path(*relative.parts)).resolve()
    if not candidate.is_relative_to(root) or not candidate.is_file():
        raise InvalidThemeAsset("Theme data asset is missing or outside its pack")
    return candidate


def _compiled_tiles(pack_root: Path, reference: str | None) -> tuple[tuple[str, CompiledTileAssignment], ...]:
    if reference is None:
        return ()
    catalog_path = _local_json_asset(pack_root, reference)
    try:
        raw = json.loads(catalog_path.read_text(encoding="utf-8"))
        catalog = TileCatalog.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise InvalidThemeAsset(f"invalid tile catalog: {error}") from error
    if not catalog.assignments:
        raise InvalidThemeAsset("tile catalog must contain at least one assignment")
    return tuple(
        (
            title,
            CompiledTileAssignment(
                base_svg=sanitized_svg_asset(pack_root, assignment.base),
                expanded_svg=sanitized_svg_asset(pack_root, assignment.expanded),
                factors=tuple(sorted(assignment.factors.items())),
            ),
        )
        for title, assignment in sorted(catalog.assignments.items())
    )


@dataclass(frozen=True, slots=True)
class ThemePackRegistry:
    packs: tuple[LoadedThemePack, ...]
    diagnostics: tuple[ThemePackDiagnostic, ...] = ()

    @classmethod
    def discover(cls, root: Path = DEFAULT_THEME_ROOT) -> "ThemePackRegistry":
        packs: list[LoadedThemePack] = []
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
                    packs.append(
                        LoadedThemePack(
                            manifest=manifest,
                            tiles=_compiled_tiles(pack_dir, manifest.tiles),
                        )
                    )
                except (
                    OSError,
                    json.JSONDecodeError,
                    ValidationError,
                    ValueError,
                ) as error:
                    diagnostics.append(
                        ThemePackDiagnostic(pack_id=pack_dir.name, message=str(error))
                    )

        packs.sort(key=lambda pack: (pack.id != CANONICAL_THEME, pack.id))
        if not packs or packs[0].id != CANONICAL_THEME:
            raise RuntimeError("A valid canonical Theme Pack is required")
        return cls(tuple(packs), tuple(diagnostics))

    @property
    def ids(self) -> tuple[str, ...]:
        return tuple(pack.id for pack in self.packs)

    @property
    def random_candidates(self) -> tuple[LoadedThemePack, ...]:
        return tuple(
            pack
            for pack in self.packs
            if pack.selection.enabled
            and pack.selection.random_eligible
        )

    def resolve(self, requested: str | None, *, enabled: bool) -> LoadedThemePack:
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
