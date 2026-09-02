"""Validated discovery for declarative Portfolio Theme Packs."""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from pathlib import PurePosixPath
import re
import secrets
from typing import Any, Literal
from xml.etree import ElementTree

from pydantic import BaseModel, ConfigDict, Field, ValidationError


THEME_PACK_SCHEMA = "portfolio-theme-pack/v1"
CANONICAL_THEME = "canonical"
DEFAULT_THEME_ROOT = Path(__file__).parent.parent / "static" / "themes"
MAX_SVG_BYTES = 256 * 1024
MAX_THEME_VALUE_LENGTH = 500
BOARD_PRESENTATION_TOKENS = frozenset(
    {
        "action-radius", "action-size", "ambient-after-bottom",
        "ambient-after-right", "ambient-after-transform", "ambient-before-left",
        "ambient-before-top", "ambient-before-transform", "ambient-bg",
        "ambient-mark-bg", "ambient-mark-border", "ambient-mark-border-color",
        "ambient-mark-filter", "ambient-mark-height", "ambient-mark-radius",
        "ambient-mark-width", "base-title-size", "board-bg-color",
        "board-bg-image", "board-bg-size", "expanded-text-size",
        "expanded-title-size", "focus", "font-action", "font-base-title",
        "font-expanded-text", "font-expanded-title", "font-navbar", "ink",
        "link", "link-bg", "nav-bg", "nav-border", "nav-ink",
        "nav-logo-filter", "nav-logo-radius", "nav-radius", "nav-shadow",
        "phone-expanded-text-size", "text-shadow", "tile-hover-shadow",
        "tile-shadow", "viewer-bg", "viewer-border", "viewer-bg-image",
        "viewer-radius", "viewer-shadow", "viewer-rotation", "viewer-padding",
        "selector-bg", "selector-border", "selector-ink", "selector-radius",
        "control-bg", "control-border", "control-ink", "control-radius",
        "control-shadow", "control-font", "control-icon-filter",
        "action-transform", "hover-scale", "tile-transition-duration",
        "cover-enter-duration", "cover-exit-duration", "viewer-enter-duration",
        "viewer-exit-duration",
        "ambient-display", "tape-display", "chrome-decoration-display",
        "title-underline-display",
    }
)
DOCUMENT_PRESENTATION_TOKENS = frozenset(
    {
        "body-size", "button-bg", "button-border", "button-ink",
        "button-radius", "code-bg", "focus", "font-body", "font-code",
        "font-heading", "font-link", "font-title", "header-bg", "header-ink",
        "heading-size", "ink", "link", "media-bg", "media-border",
        "media-radius", "page-bg", "page-bg-image", "page-bg-size",
        "panel-bg", "panel-border", "panel-border-style", "panel-radius",
        "panel-shadow", "secondary-ink", "separator", "separator-display",
        "title-size",
    }
)

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
    presentation: str | None = None


class TileAssignment(StrictModel):
    base: str
    expanded: str
    factors: dict[str, int]
    rotation_degrees: float = Field(alias="rotationDegrees", ge=-45, le=45)


class TileCatalog(StrictModel):
    assignments: dict[str, TileAssignment]


class ConnectorPresentation(StrictModel):
    color: str
    stroke_width: float = Field(alias="strokeWidth", ge=0.5, le=12)
    opacity: float = Field(ge=0, le=1)
    head_style: Literal["none", "open", "closed"] = Field(alias="headStyle")
    head_position: Literal["none", "start", "end", "both"] = Field(alias="headPosition")
    head_len: float = Field(alias="headLen", ge=0, le=40)
    head_half: float = Field(alias="headHalf", ge=0, le=30)
    wobble: float = Field(ge=0, le=0.5)


class ThemePresentation(StrictModel):
    board: dict[str, str | int | float]
    document: dict[str, str | int | float]
    connectors: ConnectorPresentation


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


def _compiled_tile_svg(pack_root: Path, reference: str) -> str:
    markup = sanitized_svg_asset(pack_root, reference)
    root = ElementTree.fromstring(markup)
    view_box = root.attrib.get("viewBox", "").split()
    if len(view_box) != 4:
        raise InvalidThemeAsset("compiled tile SVG must declare a four-number viewBox")
    try:
        view_x, view_y, view_width, view_height = map(float, view_box)
    except ValueError as error:
        raise InvalidThemeAsset("compiled tile SVG viewBox is invalid") from error
    markers = [
        element
        for element in root.iter()
        if element.attrib.get("data-theme-content-area") == "content"
    ]
    if len(markers) != 1 or _local_name(markers[0].tag) != "rect":
        raise InvalidThemeAsset(
            "compiled tile SVG must contain exactly one rectangular content-safe area"
        )
    try:
        x, y, width, height = (
            float(markers[0].attrib[name])
            for name in ("x", "y", "width", "height")
        )
    except (KeyError, ValueError) as error:
        raise InvalidThemeAsset("compiled tile content-safe area is invalid") from error
    if (
        view_width <= 0
        or view_height <= 0
        or x < view_x
        or y < view_y
        or width <= 0
        or height <= 0
        or x + width > view_x + view_width
        or y + height > view_y + view_height
    ):
        raise InvalidThemeAsset("compiled tile content-safe area leaves its viewBox")
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
    rotation_degrees: float

    def client_payload(self) -> dict[str, object]:
        return {
            "baseSvg": self.base_svg,
            "expandedSvg": self.expanded_svg,
            "factors": dict(self.factors),
            "rotation": self.rotation_degrees,
        }


