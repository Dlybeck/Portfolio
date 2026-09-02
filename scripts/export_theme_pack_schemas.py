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
)


OUTPUT = ROOT / "schemas" / "theme-pack-v1"
VALUE = {"oneOf": [{"type": "string", "maxLength": 500}, {"type": "number"}]}


def object_with_exact_values(names: set[str] | frozenset[str]) -> dict[str, object]:
    ordered = sorted(names)
    return {
        "type": "object",
        "properties": {name: VALUE for name in ordered},
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
        },
        "required": [
            "color", "strokeWidth", "opacity", "headStyle", "headPosition",
            "headLen", "headHalf", "wobble",
            "lineCap", "dashPattern", "curveStyle", "texture",
            "textureColor", "haloWidth", "haloOpacity", "insetFactor",
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
                "board": object_with_exact_values(BOARD_PRESENTATION_TOKENS),
                "document": object_with_exact_values(DOCUMENT_PRESENTATION_TOKENS),
                "connectors": connector,
            },
            "required": ["board", "document", "connectors"],
            "additionalProperties": False,
        },
    )

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
            "rotationDegrees": {"type": "number", "minimum": -45, "maximum": 45},
        },
        "required": ["base", "expanded", "factors", "rotationDegrees"],
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
