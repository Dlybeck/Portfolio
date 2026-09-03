#!/usr/bin/env python3
"""Create a complete, inert Theme Pack that can be edited without engine code."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.theme_packs import BOARD_LOCATIONS  # noqa: E402


def slug(value: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", value.lower()))


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


def tile_svg(
    title: str,
    state: str,
    color: str,
    edge: str,
    factors: dict[str, int],
) -> str:
    silhouette = factors["silhouette"]
    orientation = factors["orientation"]
    accent = factors["accent"]
    detail = factors["detail"]
    frame = factors["frame"]
    cut = 7 + silhouette * 2
    shape = (
        f"M{cut} 3H{200-cut}L197 {cut}V{160-cut}L{200-cut} 157H{cut}"
        f"L3 {160-cut}V{cut}Z"
    )
    accent_x = 174 - accent * 3
    accent_y = 18 + accent * 3
    accent_radius = 5 + accent
    marker_x = 28 + orientation * 16
    detail_y = 134 + detail
    frame_width = 2 + frame
    detail_opacity = ".62" if state == "expanded" else ".45"
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 160" '
        'preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">'
        f'<g data-visual-axis="palette" data-visual-value="{factors["palette"]}">'
        f'<path d="{shape}" fill="{color}" data-visual-axis="silhouette" '
        f'data-visual-value="{silhouette}" data-visual-scope="self"/>'
        f'<path d="{shape}" fill="none" stroke="{edge}" stroke-width="{frame_width}" '
        f'data-visual-axis="frame" data-visual-value="{frame}" '
        f'data-visual-scope="self"/>'
        '</g>'
        f'<circle cx="{accent_x}" cy="{accent_y}" r="{accent_radius}" '
        f'fill="{edge}" opacity=".55" data-visual-axis="accent" '
        f'data-visual-value="{accent}" data-visual-scope="self"/>'
        f'<path d="M{marker_x} 18v10" stroke="{edge}" stroke-width="3" '
        f'data-visual-axis="orientation" data-visual-value="{orientation}" '
        f'data-visual-scope="self"/>'
        f'<path d="M35 {detail_y}Q100 {detail_y - detail} 165 {detail_y}" '
        f'fill="none" stroke="{edge}" stroke-width="{1 + detail % 3}" '
        f'opacity="{detail_opacity}" data-visual-axis="detail" data-visual-value="{detail}" '
        f'data-visual-scope="self"/>'
        '<rect x="30" y="34" width="140" height="92" fill="none" stroke="none" '
        'data-theme-content-area="content"/></svg>\n'
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pack_id", help="lowercase kebab-case Theme Pack id")
    parser.add_argument("label", help="human-visible theme label")
    parser.add_argument("output_root", type=Path, help="parent directory for the new pack")
    args = parser.parse_args()
    if not re.fullmatch(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)*", args.pack_id):
        parser.error("pack_id must be lowercase kebab-case")

    pack = args.output_root.resolve() / args.pack_id
    if pack.exists():
        parser.error(f"refusing to overwrite existing path: {pack}")
    assets = pack / "assets" / "tiles"
    assets.mkdir(parents=True)

    canonical_presentation = json.loads(
        (ROOT / "static" / "themes" / "canonical" / "presentation.json")
        .read_text(encoding="utf-8")
    )
    write_json(pack / "presentation.json", canonical_presentation)
    write_json(
        pack / "theme.json",
        {
            "$schema": "portfolio-theme-pack/v1",
            "id": args.pack_id,
            "label": args.label,
            "version": 1,
            "tiles": "tiles.json",
            "presentation": "presentation.json",
            "selection": {
                "enabled": True,
                "randomEligible": False,
                "randomWeight": 1,
            },
        },
    )

    palette = ("#e7eef6", "#dcebd8", "#f5e4c6", "#eadcf2")
    assignments: dict[str, object] = {}
    for title in sorted(BOARD_LOCATIONS):
        value = int.from_bytes(
            hashlib.sha256(f"{args.pack_id}:{title}".encode()).digest()[:4],
            "big",
        )
        color = palette[value % len(palette)]
        edge = "#28384a"
        name = slug(title)
        factors = {
            "silhouette": value % 6,
            "palette": value % len(palette),
            "orientation": (value // 13) % 9,
            "accent": (value // 31) % 5,
            "detail": (value // 61) % 6,
            "frame": (value // 97) % 4,
        }
        for state in ("base", "expanded"):
            (assets / f"{name}-{state}.svg").write_text(
                tile_svg(title, state, color, edge, factors), encoding="utf-8"
            )
        assignments[title] = {
            "base": f"assets/tiles/{name}-base.svg",
            "expanded": f"assets/tiles/{name}-expanded.svg",
            "factors": factors,
            "transforms": {
                "base": {
                    "rotationDegrees": (value % 9) - 4,
                    "offsetXPixels": (value // 11) % 7 - 3,
                    "offsetYPixels": (value // 17) % 7 - 3,
                },
                "expanded": {
                    "rotationDegrees": (value // 23) % 9 - 4,
                    "offsetXPixels": (value // 29) % 7 - 3,
                    "offsetYPixels": (value // 37) % 7 - 3,
                },
                "detailRotationDegrees": (value // 43) % 13 - 6,
            },
            "motion": {
                "durationOffsetMilliseconds": (value // 47) % 61 - 30,
                "rotationOffsetDegrees": (value // 53) % 5 - 2,
                "offsetXPixels": (value // 59) % 5 - 2,
                "offsetYPixels": (value // 67) % 5 - 2,
                "scaleOffset": 0,
            },
        }
    write_json(pack / "tiles.json", {"assignments": assignments})
    print(pack)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
