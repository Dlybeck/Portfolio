#!/usr/bin/env python3
"""Compile the four legacy Theme Laboratory renderers into pack SVG assets."""

from __future__ import annotations

import json
import hashlib
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


def deterministic_value(theme: str, title: str, channel: str) -> int:
    digest = hashlib.sha256(f"{theme}|{title}|{channel}".encode()).digest()
    return int.from_bytes(digest[:4], "big")


def assignment_variation(
    theme: str, title: str, rotation: float
) -> tuple[dict[str, object], dict[str, int | float]]:
    # Preserve the accepted static alternate artwork. The separate fields are
    # available to future packs without forcing motion or placement changes on
    # worlds that already passed owner review.
    transforms = {
        "base": {
            "rotationDegrees": rotation,
            "offsetXPixels": 0,
            "offsetYPixels": 0,
        },
        "expanded": {
            "rotationDegrees": rotation,
            "offsetXPixels": 0,
            "offsetYPixels": 0,
        },
        "detailRotationDegrees": 0,
    }
    if theme in {"planets", "islands"}:
        seed = deterministic_value(theme, title, "motion")
        motion = {
            "durationOffsetMilliseconds": seed % 41 - 20,
            "rotationOffsetDegrees": round(((seed // 41) % 201) / 200 - .5, 2),
            "offsetXPixels": round(((seed // 201) % 201) / 100 - 1, 2),
            "offsetYPixels": round(((seed // 40401) % 201) / 100 - 1, 2),
            "scaleOffset": round(((seed // 809) % 11) / 1000 - .005, 3),
        }
    else:
        motion = {
            "durationOffsetMilliseconds": 0,
            "rotationOffsetDegrees": 0,
            "offsetXPixels": 0,
            "offsetYPixels": 0,
            "scaleOffset": 0,
        }
    return transforms, motion


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
                            // A full radial cut reaches the center of a lily
                            // pad and bisects every possible text carrier.
                            // Keep the recognizable notch, but make it the
                            // shallow natural edge cut used by the final pack.
                            if (options.theme === 'lily') {
                                source.querySelectorAll(
                                    '[data-visual-axis~="notch"]'
                                ).forEach((notch) => {
                                    notch.setAttribute(
                                        'd', 'M145 88L194 65L194 92Z'
                                    );
                                });
                            }
                            function fittedSafeArea() {
                                const silhouette = source.querySelector(
                                    '[data-visual-axis~="silhouette"]'
                                );
                                if (!silhouette?.isPointInFill) return options.fallback;
                                const cutouts = [...source.querySelectorAll(
                                    'mask path[fill="black"]'
                                )].filter((shape) => shape.isPointInFill);
                                const pointBelongsTo = (shape, point) => {
                                    const screenPoint = point.matrixTransform(
                                        source.getScreenCTM()
                                    );
                                    const localPoint = screenPoint.matrixTransform(
                                        shape.getScreenCTM().inverse()
                                    );
                                    return shape.isPointInFill(localPoint);
                                };
                                const targetRatio = options.state === 'base' ? 1.65 : 1.35;
                                const candidates = [];
                                const centerXs = cutouts.length
                                    ? [76, 88, 100, 112, 124]
                                    : [92, 100, 108];
                                const centerYs = cutouts.length
                                    ? [64, 76, 88, 100]
                                    : [76, 84, 92];
                                for (let width = 136; width >= 48; width -= 8) {
                                    for (let height = 104; height >= 40; height -= 8) {
                                        for (const centerX of centerXs) {
                                            for (const centerY of centerYs) {
                                                const x = centerX - width / 2;
                                                const y = centerY - height / 2;
                                                const points = [];
                                                for (let row = 0; row <= 2; row += 1) {
                                                    for (let column = 0; column <= 2; column += 1) {
                                                        points.push(new DOMPoint(
                                                            x + width * column / 2,
                                                            y + height * row / 2
                                                        ));
                                                    }
                                                }
                                                if (!points.every((point) => (
                                                    pointBelongsTo(silhouette, point)
                                                    && !cutouts.some((cutout) => (
                                                        pointBelongsTo(cutout, point)
                                                    ))
                                                ))) {
                                                    continue;
                                                }
                                                const ratioPenalty = 1 + Math.abs(
                                                    Math.log(width / height / targetRatio)
                                                );
                                                const centerPenalty = 1 + Math.hypot(
                                                    centerX - 100, centerY - 82
                                                ) / 180;
                                                candidates.push({
                                                    x, y, width, height,
                                                    score: width * height / ratioPenalty / centerPenalty,
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
                            const safeArea = options.safeOverride || fittedSafeArea();
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
                            const runtimePrefix = `${options.theme}-${options.slug}-${options.state}-`;
                            clone.querySelectorAll('[id]').forEach((element) => {
                                if (element.id.startsWith(runtimePrefix)) {
                                    element.id = element.id.slice(runtimePrefix.length);
                                }
                            });
                            clone.querySelectorAll('*').forEach((element) => {
                                for (const name of ['href', 'mask', 'clip-path', 'fill', 'stroke']) {
                                    const value = element.getAttribute(name);
                                    if (!value) continue;
                                    element.setAttribute(
                                        name,
                                        value.replace(`#${runtimePrefix}`, '#'),
                                    );
                                }
                            });
                            clone.querySelectorAll('[data-theme-content-area]')
                                .forEach((marker) => marker.remove());
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
                            "theme": theme,
                            "slug": slug(title),
                            "viewBox": VIEW_BOXES.get((theme, state)),
                            "safeOverride": (
                                [56, 62, 88, 42]
                                if theme == "planets"
                                and state == "base"
                                and title in {"Work Experience", "ScribbleScan"}
                                else None
                            ),
                        },
                    )
                    asset_name = f"{slug(title)}-{state}.svg"
                    (output / asset_name).write_text(
                        exported["markup"] + "\n", encoding="utf-8"
                    )
                    paths[state] = f"assets/tiles/{asset_name}"
                    factors = factors or exported["factors"]
                rotation = (factors or {}).get("orientation", 8) - 8
                transforms, motion = assignment_variation(
                    theme, title, rotation
                )
                assignments[title] = {
                    **paths,
                    "factors": factors,
                    "transforms": transforms,
                    "motion": motion,
                }
            (ROOT / "static" / "themes" / theme / "tiles.json").write_text(
                json.dumps({"assignments": assignments}, indent=2) + "\n",
                encoding="utf-8",
            )
        page.close()
        browser.close()


if __name__ == "__main__":
    main()
