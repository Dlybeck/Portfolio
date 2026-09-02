#!/usr/bin/env python3
"""Audit rendered Theme Laboratory variation against the canonical Board."""

from __future__ import annotations

import json
import math
import os
from pathlib import Path
import socket
import sys
import threading
import time

from playwright.sync_api import sync_playwright
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import settings  # noqa: E402
from main import app  # noqa: E402


THEMES = ("lily", "planets", "clouds", "islands")
CANONICAL_AXIS_COUNT = 6
MINIMUM_AXIS_COUNT = math.ceil(CANONICAL_AXIS_COUNT * 0.8)


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def main() -> None:
    settings.THEME_LAB_ENABLED = True
    port = available_port()
    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("Portfolio audit server did not start")

    endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
    browser_host = os.environ.get("PLAYWRIGHT_BROWSER_HOST", "127.0.0.1")
    origin = f"http://{browser_host}:{port}"
    report: dict[str, object] = {
        "canonical_axis_count": CANONICAL_AXIS_COUNT,
        "minimum_axis_count": MINIMUM_AXIS_COUNT,
    }

    try:
        with sync_playwright() as playwright:
            browser = (
                playwright.chromium.connect(endpoint)
                if endpoint
                else playwright.chromium.launch(headless=True)
            )
            context = browser.new_context(viewport={"width": 1440, "height": 900})
            page = context.new_page()
            page.goto(f"{origin}/?theme=canonical", wait_until="domcontentloaded")
            page.locator('.tile-container[data-title="Home"].expanded').wait_for()
            canonical_variants = page.locator(".tile-container").evaluate_all(
                """tiles => tiles.map((tile) => {
                    const classes = [...tile.classList];
                    const expandedClasses = [...tile.querySelector('.tile-expanded').classList];
                    const material = classes.find((name) =>
                        /^sticky-(yellow|pink|blue|green|orange)$/.test(name)
                        || /^scrap-(ruled|graph|plain|kraft|index|legal|dotgrid|manila|receipt|napkin)$/.test(name)
                    );
                    const form = classes.find((name) =>
                        name.startsWith('sticky-fold-') || name.startsWith('shape-')
                    );
                    const cover = expandedClasses.filter((name) =>
                        /^sticky-(yellow|pink|blue|green|orange)$/.test(name)
                        || /^scrap-(ruled|graph|plain|kraft|index|legal|dotgrid|manila|receipt|napkin)$/.test(name)
                        || name.startsWith('shape-')
                    ).sort().join('+');
                    return {
                        material,
                        form,
                        attachment: tile.classList.contains('sticky') ? 'self-adhesive' : 'tape',
                        ink: tile.style.getPropertyValue('--ink-color'),
                        orientation: tile.style.getPropertyValue('--rot'),
                        cover,
                    };
                })"""
            )
            canonical_signatures = {
                tuple(sorted(variant.items())) for variant in canonical_variants
            }
            minimum_combinations = math.ceil(len(canonical_variants) * 0.8)
            report["canonical"] = {
                "locations": len(canonical_variants),
                "distinct_combinations": len(canonical_signatures),
            }
            report["minimum_distinct_combinations"] = minimum_combinations

            worlds: dict[str, object] = {}
            for theme in THEMES:
                page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")
                page.locator('.tile-container[data-title="Home"].expanded').wait_for()
                variants = page.locator('[data-theme-size="base"]').evaluate_all(
                    """nodes => nodes.map((node) => Object.fromEntries(
                        [...node.attributes]
                            .filter((attribute) => attribute.name.startsWith('data-variant-'))
                            .map((attribute) => [
                                attribute.name.replace('data-variant-', ''),
                                attribute.value,
                            ])
                    ))"""
                )
                factor_names = set.intersection(*(set(variant) for variant in variants))
                factor_values = {
                    factor: len({variant[factor] for variant in variants})
                    for factor in sorted(factor_names)
                }
                signatures = {
                    tuple(sorted(variant.items())) for variant in variants
                }
                passed = (
                    len(factor_names) >= MINIMUM_AXIS_COUNT
                    and len(signatures) >= minimum_combinations
                    and all(count >= 2 for count in factor_values.values())
                )
                worlds[theme] = {
                    "axis_count": len(factor_names),
                    "factor_values": factor_values,
                    "distinct_combinations": len(signatures),
                    "passed": passed,
                }
            report["worlds"] = worlds
            context.close()
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    print(json.dumps(report, indent=2, sort_keys=True))
    if not all(world["passed"] for world in report["worlds"].values()):
        raise SystemExit("Theme variant parity audit failed")


if __name__ == "__main__":
    main()