@dataclass(frozen=True, slots=True)
class LoadedThemePack:
    """A complete Theme Pack after every referenced asset has been validated."""

    manifest: ThemePackManifest
    tiles: tuple[tuple[str, CompiledTileAssignment], ...] = ()
    board_variables: tuple[tuple[str, str], ...] = ()
    document_variables: tuple[tuple[str, str], ...] = ()
    connectors: ConnectorPresentation | None = None

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
        if self.board_variables or self.document_variables:
            payload["variables"] = {
                "board": dict(self.board_variables),
                "document": dict(self.document_variables),
            }
        if self.connectors:
            payload["connectors"] = self.connectors.model_dump(by_alias=True)
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
                base_svg=_compiled_tile_svg(pack_root, assignment.base),
                expanded_svg=_compiled_tile_svg(pack_root, assignment.expanded),
                factors=tuple(sorted(assignment.factors.items())),
                rotation_degrees=assignment.rotation_degrees,
            ),
        )
        for title, assignment in sorted(catalog.assignments.items())
    )


def _safe_theme_value(name: str, value: str | int | float) -> str:
    if not re.fullmatch(r"[a-z][a-z0-9-]{0,63}", name):
        raise InvalidThemeAsset(f"invalid presentation token {name!r}")
    rendered = str(value)
    normalized = rendered.lower()
    if len(rendered) > MAX_THEME_VALUE_LENGTH:
        raise InvalidThemeAsset(f"presentation token {name!r} is too long")
    if any(marker in normalized for marker in (";", "{", "}", "<", ">", "url(", "javascript:", "expression(", "@import")):
        raise InvalidThemeAsset(f"presentation token {name!r} contains unsafe CSS")
    return rendered


def _presentation(
    pack_root: Path,
    reference: str | None,
) -> tuple[tuple[tuple[str, str], ...], tuple[tuple[str, str], ...], ConnectorPresentation | None]:
    if reference is None:
        return (), (), None
    path = _local_json_asset(pack_root, reference)
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
        presentation = ThemePresentation.model_validate(raw)
    except (OSError, json.JSONDecodeError, ValidationError) as error:
        raise InvalidThemeAsset(f"invalid presentation data: {error}") from error
    board = tuple(
        (name, _safe_theme_value(name, value))
        for name, value in sorted(presentation.board.items())
    )
    document = tuple(
        (name, _safe_theme_value(name, value))
        for name, value in sorted(presentation.document.items())
    )
    if not board or not document:
        raise InvalidThemeAsset("presentation must define Board and Document tokens")
    board_names = {name for name, _ in board}
    document_names = {name for name, _ in document}
    if board_names != BOARD_PRESENTATION_TOKENS:
        missing = sorted(BOARD_PRESENTATION_TOKENS - board_names)
        unknown = sorted(board_names - BOARD_PRESENTATION_TOKENS)
        raise InvalidThemeAsset(
            f"Board presentation tokens mismatch; missing={missing}, unknown={unknown}"
        )
    if document_names != DOCUMENT_PRESENTATION_TOKENS:
        missing = sorted(DOCUMENT_PRESENTATION_TOKENS - document_names)
        unknown = sorted(document_names - DOCUMENT_PRESENTATION_TOKENS)
        raise InvalidThemeAsset(
            f"Document presentation tokens mismatch; missing={missing}, unknown={unknown}"
        )
    return board, document, presentation.connectors


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
                    if bool(manifest.tiles) != bool(manifest.presentation):
                        raise InvalidThemeAsset(
                            "a visual Theme Pack must declare both tiles and presentation"
                        )
                    board_variables, document_variables, connectors = _presentation(
                        pack_dir, manifest.presentation
                    )
                    packs.append(
                        LoadedThemePack(
                            manifest=manifest,
                            tiles=_compiled_tiles(pack_dir, manifest.tiles),
                            board_variables=board_variables,
                            document_variables=document_variables,
                            connectors=connectors,
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

    def select_for_request(
        self,
        requested: str | None,
        *,
        enabled: bool,
        ticket: int | None = None,
        exclude_id: str | None = None,
    ) -> LoadedThemePack:
        """Resolve a pin or choose one weighted pack for an unpinned load."""
        if not enabled or requested is not None:
            return self.resolve(requested, enabled=enabled)
        candidates = self.random_candidates
        if exclude_id and len(candidates) > 1:
            candidates = tuple(pack for pack in candidates if pack.id != exclude_id)
        if not candidates:
            return self.packs[0]
        total = sum(pack.selection.random_weight for pack in candidates)
        cursor = secrets.randbelow(total) if ticket is None else ticket % total
        for pack in candidates:
            cursor -= pack.selection.random_weight
            if cursor < 0:
                return pack
        return candidates[-1]

    def public_catalog(self) -> tuple[dict[str, str], ...]:
        return tuple(
            {"key": pack.id, "label": pack.label}
            for pack in self.packs
            if pack.selection.enabled
        )
