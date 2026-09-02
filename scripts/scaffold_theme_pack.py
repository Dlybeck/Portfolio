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


def tile_svg(title: str, state: str, color: str, edge: str) -> str:
    identity = slug(title)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 160" '
        'preserveAspectRatio="xMidYMid meet" aria-hidden="true" focusable="false">'
        f'<rect x="3" y="3" width="194" height="154" rx="22" fill="{color}" '
        f'stroke="{edge}" stroke-width="5" data-visual-axis="silhouette" '
        f'data-visual-value="{identity}" data-visual-scope="self"/>'
        f'<circle cx="24" cy="24" r="8" fill="{edge}" opacity=".55" '
        f'data-visual-axis="accent" data-visual-value="{state}"/>'
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
        for state in ("base", "expanded"):
            (assets / f"{name}-{state}.svg").write_text(
                tile_svg(title, state, color, edge), encoding="utf-8"
            )
        assignments[title] = {
            "base": f"assets/tiles/{name}-base.svg",
            "expanded": f"assets/tiles/{name}-expanded.svg",
            "factors": {
                "silhouette": value % 8,
                "palette": value % len(palette),
                "orientation": (value // 13) % 9,
                "accent": (value // 31) % 5,
            },
            "rotationDegrees": (value % 9) - 4,
        }
    write_json(pack / "tiles.json", {"assignments": assignments})
    print(pack)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
