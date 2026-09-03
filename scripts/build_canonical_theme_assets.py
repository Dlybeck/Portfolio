#!/usr/bin/env python3
"""Compile the original paper-board grammar into inert Theme Pack SVGs.

The selections intentionally mirror ``legacyPaperTiles.js``.  The SVG output
keeps that hand-made variation while letting the generic Theme Engine render
Canonical Paper through the same contract as every other world.
"""

from __future__ import annotations

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
    "rect", "rect", "rect", "rect", "torn-bottom", "torn-top",
    "torn-both", "corner-bite", "ripped-side",
)


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def stable_hash(value: str) -> int:
    """The FNV-1a channel used by the original JavaScript presenter."""
    result = 2166136261
    for character in value:
        result ^= ord(character)
        result = (result * 16777619) & 0xFFFFFFFF
    signed = result if result < 0x80000000 else result - 0x100000000
    return abs(signed)


def rehash(value: int) -> int:
    mixed = ((value ^ (value >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
    mixed = ((mixed ^ (mixed >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
    return (mixed ^ (mixed >> 16)) & 0xFFFFFFFF


def style_seed(title: str) -> dict[str, int | float]:
    value = stable_hash(title)
    return {
        "rotation": (value % 1000) / 100 - 5,
        "expanded_rotation": ((value // 7) % 1000) / 125 - 4,
        "tape_angle": ((value // 1031) % 1000) / 62.5 - 8,
        "color": value,
        "variant": value // 7,
        "expanded_variant": value // 3779,
        "shape": value // 19937,
        "expanded_shape": value // 39119,
    }


def node(parent: ET.Element, tag: str, **attributes: object) -> ET.Element:
    return ET.SubElement(
        parent,
        f"{{{SVG_NS}}}{tag}",
        {key: str(value) for key, value in attributes.items()},
    )


def visual_carriers(
    parent: ET.Element, factors: dict[str, int], axes: tuple[str, ...]
) -> ET.Element:
    current = parent
    for axis in axes:
        current = node(
            current,
            "g",
            **{"data-visual-axis": axis, "data-visual-value": factors[axis]},
        )
    return current


def sticky_points(fold: int, height: int) -> str:
    small, large = 14, 22
    if fold == 0:
        return f"0,0 200,0 200,{height-small} {200-small},{height} 0,{height}"
    if fold == 1:
        return f"0,0 {200-small},0 200,{small} 200,{height} 0,{height}"
    if fold == 2:
        return f"0,0 200,0 200,{height} {small},{height} 0,{height-small}"
    if fold == 3:
        return f"{small},0 200,0 200,{height} 0,{height} 0,{small}"
    if fold == 4:
        return f"0,0 200,0 200,{height-large} {200-large},{height} 0,{height}"
    if fold == 5:
        return f"0,0 200,0 200,{height} {large},{height} 0,{height-large}"
    if fold == 6:
        return f"{large},0 200,0 200,{height} 0,{height} 0,{large}"
    return f"0,0 200,0 200,{height} 0,{height}"


def scrap_points(shape: str, height: int) -> str:
    top = {
        "torn-top": (
            "0,{h6} 8,{h2} 24,{h7} 40,{h1} 56,{h8} 72,{h2} "
            "88,{h8} 104,{h1} 120,{h9} 136,{h2} 152,{h7} 168,{h1} "
            "180,{h9} 192,{h3} 200,{h8}"
        ),
        "torn-both": (
            "0,{h6} 20,{h2} 44,{h7} 68,{h2} 92,{h8} 116,{h2} "
            "140,{h7} 164,{h2} 188,{h6} 200,{h3}"
        ),
        "corner-bite": "0,0 144,0 156,{h6} 172,{h3} 184,{h10} 200,{h14}",
    }
    bottom = {
        "torn-bottom": (
            "200,{h92} 192,{h97} 180,{h91} 168,{h99} 152,{h93} "
            "136,{h98} 120,{h91} 104,{h99} 88,{h92} 72,{h98} "
            "56,{h92} 40,{h99} 24,{h93} 8,{h98} 0,{h94}"
        ),
        "torn-both": (
            "200,{h94} 184,{h99} 160,{h93} 136,{h99} 112,{h92} "
            "88,{h98} 64,{h93} 40,{h99} 16,{h94} 0,{h97}"
        ),
    }
    values = {f"h{percent}": round(height * percent / 100, 2) for percent in (
        1, 2, 3, 6, 7, 8, 9, 10, 14, 91, 92, 93, 94, 97, 98, 99
    )}
    if shape == "ripped-side":
        return (
            f"6,0 200,0 200,{height} 6,{height} 12,{height*.92} "
            f"4,{height*.84} 10,{height*.76} 2,{height*.68} 8,{height*.60} "
            f"4,{height*.52} 10,{height*.44} 2,{height*.36} 8,{height*.28} "
            f"4,{height*.20} 10,{height*.12} 4,{height*.04}"
        )
    top_edge = top.get(shape, "0,0 200,0").format(**values)
    bottom_edge = bottom.get(shape, f"200,{height} 0,{height}").format(**values)
    return f"{top_edge} {bottom_edge}"


def add_surface_pattern(
    defs: ET.Element, pattern_id: str, kind: int, color: str
) -> str:
    pattern = node(
        defs, "pattern", id=pattern_id, patternUnits="userSpaceOnUse",
        width=24, height=24,
    )
    node(pattern, "rect", width=24, height=24, fill=color)
    if kind in {0, 4, 5}:
        node(pattern, "line", x1=0, y1=22, x2=24, y2=22,
             stroke="#7890b4", **{"stroke-width": .8, "stroke-opacity": .32})
    elif kind == 1:
        for position in (0, 16):
            node(pattern, "line", x1=position, y1=0, x2=position, y2=24,
                 stroke="#88a88c", **{"stroke-width": .8, "stroke-opacity": .3})
            node(pattern, "line", x1=0, y1=position, x2=24, y2=position,
                 stroke="#88a88c", **{"stroke-width": .8, "stroke-opacity": .3})
    elif kind in {3, 7}:
        node(pattern, "path", d="M-6 6L6-6M0 24L24 0M18 30L30 18",
             stroke="#6f5738", fill="none",
             **{"stroke-width": .8, "stroke-opacity": .1})
    elif kind == 6:
        for x, y in ((5, 5), (17, 17)):
            node(pattern, "circle", cx=x, cy=y, r=1, fill="#7f8d9b",
                 **{"fill-opacity": .38})
    elif kind == 8:
        node(pattern, "line", x1=0, y1=21, x2=24, y2=21,
             stroke="#725f49",
             **{"stroke-width": .8, "stroke-dasharray": "5 5", "stroke-opacity": .3})
    elif kind == 9:
        node(pattern, "path",
             d="M-6 6L6-6M0 24L24 0M18 30L30 18M-6 18L6 30M0 0L24 24M18-6L30 6",
             stroke="#846f52", fill="none",
             **{"stroke-width": .7, "stroke-opacity": .09})
    return f"url(#{pattern_id})"


def factors_for(title: str, seed: dict[str, int | float]) -> dict[str, int]:
    if title in HUBS:
        palette = int(seed["color"]) % len(STICKY_PALETTES)
        fold = rehash(stable_hash(f"{title}|fold")) % 8
        detail = rehash(stable_hash(title)) % 4
        return {
            "family": 0, "palette": palette, "surface": palette,
            "shape": fold, "fold": fold, "tape": 0, "detail": detail,
            "silhouette": fold,
        }
    surface = int(seed["variant"]) % len(SCRAP_PALETTES)
    shape = int(seed["shape"]) % len(SCRAP_SHAPES)
    return {
        "family": 1, "palette": surface, "surface": surface,
        "shape": shape, "fold": 0, "tape": 1,
        "detail": round(float(seed["tape_angle"]) + 8),
        "silhouette": shape,
    }


def add_sticky(
    svg: ET.Element, defs: ET.Element, title: str, state: str,
    height: int, factors: dict[str, int], seed: dict[str, int | float],
) -> None:
    base_palette = int(seed["color"]) % len(STICKY_PALETTES)
    palette = base_palette
    if state == "expanded":
        palette = (int(seed["expanded_variant"]) + 2) % len(STICKY_PALETTES)
        if palette == base_palette:
            palette = (palette + 1) % len(STICKY_PALETTES)
    fill, edge = STICKY_PALETTES[palette]
    pattern_id = f"sticky-{slug(title)}-{state}"
    pattern = node(defs, "pattern", id=pattern_id, patternUnits="userSpaceOnUse",
                   width=10, height=10)
    node(pattern, "rect", width=10, height=10, fill=fill)
    node(pattern, "path", d="M1 0L3 10M6 0L8 10", stroke="#1b1b1b",
         **{"stroke-width": .5, "stroke-opacity": .025})
    group = visual_carriers(svg, factors, (
        "family", "palette", "surface", "shape", "fold", "tape", "detail",
    ))
    node(group, "polygon", points=sticky_points(factors["fold"], height),
         fill=f"url(#{pattern_id})", stroke=edge,
         **{"stroke-width": 2, "stroke-linejoin": "round",
            "data-visual-axis": "silhouette",
            "data-visual-value": factors["silhouette"],
            "data-visual-scope": "self"})
    if state == "base":
        paths = (
            "M42 126Q68 120 92 126T158 125",
            "M40 124Q78 121 108 125T160 124M44 129Q88 126 156 128",
            "M38 126C58 119 72 132 92 126S124 119 162 126",
            "M40 126Q98 121 154 126Q160 127 165 123",
        )
        node(group, "path", d=paths[factors["detail"]], fill="none",
             stroke="#364b66",
             **{"stroke-width": 2.1, "stroke-linecap": "round",
                "stroke-linejoin": "round", "stroke-opacity": .72})


def add_scrap(
    svg: ET.Element, defs: ET.Element, title: str, state: str,
    height: int, factors: dict[str, int], seed: dict[str, int | float],
) -> None:
    base_surface = int(seed["variant"]) % len(SCRAP_PALETTES)
    surface = base_surface
    shape_index = int(seed["shape"]) % len(SCRAP_SHAPES)
    if state == "expanded":
        surface = (int(seed["expanded_variant"]) + 2) % len(SCRAP_PALETTES)
        if surface == base_surface:
            surface = (surface + 1) % len(SCRAP_PALETTES)
        shape_index = int(seed["expanded_shape"]) % len(SCRAP_SHAPES)
    fill, edge = SCRAP_PALETTES[surface]
    pattern_id = f"paper-{slug(title)}-{state}"
    paper_fill = add_surface_pattern(defs, pattern_id, surface, fill)
    group = visual_carriers(svg, factors, (
        "family", "palette", "surface", "shape", "fold", "tape", "detail",
    ))
    node(group, "polygon", points=scrap_points(SCRAP_SHAPES[shape_index], height),
         fill=paper_fill, stroke=edge,
         **{"stroke-width": 1.6, "stroke-linejoin": "round",
            "data-visual-axis": "silhouette",
            "data-visual-value": factors["silhouette"],
            "data-visual-scope": "self"})
    tape_width = 58 if state == "base" else 84
    tape_height = 18 if state == "base" else 22
    tape_x = (200 - tape_width) / 2
    tape_y = -8 if state == "base" else -10
    tape = node(group, "g", transform=(
        f"rotate({float(seed['tape_angle']):.2f} 100 {tape_y + tape_height / 2})"
    ))
    node(tape, "rect", x=tape_x, y=tape_y, width=tape_width,
         height=tape_height, rx=1.5, fill="#eee0aa", stroke="#aa955d",
         **{"stroke-width": .8, "fill-opacity": .82, "stroke-opacity": .45})
    node(tape, "line", x1=tape_x + 4, y1=tape_y + 4,
         x2=tape_x + tape_width - 4, y2=tape_y + 4,
         stroke="#fff8d1", **{"stroke-width": .8, "stroke-opacity": .65})


def build_svg(title: str, state: str) -> tuple[str, dict[str, int], float]:
    height = 160 if state == "base" else 240
    seed = style_seed(title)
    factors = factors_for(title, seed)
    svg = ET.Element(f"{{{SVG_NS}}}svg", {
        "viewBox": f"0 0 200 {height}",
        "preserveAspectRatio": "xMidYMid meet",
        "aria-hidden": "true", "focusable": "false",
        "data-visual-axis": "orientation",
        "data-visual-value": str(round(float(seed["rotation"]) + 5)),
    })
    defs = node(svg, "defs")
    if title in HUBS:
        add_sticky(svg, defs, title, state, height, factors, seed)
    else:
        add_scrap(svg, defs, title, state, height, factors, seed)
    safe = (27, 30, 146, 98) if state == "base" else (24, 28, 152, 174)
    node(svg, "rect", x=safe[0], y=safe[1], width=safe[2], height=safe[3],
         fill="none", stroke="none", **{"data-theme-content-area": "content"})
    factors["orientation"] = round(float(seed["rotation"]) + 5)
    rotation = seed["rotation"] if state == "base" else seed["expanded_rotation"]
    return ET.tostring(svg, encoding="unicode"), factors, round(float(rotation), 2)


def main() -> None:
    output = PACK_ROOT / "assets" / "tiles"
    output.mkdir(parents=True, exist_ok=True)
    assignments: dict[str, object] = {}
    for title in TITLES:
        paths: dict[str, str] = {}
        identity_factors: dict[str, int] | None = None
        base_rotation = 0.0
        for state in ("base", "expanded"):
            markup, factors, rotation = build_svg(title, state)
            asset_name = f"{slug(title)}-{state}.svg"
            (output / asset_name).write_text(markup + "\n", encoding="utf-8")
            paths[state] = f"assets/tiles/{asset_name}"
            identity_factors = identity_factors or factors
            if state == "base":
                base_rotation = rotation
        assignments[title] = {
            **paths, "factors": identity_factors,
            "rotationDegrees": base_rotation,
        }
    (PACK_ROOT / "tiles.json").write_text(
        json.dumps({"assignments": assignments}, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
