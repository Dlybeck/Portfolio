#!/usr/bin/env python3
"""Compile the Original paper world into inert Theme Pack SVG assets."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parent.parent
PACK_ROOT = ROOT / "static" / "themes" / "canonical"
SVG_NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG_NS)

TITLES = (
    "Home", "Hobbies", "Projects", "Work Experience", "Education",
    "3D Printing", "Gaming", "Tennis", "Other Models", "Puzzles",
    "Programs", "Websites", "Digital Planner", "This website",
    "ScribbleScan", "College", "Early Education",
)
HUBS = frozenset(
    {"Home", "Hobbies", "3D Printing", "Projects", "Websites", "Education"}
)
STICKY_PALETTES = (
    ("#ffe66d", "#d7bd42"), ("#ffb6c1", "#d88798"),
    ("#b3dcff", "#78acd8"), ("#c4eab0", "#86bc70"),
    ("#ffd49a", "#d7a45d"),
)
SCRAP_PALETTES = (
    ("#fafaf2", "#c9c5b9"), ("#f7faf3", "#bac9ba"),
    ("#fbf8ee", "#cbc2aa"), ("#c9a877", "#967447"),
    ("#fbfbf3", "#c8c8b6"), ("#fdf1a5", "#cdbc64"),
    ("#f8f6ef", "#c4c0b4"), ("#d9bf8a", "#a98e59"),
    ("#f6f3e8", "#c4bcaa"), ("#f9f4e6", "#cbbfa7"),
)
SCRAP_SHAPES = (
    "0,0 200,0 200,160 0,160",
    "0,0 200,0 200,145 190,156 176,146 160,159 144,148 126,157 "
    "108,146 90,159 72,147 54,157 36,146 18,158 0,150",
    "0,12 16,3 34,13 52,2 70,14 88,4 106,15 124,3 142,13 160,2 "
    "180,14 200,5 200,160 0,160",
    "0,11 20,3 42,13 64,3 86,14 108,3 130,13 152,2 176,13 200,5 "
    "200,149 182,158 160,147 138,159 116,147 94,158 72,148 50,159 "
    "26,148 0,156",
    "0,0 145,0 158,12 174,5 186,19 200,26 200,160 0,160",
    "7,0 200,0 200,160 7,160 13,146 4,132 11,118 3,104 10,90 4,76 "
    "12,62 3,48 10,34 4,20 11,8",
)


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def seed(title: str, state: str) -> int:
    digest = hashlib.sha256(f"original|{title}|{state}".encode()).digest()
    return int.from_bytes(digest[:8], "big")


def node(parent: ET.Element, tag: str, **attributes: object) -> ET.Element:
    return ET.SubElement(
        parent,
        f"{{{SVG_NS}}}{tag}",
        {key: str(value) for key, value in attributes.items()},
    )


def visual_carriers(
    parent: ET.Element, factors: dict[str, int], axes: tuple[str, ...]
) -> ET.Element:
    """Wrap one visible object in independently auditable variation axes."""
    current = parent
    for axis in axes:
        current = node(
            current,
            "g",
            **{
                "data-visual-axis": axis,
                "data-visual-value": factors[axis],
            },
        )
    return current


def add_scrap_pattern(
    defs: ET.Element, pattern_id: str, kind: int, color: str
) -> str:
    pattern = node(
        defs,
        "pattern",
        id=pattern_id,
        patternUnits="userSpaceOnUse",
        width=24,
        height=24,
    )
    node(pattern, "rect", width=24, height=24, fill=color)
    if kind in {0, 4, 5}:
        node(
            pattern, "line", x1=0, y1=22, x2=24, y2=22,
            stroke="#8ca4c5", **{"stroke-width": 1, "stroke-opacity": .42}
        )
    elif kind == 1:
        for position in (0, 16):
            node(
                pattern, "line", x1=position, y1=0, x2=position, y2=24,
                stroke="#88a88c", **{"stroke-width": 1, "stroke-opacity": .35}
            )
            node(
                pattern, "line", x1=0, y1=position, x2=24, y2=position,
                stroke="#88a88c", **{"stroke-width": 1, "stroke-opacity": .35}
            )
    elif kind in {3, 7, 9}:
        node(
            pattern, "path", d="M-6 6L6-6M0 24L24 0M18 30L30 18",
            stroke="#6f5738",
            **{"stroke-width": 1, "stroke-opacity": .14, "fill": "none"},
        )
    elif kind == 6:
        for x, y in ((5, 5), (17, 17)):
            node(
                pattern, "circle", cx=x, cy=y, r=1.2, fill="#7f8d9b",
                **{"fill-opacity": .45},
            )
    elif kind == 8:
        node(
            pattern, "line", x1=0, y1=21, x2=24, y2=21,
            stroke="#725f49",
            **{
                "stroke-width": 1,
                "stroke-dasharray": "5 5",
                "stroke-opacity": .35,
            },
        )
    return f"url(#{pattern_id})"


def add_sticky(
    svg: ET.Element, title: str, state: str, value: int
) -> dict[str, int]:
    palette = value % len(STICKY_PALETTES)
    fill, edge = STICKY_PALETTES[palette]
    fold = (value // 7) % 8
    underline = (value // 17) % 6
    factors = {
        "family": 0,
        "palette": palette,
        "surface": 0,
        "shape": fold,
        "fold": fold,
        "tape": 0,
        "detail": underline,
        "silhouette": TITLES.index(title) % 8,
    }
    fold_points = {
        0: "174,160 200,134 200,160", 1: "174,0 200,26 200,0",
        2: "0,134 26,160 0,160", 3: "0,0 26,0 0,26",
        4: "158,160 200,118 200,160", 5: "0,118 42,160 0,160",
        6: "0,0 42,0 0,42",
    }
    group = visual_carriers(
        svg,
        factors,
        (
            "family", "palette", "surface", "shape", "fold", "tape",
            "detail",
        ),
    )
    node(
        group, "polygon", points="0,0 200,0 200,160 0,160",
        fill=fill,
        stroke=edge,
        **{
            "stroke-width": 2.5,
            "data-visual-axis": "silhouette",
            "data-visual-value": TITLES.index(title) % 8,
            "data-visual-scope": "self",
        },
    )
    if fold in fold_points:
        node(
            group, "polygon", points=fold_points[fold], fill=edge,
            **{"fill-opacity": .38},
        )
        node(
            group, "polyline", points=fold_points[fold], fill="none",
            stroke=edge, **{"stroke-width": 1.3, "stroke-opacity": .55},
        )
    y = 125 if state == "base" else 132
    paths = (
        f"M42 {y}Q68 {y-6} 92 {y}T158 {y-1}",
        f"M40 {y-2}Q78 {y-5} 108 {y-1}T160 {y-2}"
        f"M44 {y+3}Q88 {y} 156 {y+2}",
        f"M38 {y}C58 {y-7} 72 {y+6} 92 {y}S124 {y-7} 162 {y}",
        f"M40 {y}Q98 {y-5} 154 {y}Q160 {y+1} 165 {y-3}",
        f"M40 {y-2}L55 {y+2}L72 {y-2}L90 {y+2}L108 {y-2}"
        f"L126 {y+2}L146 {y-2}L162 {y}",
        f"M42 {y}Q72 {y-4} 104 {y+1}T158 {y}",
    )
    node(
        group, "path", d=paths[underline], fill="none", stroke="#364b66",
        **{
            "stroke-width": 2.2,
            "stroke-linecap": "round",
            "stroke-linejoin": "round",
            "stroke-opacity": .7,
        },
    )
    return factors


def add_scrap(
    svg: ET.Element, defs: ET.Element, title: str, state: str, value: int
) -> dict[str, int]:
    surface = value % len(SCRAP_PALETTES)
    fill, edge = SCRAP_PALETTES[surface]
    shape = (value // 11) % len(SCRAP_SHAPES)
    angle = (value // 37) % 15 - 7
    factors = {
        "family": 1,
        "palette": surface,
        "surface": surface,
        "shape": shape,
        "fold": 0,
        "tape": 1,
        "detail": angle + 7,
        "silhouette": shape,
    }
    pattern_id = f"paper-{slug(title)}-{state}"
    paper_fill = add_scrap_pattern(defs, pattern_id, surface, fill)
    group = visual_carriers(
        svg,
        factors,
        (
            "family", "palette", "surface", "shape", "fold", "tape",
            "detail",
        ),
    )
    node(
        group, "polygon", points=SCRAP_SHAPES[shape], fill=paper_fill,
        stroke=edge,
        **{
            "stroke-width": 2.2,
            "stroke-linejoin": "round",
            "data-visual-axis": "silhouette",
            "data-visual-value": shape,
            "data-visual-scope": "self",
        },
    )
    tape_width = 62 if state == "base" else 82
    tape_x = (200 - tape_width) / 2
    tape = node(
        group,
        "g",
        transform=f"rotate({angle} 100 9)",
    )
    node(
        tape, "rect", x=tape_x, y=0, width=tape_width,
        height=19 if state == "base" else 23, rx=2,
        fill="#eee0aa", stroke="#aa955d",
        **{
            "stroke-width": 1,
            "fill-opacity": .82,
            "stroke-opacity": .5,
        },
    )
    node(
        tape, "line", x1=tape_x + 4, y1=5,
        x2=tape_x + tape_width - 4, y2=5,
        stroke="#fff8d1", **{"stroke-width": 1, "stroke-opacity": .7},
    )
    return factors


def build_svg(title: str, state: str) -> tuple[str, dict[str, int], float]:
    value = seed(title, "identity")
    svg = ET.Element(
        f"{{{SVG_NS}}}svg",
        {
            "viewBox": "0 0 200 160",
            "preserveAspectRatio": "xMidYMid meet",
            "aria-hidden": "true",
            "focusable": "false",
        },
    )
    defs = node(svg, "defs")
    factors = (
        add_sticky(svg, title, state, value)
        if title in HUBS
        else add_scrap(svg, defs, title, state, value)
    )
    if len(defs) == 0:
        svg.remove(defs)
    safe = (31, 36, 138, 86) if state == "base" else (27, 27, 146, 104)
    node(
        svg, "rect", x=safe[0], y=safe[1], width=safe[2], height=safe[3],
        fill="none", stroke="none",
        **{"data-theme-content-area": "content"},
    )
    rotation = ((seed(title, "rotation") % 1001) / 100) - 5
    factors["orientation"] = round(rotation + 5)
    svg.set("data-visual-axis", "orientation")
    svg.set("data-visual-value", str(factors["orientation"]))
    return ET.tostring(svg, encoding="unicode"), factors, round(rotation, 2)


def main() -> None:
    output = PACK_ROOT / "assets" / "tiles"
    output.mkdir(parents=True, exist_ok=True)
    assignments: dict[str, object] = {}
    for title in TITLES:
        paths: dict[str, str] = {}
        identity_factors: dict[str, int] | None = None
        rotation = 0.0
        for state in ("base", "expanded"):
            markup, factors, rotation = build_svg(title, state)
            asset_name = f"{slug(title)}-{state}.svg"
            (output / asset_name).write_text(markup + "\n", encoding="utf-8")
            paths[state] = f"assets/tiles/{asset_name}"
            identity_factors = identity_factors or factors
        assignments[title] = {
            **paths,
            "factors": identity_factors,
            "rotationDegrees": rotation,
        }
    (PACK_ROOT / "tiles.json").write_text(
        json.dumps({"assignments": assignments}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
