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


THEMES = ("canonical", "lily", "planets", "clouds", "islands")
CANONICAL_AXIS_COUNT = 6
MINIMUM_AXIS_COUNT = math.ceil(CANONICAL_AXIS_COUNT * 0.8)


def audit_world(page, origin: str, theme: str) -> dict[str, object]:
    """Prove declared factors have visible SVG evidence and stable expansion."""
    page.goto(f"{origin}/?theme={theme}", wait_until="domcontentloaded")
    page.locator('.tile-container[data-title="Home"].expanded').wait_for()
    variants = page.locator('[data-theme-size="base"]').evaluate_all(
        r"""nodes => nodes.map((node) => {
            const factors = Object.fromEntries(
                [...node.attributes]
                    .filter((attribute) => attribute.name.startsWith('data-variant-'))
                    .map((attribute) => [
                        attribute.name.replace('data-variant-', ''),
                        attribute.value,
                    ])
            );
            const visible = Object.fromEntries(Object.entries(factors).map(
                ([factorName, expectedValue]) => {
                    const selector = `[data-visual-axis~="${factorName}"]`;
                    const carrier = node.matches(selector) ? node : node.querySelector(selector);
                    if (!carrier || carrier.dataset.visualValue !== expectedValue) {
                        return [factorName, null];
                    }
                    const clone = carrier.cloneNode(true);
                    if (carrier.dataset.visualScope === 'self') clone.replaceChildren();
                    [clone, ...clone.querySelectorAll('*')].forEach((element) => {
                        [...element.attributes]
                            .filter((attribute) => attribute.name.startsWith('data-'))
                            .forEach((attribute) => element.removeAttribute(attribute.name));
                    });
                    let fingerprint = clone.outerHTML;
                    if (factorName !== 'palette') {
                        fingerprint = fingerprint
                            .replace(/#[0-9a-f]{3,8}/gi, '#color')
                            .replace(/rgba?\([^)]*\)/gi, 'rgb(color)');
                    }
                    return [factorName, {
                        value: expectedValue,
                        fingerprint,
                    }];
                }
            ));
            return {
                identity: node.dataset.themeIdentity,
                factors,
                visible,
            };
        })"""
    )
    expanded = page.locator('[data-theme-size="expanded"]').evaluate_all(
        """nodes => Object.fromEntries(nodes.map((node) => [
            node.dataset.themeIdentity,
            Object.fromEntries(
                [...node.attributes]
                    .filter((attribute) => attribute.name.startsWith('data-variant-'))
                    .map((attribute) => {
                        const name = attribute.name.replace('data-variant-', '');
                        const selector = `[data-visual-axis~="${name}"]`;
                        const carrier = node.matches(selector) ? node : node.querySelector(selector);
                        return [name, carrier?.dataset.visualValue ?? null];
                    })
            ),
        ]))"""
    )
    factor_names = set.intersection(
        *(set(variant["factors"]) for variant in variants)
    )
    factor_values = {
        factor: len({variant["factors"][factor] for variant in variants})
        for factor in sorted(factor_names)
    }
    visible_factor_values = {
        factor: len(
            {
                variant["visible"][factor]["fingerprint"]
                for variant in variants
                if variant["visible"][factor]
            }
        )
        for factor in sorted(factor_names)
    }
    visible_evidence_complete = all(
        all(variant["visible"][factor] for factor in factor_names)
        for variant in variants
    )
    visible_signatures = {
        tuple(
            sorted(
                (
                    factor,
                    variant["visible"][factor]["fingerprint"]
                    if variant["visible"][factor]
                    else None,
                )
                for factor in factor_names
            )
        )
        for variant in variants
    }
    continuity = all(
        variant["identity"] in expanded
        and all(
            expanded[variant["identity"]].get(factor) == value
            for factor, value in variant["factors"].items()
        )
        for variant in variants
    )
    minimum_combinations = math.ceil(len(variants) * 0.8)
    passed = (
        len(factor_names) >= MINIMUM_AXIS_COUNT
        and visible_evidence_complete
        and all(count >= 2 for count in factor_values.values())
        and all(count >= 2 for count in visible_factor_values.values())
        and len(visible_signatures) >= minimum_combinations
        and continuity
    )
    return {
        "locations": len(variants),
        "axis_count": len(factor_names),
        "factor_values": factor_values,
        "visible_factor_values": visible_factor_values,
        "visible_evidence_complete": visible_evidence_complete,
        "visible_distinct_combinations": len(visible_signatures),
        "minimum_distinct_combinations": minimum_combinations,
        "base_expanded_continuity": continuity,
        "passed": passed,
    }


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
            report["worlds"] = {
                theme: audit_world(page, origin, theme) for theme in THEMES
            }
            report["minimum_distinct_combinations"] = min(
                world["minimum_distinct_combinations"]
                for world in report["worlds"].values()
            )
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
