#!/usr/bin/env python3
"""Build deterministic, non-repeating Theme Pack background artwork."""

from __future__ import annotations

from html import escape
from pathlib import Path
import random


ROOT = Path(__file__).resolve().parents[1]
THEMES = ROOT / "static" / "themes"


def write(theme: str, body: str) -> None:
    path = THEMES / theme / "assets" / "background.svg"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3000 3000" '
        'preserveAspectRatio="none" aria-hidden="true" focusable="false">'
        f"{body}</svg>\n",
        encoding="utf-8",
    )


def canonical() -> str:
    # This is the original board's two-scale chalk dust recipe translated
    # from CSS data images into one pack-owned SVG.  Broad grain prevents a
    # flat wall; fine grain keeps it tactile without visible geometric bands.
    return (
        '<defs><filter id="chalk-fine" filterUnits="userSpaceOnUse" '
        'x="0" y="0" width="3000" height="3000">'
        '<feTurbulence type="fractalNoise" baseFrequency="2.0" numOctaves="3" '
        'seed="23" stitchTiles="stitch"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 '
        '0 0 0 .26 -.13"/></filter>'
        '<filter id="chalk-broad" filterUnits="userSpaceOnUse" '
        'x="0" y="0" width="3000" height="3000">'
        '<feTurbulence type="fractalNoise" baseFrequency="0.01" numOctaves="3" '
        'seed="30" stitchTiles="stitch"/>'
        '<feColorMatrix type="matrix" values="0 0 0 0 1 0 0 0 0 1 0 0 0 0 1 '
        '0 0 0 .09 -.045"/></filter></defs>'
        '<rect width="3000" height="3000" fill="#f3efe2" '
        'filter="url(#chalk-broad)"/>'
        '<rect width="3000" height="3000" fill="#f3efe2" '
        'filter="url(#chalk-fine)"/>'
    )


def planets() -> str:
    rng = random.Random(771943)
    colors = ("#ffffff", "#b7d9ff", "#ffe5a6", "#ddd1ff")
    stars = []
    for index in range(520):
        x = rng.uniform(18, 2982)
        y = rng.uniform(18, 2982)
        radius = rng.choices((1.2, 1.8, 2.5, 3.4), weights=(48, 32, 16, 4))[0]
        color = rng.choice(colors)
        opacity = rng.uniform(.5, .98)
        stars.append(
            f'<circle cx="{x:.1f}" cy="{y:.1f}" r="{radius:.1f}" '
            f'fill="{color}" opacity="{opacity:.2f}"/>'
        )
        if index % 83 == 0:
            arm = radius * 3.4
            stars.append(
                f'<path d="M{x-arm:.1f} {y:.1f}H{x+arm:.1f}M{x:.1f} {y-arm:.1f}'
                f'V{y+arm:.1f}" stroke="{color}" stroke-width="1.2" '
                f'stroke-opacity="{opacity:.2f}" stroke-linecap="round"/>'
            )
    return "".join(stars)


def islands() -> str:
    rng = random.Random(481516)
    currents = []
    for _ in range(46):
        x = rng.uniform(-120, 2850)
        y = rng.uniform(20, 2980)
        width = rng.uniform(180, 620)
        drift = rng.uniform(-85, 85)
        bend = rng.uniform(-90, 90)
        path = (
            f"M{x:.1f} {y:.1f} "
            f"C{x + width*.24:.1f} {y + bend:.1f} "
            f"{x + width*.62:.1f} {y - bend*.65:.1f} "
            f"{x + width:.1f} {y + drift:.1f}"
        )
        currents.append(
            f'<path d="{escape(path)}" fill="none" stroke="#cff2ed" '
            f'stroke-width="{rng.uniform(2, 5):.1f}" '
            f'stroke-opacity="{rng.uniform(.08, .19):.2f}" '
            'stroke-linecap="round"/>'
        )
    return "".join(currents)


def lily() -> str:
    """Sparse, unique water rings without a repeating wallpaper cadence."""
    rng = random.Random(314159)
    ripples = []
    for _ in range(10):
        x = rng.uniform(120, 2880)
        y = rng.uniform(120, 2880)
        width = rng.uniform(150, 430)
        height = width * rng.uniform(.22, .38)
        rotation = rng.uniform(-18, 18)
        opacity = rng.uniform(.07, .14)
        for ring in (1.0, 1.34):
            ripples.append(
                f'<ellipse cx="{x:.1f}" cy="{y:.1f}" '
                f'rx="{width * ring / 2:.1f}" ry="{height * ring / 2:.1f}" '
                'fill="none" stroke="#def7ed" '
                f'stroke-width="{rng.uniform(2.0, 4.2):.1f}" '
                f'stroke-opacity="{opacity / ring:.2f}" '
                f'transform="rotate({rotation:.1f} {x:.1f} {y:.1f})"/>'
            )
    return "".join(ripples)


def main() -> None:
    write("canonical", canonical())
    write("planets", planets())
    write("islands", islands())
    write("lily", lily())


if __name__ == "__main__":
    main()
