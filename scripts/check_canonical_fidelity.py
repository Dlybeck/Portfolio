#!/usr/bin/env python3
"""Fail when Canonical loses the organic controls present before Theme Packs."""

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "static" / "themes" / "canonical"


def main() -> None:
    manifest = json.loads((PACK / "theme.json").read_text(encoding="utf-8"))
    presentation = json.loads(
        (PACK / "presentation.json").read_text(encoding="utf-8")
    )
    tiles = json.loads((PACK / "tiles.json").read_text(encoding="utf-8"))

    failures: list[str] = []
    backgrounds = manifest.get("background", [])
    if len(backgrounds) != 1 or backgrounds[0].get("depth") != 1.0:
        failures.append("Canonical background must remain one Board-attached layer")
    if not backgrounds:
        failures.append("Canonical has no validated background asset")
    else:
        path = PACK / backgrounds[0].get("asset", "")
        markup = path.read_text(encoding="utf-8") if path.is_file() else ""
        if markup.count("feTurbulence") != 2:
            failures.append("Canonical background lost its two-scale chalk texture")
        for frequency, seed in (("2.0", "23"), ("0.01", "30")):
            if f'baseFrequency="{frequency}"' not in markup or f'seed="{seed}"' not in markup:
                failures.append(
                    f"Canonical background lost original noise channel {frequency}/{seed}"
                )

    connectors = presentation["connectors"]
    original_connector_values = {
        "headStyle": "open",
        "headPosition": "both",
        "strokeWidth": 5.2,
        "wobble": 0.14,
        "texture": "rough",
    }
    for name, expected in original_connector_values.items():
        actual = connectors.get(name)
        if actual != expected:
            failures.append(
                f"connector {name} expected original {expected!r}, got {actual!r}"
            )

    board = presentation["board"]
    document = presentation["document"]
    if board.get("viewer-bg-image") == "none":
        failures.append("Canonical viewer lost the original ruled outer paper")
    main_document_values = {
        "container-bg": "#ffffff",
        "container-box-sizing": "content-box",
        "page-bg": "transparent",
        "page-bg-image": "none",
        "title-ink": "#006699",
        "title-size": "1.5rem",
        "body-line-height": "normal",
        "paragraph-line-height": "1.5",
        "paragraph-margin": "1em 0",
        "panel-bg": "rgba(255,255,255,.55)",
        "panel-border": "rgba(0,0,0,.3)",
        "panel-box-sizing": "content-box",
        "heading-2-size": "1.5rem",
        "heading-3-size": "1.17em",
        "heading-4-size": "1em",
        "model-bg": "#006699",
        "model-border-style": "none",
        "model-radius": "40px",
    }
    for name, expected in main_document_values.items():
        actual = document.get(name)
        if actual != expected:
            failures.append(
                f"Canonical document {name} expected main value "
                f"{expected!r}, got {actual!r}"
            )
    if board.get("phone-viewer-padding") != "26px 16px 30px":
        failures.append("Canonical viewer lost main's phone paper margins")
    for title, assignment in tiles["assignments"].items():
        transforms = assignment.get("transforms", {})
        base = transforms.get("base", {})
        expanded = transforms.get("expanded", {})
        for state, values in (("base", base), ("expanded", expanded)):
            for name in ("rotationDegrees", "offsetXPixels", "offsetYPixels"):
                if name not in values:
                    failures.append(f"{title} is missing {state} {name}")
        if "detailRotationDegrees" not in transforms:
            failures.append(f"{title} is missing independently declared detail rotation")
        if base.get("rotationDegrees") == expanded.get("rotationDegrees"):
            failures.append(f"{title} reuses one rotation for base and expanded paper")

        base_markup = (PACK / assignment["base"]).read_text(encoding="utf-8")
        expanded_markup = (PACK / assignment["expanded"]).read_text(encoding="utf-8")
        if title in {"Home", "Hobbies", "3D Printing", "Projects", "Websites", "Education"}:
            if "data-theme-detail=\"tape\"" in base_markup:
                failures.append(f"{title} incorrectly tapes a self-adhesive note")
            if "<linearGradient" not in base_markup:
                failures.append(f"{title} lost the shaded sticky-note surface")
            if "<path" in expanded_markup:
                failures.append(f"{title} gained an invented sticky-surface line")
        else:
            if "data-theme-detail=\"tape\"" not in base_markup:
                failures.append(f"{title} lost its base tape")
            if "data-theme-detail=\"tape\"" not in expanded_markup:
                failures.append(f"{title} lost its expanded tape")
            if "<linearGradient" not in base_markup:
                failures.append(f"{title} lost its dimensional tape treatment")

    if failures:
        for failure in failures[:16]:
            print(f"- {failure}")
        print(f"FAIL: {len(failures)} Original Paper fidelity signals are missing")
        raise SystemExit(1)
    print("PASS: Canonical retains the original organic-variation controls")


if __name__ == "__main__":
    main()
