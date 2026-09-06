#!/usr/bin/env python3
"""Export the machine-readable, multi-file Theme Pack v1 contract."""

from __future__ import annotations

import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.theme_packs import (
    BOARD_LOCATIONS,
    BOARD_PRESENTATION_TOKENS,
    DOCUMENT_PRESENTATION_TOKENS,
    MIN_VARIATION_AXIS_COUNT,
    THEME_PACK_SCHEMA,
    TileReveal,
)


OUTPUT = ROOT / "schemas" / "theme-pack-v1"
VALUE = {"oneOf": [{"type": "string", "maxLength": 500}, {"type": "number"}]}


def object_with_exact_values(
    names: set[str] | frozenset[str],
    *,
    overrides: dict[str, object] | None = None,
) -> dict[str, object]:
    ordered = sorted(names)
    value_schemas = overrides or {}
    return {
        "type": "object",
        "properties": {
            name: value_schemas.get(name, VALUE)
            for name in ordered
        },
        "required": ordered,
        "additionalProperties": False,
    }


def write(name: str, schema: dict[str, object]) -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(
        json.dumps(schema, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    write(
        "theme.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://davidlybeck.com/schemas/theme-pack-v1/theme.schema.json",
            "title": "Portfolio Theme Pack v1 manifest",
            "type": "object",
            "properties": {
                "$schema": {"const": THEME_PACK_SCHEMA},
                "id": {
                    "type": "string",
                    "pattern": "^[a-z][a-z0-9]*(?:-[a-z0-9]+)*$",
                    "maxLength": 48,
                },
                "label": {"type": "string", "minLength": 1, "maxLength": 64},
                "version": {"const": 1},
                "tiles": {"const": "tiles.json"},
                "presentation": {"const": "presentation.json"},
                "background": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 4,
                    "items": {
                        "type": "object",
                        "properties": {
                            "asset": {
                                "type": "string",
                                "pattern": "^assets/.+\\.svg$",
                                "maxLength": 200,
                            },
                            "depth": {
                                "type": "number",
                                "minimum": 0,
                                "maximum": 1,
                            },
                        },
                        "required": ["asset", "depth"],
                        "additionalProperties": False,
                    },
                },
                "selection": {
                    "type": "object",
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "randomEligible": {"type": "boolean"},
                        "randomWeight": {"type": "integer", "minimum": 1, "maximum": 100},
                    },
                    "required": ["enabled", "randomEligible", "randomWeight"],
                    "additionalProperties": False,
                },
            },
            "required": [
                "$schema", "id", "label", "version", "tiles",
                "presentation", "selection",
            ],
            "additionalProperties": False,
        },
    )

    connector = {
        "type": "object",
        "properties": {
            "color": {"type": "string", "minLength": 1, "maxLength": 500},
            "strokeWidth": {"type": "number", "minimum": .5, "maximum": 12},
            "opacity": {"type": "number", "minimum": 0, "maximum": 1},
            "headStyle": {"enum": ["none", "open", "closed"]},
            "headPosition": {"enum": ["none", "start", "end", "both"]},
            "headLen": {"type": "number", "minimum": 0, "maximum": 40},
            "headHalf": {"type": "number", "minimum": 0, "maximum": 30},
            "wobble": {"type": "number", "minimum": 0, "maximum": .5},
            "lineCap": {"enum": ["butt", "round", "square"]},
            "dashPattern": {"enum": ["none", "short", "long", "dot"]},
            "curveStyle": {"enum": ["straight", "arc", "varied"]},
            "texture": {"enum": ["none", "rough", "glow"]},
            "textureColor": {"type": "string", "minLength": 1, "maxLength": 500},
            "haloWidth": {"type": "number", "minimum": 1, "maximum": 4},
            "haloOpacity": {"type": "number", "minimum": 0, "maximum": 1},
            "insetFactor": {"type": "number", "minimum": 0, "maximum": 20},
            "variation": {
                "type": "object",
                "properties": {
                    "strokeWidth": {"type": "number", "minimum": 0, "maximum": .5},
                    "wobble": {"type": "number", "minimum": 0, "maximum": .25},
                    "dash": {"type": "number", "minimum": 0, "maximum": .5},
                    "opacity": {"type": "number", "minimum": 0, "maximum": .5},
                    "markerScale": {"type": "number", "minimum": 0, "maximum": .5},
                },
                "required": ["strokeWidth", "wobble", "dash", "opacity", "markerScale"],
                "additionalProperties": False,
            },
        },
        "required": [
            "color", "strokeWidth", "opacity", "headStyle", "headPosition",
            "headLen", "headHalf", "wobble",
            "lineCap", "dashPattern", "curveStyle", "texture",
            "textureColor", "haloWidth", "haloOpacity", "insetFactor",
            "variation",
        ],
        "additionalProperties": False,
    }
    write(
        "presentation.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://davidlybeck.com/schemas/theme-pack-v1/presentation.schema.json",
            "title": "Portfolio Theme Pack v1 presentation",
            "type": "object",
            "properties": {
                "board": object_with_exact_values(
                    BOARD_PRESENTATION_TOKENS,
                    overrides={
                        "content-area-space": {"enum": ["box", "svg"]},
                        "focus-motion": {"enum": ["cover", "grow", "settle", "reveal"]},
                        "action-treatment": {"enum": ["annotation", "marker"]},
                        "viewer-artifact": {
                            "enum": [
                                "none",
                                "field-notebook",
                                "observation-window",
                                "expedition-log",
                            ]
                        },
                    },
                ),
                "document": object_with_exact_values(DOCUMENT_PRESENTATION_TOKENS),
                "connectors": connector,
            },
            "required": ["board", "document", "connectors"],
            "additionalProperties": False,
        },
    )

    transform = {
        "type": "object",
        "properties": {
            "rotationDegrees": {"type": "number", "minimum": -45, "maximum": 45},
            "offsetXPixels": {"type": "number", "minimum": -24, "maximum": 24},
            "offsetYPixels": {"type": "number", "minimum": -24, "maximum": 24},
        },
        "required": ["rotationDegrees", "offsetXPixels", "offsetYPixels"],
        "additionalProperties": False,
    }
    transforms = {
        "type": "object",
        "properties": {
            "base": transform,
            "expanded": transform,
            "detailRotationDegrees": {
                "type": "number", "minimum": -45, "maximum": 45,
            },
        },
        "required": ["base", "expanded", "detailRotationDegrees"],
        "additionalProperties": False,
    }
    motion = {
        "type": "object",
        "properties": {
            "durationOffsetMilliseconds": {
                "type": "integer", "minimum": -150, "maximum": 150,
            },
            "rotationOffsetDegrees": {
                "type": "number", "minimum": -12, "maximum": 12,
            },
            "offsetXPixels": {"type": "number", "minimum": -24, "maximum": 24},
            "offsetYPixels": {"type": "number", "minimum": -24, "maximum": 24},
            "scaleOffset": {"type": "number", "minimum": -.15, "maximum": .15},
        },
        "required": [
            "durationOffsetMilliseconds", "rotationOffsetDegrees",
            "offsetXPixels", "offsetYPixels", "scaleOffset",
        ],
        "additionalProperties": False,
    }
    typography = {
        "type": ["object", "null"],
        "properties": {
            "baseFontFamily": {"type": "string", "minLength": 1, "maxLength": 200},
            "expandedTitleFontFamily": {
                "type": "string", "minLength": 1, "maxLength": 200,
            },
            "expandedTextFontFamily": {
                "type": "string", "minLength": 1, "maxLength": 200,
            },
            "inkColor": {"type": "string", "minLength": 1, "maxLength": 200},
            "baseLetterSpacing": {
                "type": ["string", "null"], "minLength": 1, "maxLength": 200,
            },
        },
        "required": [
            "baseFontFamily", "expandedTitleFontFamily",
            "expandedTextFontFamily", "inkColor",
        ],
        "additionalProperties": False,
    }
    layout = {
        "type": ["object", "null"],
        "properties": {
            "expandedWidth": {"type": "string", "minLength": 1, "maxLength": 200},
            "expandedMinHeight": {
                "type": "string", "minLength": 1, "maxLength": 200,
            },
            "phoneExpandedWidth": {
                "type": "string", "minLength": 1, "maxLength": 200,
            },
            "phoneExpandedMinHeight": {
                "type": "string", "minLength": 1, "maxLength": 200,
            },
        },
        "required": [
            "expandedWidth", "expandedMinHeight",
            "phoneExpandedWidth", "phoneExpandedMinHeight",
        ],
        "additionalProperties": False,
    }
    reveal = TileReveal.model_json_schema(by_alias=True)
    part = reveal.pop('$defs')['RevealPart']
    reveal['properties']['parts']['additionalProperties'] = part
    assignment = {
        "type": "object",
        "properties": {
            "base": {"type": "string", "pattern": "^assets/tiles/.+\\.svg$"},
            "expanded": {"type": "string", "pattern": "^assets/tiles/.+\\.svg$"},
            "factors": {
                "type": "object",
                "minProperties": MIN_VARIATION_AXIS_COUNT,
                "required": ["silhouette", "palette", "orientation"],
                "propertyNames": {"pattern": "^[a-z][a-z0-9-]{0,63}$"},
                "additionalProperties": {"type": "integer"},
            },
            "transforms": transforms,
            "motion": motion,
            "typography": typography,
            "layout": layout,
            "reveal": {"anyOf": [reveal, {"type": "null"}]},
        },
        "required": ["base", "expanded", "factors", "transforms", "motion"],
        "additionalProperties": False,
    }
    locations = sorted(BOARD_LOCATIONS)
    write(
        "tiles.schema.json",
        {
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "$id": "https://davidlybeck.com/schemas/theme-pack-v1/tiles.schema.json",
            "title": "Portfolio Theme Pack v1 tile catalog",
            "type": "object",
            "properties": {
                "assignments": {
                    "type": "object",
                    "properties": {location: assignment for location in locations},
                    "required": locations,
                    "additionalProperties": False,
                }
            },
            "required": ["assignments"],
            "additionalProperties": False,
        },
    )


if __name__ == "__main__":
    main()
