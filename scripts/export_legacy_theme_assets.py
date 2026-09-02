#!/usr/bin/env python3
"""Compile the four legacy Theme Laboratory renderers into pack SVG assets."""

from __future__ import annotations

import json
import os
from pathlib import Path
import re

from playwright.sync_api import sync_playwright


ROOT = Path(__file__).resolve().parent.parent
THEMES = ("lily", "planets", "clouds", "islands")
ORIGIN = os.environ.get("PORTFOLIO_PREVIEW_ORIGIN", "http://127.0.0.1:8082")
FALLBACK_SAFE_AREAS = {
    "lily": {"base": (42, 48, 116, 70), "expanded": (34, 36, 132, 92)},
    "planets": {"base": (52, 48, 96, 70), "expanded": (38, 34, 124, 96)},
    "clouds": {"base": (38, 61, 124, 58), "expanded": (30, 48, 140, 80)},
    "islands": {"base": (44, 50, 112, 68), "expanded": (34, 38, 132, 90)},
}
VIEW_BOXES = {
    ("planets", "expanded"): "25 15 150 130",
    ("clouds", "expanded"): "20 15 160 130",
}


def slug(title: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")


def main() -> None:
    endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
    with sync_playwright() as playwright:
        browser = (
            playwright.chromium.connect(endpoint)
            if endpoint
            else playwright.chromium.launch(headless=True)
        )
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        for theme in THEMES:
            page.goto(f"{ORIGIN}/?theme={theme}", wait_until="domcontentloaded")
            page.locator('.tile-container[data-title="Home"].expanded').wait_for()
            assignments: dict[str, object] = {}
            output = ROOT / "static" / "themes" / theme / "assets" / "tiles"
            output.mkdir(parents=True, exist_ok=True)
            for title in page.evaluate("Object.keys(window.tileInfo)"):
                tile = page.locator(f'.tile-container[data-title="{title}"]')
                factors: dict[str, str] | None = None
                paths: dict[str, str] = {}
                for state in ("base", "expanded"):
                    node = tile.locator(f'[data-theme-size="{state}"]')
                    exported = node.evaluate(
                        """(source, options) => {
                            function fittedSafeArea() {
                                const silhouette = source.querySelector(
                                    '[data-visual-axis~="silhouette"]'
                                );
                                if (!silhouette?.isPointInFill) return options.fallback;
                                const targetRatio = options.state === 'base' ? 1.65 : 1.35;
                                const candidates = [];
                                for (let width = 144; width >= 44; width -= 4) {
                                    for (let height = 112; height >= 36; height -= 4) {
                                        for (let centerX = 92; centerX <= 108; centerX += 4) {
                                            for (let centerY = 76; centerY <= 92; centerY += 4) {
                                                const x = centerX - width / 2;
                                                const y = centerY - height / 2;
                                                const points = [];
                                                for (let row = 0; row <= 6; row += 1) {
                                                    for (let column = 0; column <= 6; column += 1) {
                                                        points.push(new DOMPoint(
                                                            x + width * column / 6,
                                                            y + height * row / 6
                                                        ));
                                                    }
                                                }
                                                if (!points.every((point) => silhouette.isPointInFill(point))) {
                                                    continue;
                                                }
                                                const ratioPenalty = 1 + Math.abs(
                                                    Math.log(width / height / targetRatio)
                                                );
                                                candidates.push({
                                                    x, y, width, height,
                                                    score: width * height / ratioPenalty,
                                                });
                                            }
                                        }
                                    }
                                }
                                candidates.sort((left, right) => right.score - left.score);
                                const best = candidates[0];
                                return best
                                    ? [best.x, best.y, best.width, best.height]
                                    : options.fallback;
                            }
                            const safeArea = fittedSafeArea();
                            const clone = source.cloneNode(true);
                            const originals = [source, ...source.querySelectorAll('*')];
                            const copies = [clone, ...clone.querySelectorAll('*')];
                            copies.forEach((copy, index) => {
                                const original = originals[index];
                                for (const name of ['fill', 'stroke']) {
                                    const value = copy.getAttribute(name);
                                    if (value?.includes('var(')) {
                                        copy.setAttribute(name, getComputedStyle(original)[name]);
                                    }
                                }
                                copy.removeAttribute('style');
                                [...copy.attributes]
                                    .filter((attribute) =>
                                        attribute.name.startsWith('data-')
                                        && !attribute.name.startsWith('data-variant-')
                                        && !attribute.name.startsWith('data-visual-')
                                        && attribute.name !== 'data-theme-content-area'
                                    )
                                    .forEach((attribute) => copy.removeAttribute(attribute.name));
                            });
                            clone.classList.remove(...[...clone.classList]
                                .filter((name) => name.startsWith('theme-object-')));
                            clone.querySelectorAll('[data-visual-axis~="palette"]')
                                .forEach((carrier) => carrier.removeAttribute('data-visual-scope'));
                            clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg');
                            if (options.viewBox) clone.setAttribute('viewBox', options.viewBox);
                            const marker = document.createElementNS(
                                'http://www.w3.org/2000/svg', 'rect'
                            );
                            marker.dataset.themeContentArea = 'content';
                            marker.setAttribute('x', safeArea[0]);
                            marker.setAttribute('y', safeArea[1]);
                            marker.setAttribute('width', safeArea[2]);
                            marker.setAttribute('height', safeArea[3]);
                            marker.setAttribute('fill', 'none');
                            marker.setAttribute('stroke', 'none');
                            clone.append(marker);
                            return {
                                markup: clone.outerHTML,
                                factors: Object.fromEntries(
                                    [...source.attributes]
                                        .filter((attribute) =>
                                            attribute.name.startsWith('data-variant-')
                                        )
                                        .map((attribute) => [
                                            attribute.name.replace('data-variant-', ''),
                                            Number(attribute.value),
                                        ])
                                ),
                            };
                        }""",
                        {
                            "fallback": FALLBACK_SAFE_AREAS[theme][state],
                            "state": state,
                            "viewBox": VIEW_BOXES.get((theme, state)),
                        },
                    )
                    asset_name = f"{slug(title)}-{state}.svg"
                    (output / asset_name).write_text(
                        exported["markup"] + "\n", encoding="utf-8"
                    )
                    paths[state] = f"assets/tiles/{asset_name}"
                    factors = factors or exported["factors"]
                assignments[title] = {
                    **paths,
                    "factors": factors,
                    "rotationDegrees": (factors or {}).get("orientation", 8) - 8,
                }
            (ROOT / "static" / "themes" / theme / "tiles.json").write_text(
                json.dumps({"assignments": assignments}, indent=2) + "\n",
                encoding="utf-8",
            )
        page.close()
        browser.close()


if __name__ == "__main__":
    main()
