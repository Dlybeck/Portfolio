#!/usr/bin/env python3
"""Simplify Island Chain landmass interiors without changing their identity."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "themes" / "islands" / "assets" / "tiles"
SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)

CONTOURS = (
    "M61 103C82 92 117 93 139 105",
    "M57 108C79 96 119 97 145 108",
    "M64 99C86 88 116 90 137 102",
    "M58 105C84 91 121 94 143 106",
    "M63 110C87 99 116 99 138 109",
    "M55 101C81 90 123 91 147 103",
)


def local(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def main() -> None:
    for path in sorted(ASSETS.glob("*.svg")):
        root = ET.fromstring(path.read_text(encoding="utf-8"))
        elevation = next(
            (
                element for element in root.iter()
                if element.attrib.get("data-visual-axis") == "elevation"
            ),
            None,
        )
        for parent in root.iter():
            for child in list(parent):
                if (
                    local(child) == "path"
                    and child.attrib.get("class") == "theme-detail"
                    and parent is not elevation
                ):
                    parent.remove(child)
        if elevation is not None:
            value = int(elevation.attrib.get("data-visual-value", "0"))
            for child in list(elevation):
                elevation.remove(child)
            ET.SubElement(elevation, f"{{{SVG}}}path", {
                "class": "theme-detail",
                "d": CONTOURS[value % len(CONTOURS)],
                "fill": "none",
                "stroke": "#2d724d",
                "stroke-width": "2.4",
                "stroke-linecap": "round",
                "stroke-opacity": ".36",
            })
            if path.stem.endswith("-expanded"):
                ET.SubElement(elevation, f"{{{SVG}}}path", {
                    "class": "theme-detail",
                    "d": CONTOURS[(value + 2) % len(CONTOURS)],
                    "fill": "none",
                    "stroke": "#b1c66b",
                    "stroke-width": "1.8",
                    "stroke-linecap": "round",
                    "stroke-opacity": ".26",
                    "transform": "translate(0 9)",
                })
        path.write_text(ET.tostring(root, encoding="unicode") + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
