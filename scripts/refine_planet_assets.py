#!/usr/bin/env python3
"""Keep long Planets titles readable inside their real planet silhouettes."""

from __future__ import annotations

from pathlib import Path
import json
from xml.etree import ElementTree


ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "static" / "themes" / "planets" / "assets" / "tiles"
LONG_TITLE_SLUGS = ("work-experience", "scribblescan")
SVG_NAMESPACE = "http://www.w3.org/2000/svg"
ElementTree.register_namespace("", SVG_NAMESPACE)


def main() -> None:
    for slug in LONG_TITLE_SLUGS:
        path = ASSETS / f"{slug}-base.svg"
        tree = ElementTree.parse(path)
        marker = next(
            element
            for element in tree.getroot().iter()
            if element.attrib.get("data-theme-content-area") == "content"
        )
        marker.attrib.update({
            "x": "56",
            "y": "62",
            "width": "88",
            "height": "42",
        })
        tree.write(path, encoding="unicode")
        path.write_text(path.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    catalog_path = ASSETS.parents[1] / "tiles.json"
    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    spacing = {"Work Experience": "-0.25px", "ScribbleScan": "-0.8px"}
    for title, letter_spacing in spacing.items():
        catalog["assignments"][title]["typography"] = {
            "baseFontFamily": "'Architects Daughter', cursive",
            "expandedTitleFontFamily": "'Kalam', cursive",
            "expandedTextFontFamily": "'Architects Daughter', cursive",
            "inkColor": "#f7f0dc",
            "baseLetterSpacing": letter_spacing,
        }
    catalog_path.write_text(
        json.dumps(catalog, indent=2) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    main()
