#!/usr/bin/env python3
"""Capture the 50-view owner-review matrix for the Theme Laboratory."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import threading
import time

from playwright.sync_api import Page, sync_playwright
import uvicorn

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.config import settings  # noqa: E402
from core.theme_packs import ThemePackRegistry  # noqa: E402
from main import app  # noqa: E402


OUTPUT = ROOT / "tests/results/theme-lab/final"
VIEWPORTS = {
    "desktop": {"width": 1440, "height": 900},
    "phone": {"width": 390, "height": 844},
}


def review_theme_ids(
    registry: ThemePackRegistry | None = None,
) -> tuple[str, ...]:
    """Return every enabled visual world in registry order."""
    active_registry = registry or ThemePackRegistry.discover()
    return tuple(
        pack.id for pack in active_registry.packs if pack.selection.enabled
    )


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def theme_url(origin: str, route: str, theme: str) -> str:
    route_without_hash, marker, fragment = route.partition("#")
    separator = "&" if "?" in route_without_hash else "?"
    hash_part = f"#{fragment}" if marker else ""
    return f"{origin}{route_without_hash}{separator}theme={theme}{hash_part}"


def wait_for_board(page: Page, title: str) -> None:
    page.locator(f'.tile-container[data-title="{title}"].expanded').wait_for()
    page.evaluate("document.fonts.ready")


def visit_scene(page: Page, origin: str, theme: str, scene: str) -> None:
    if scene == "home":
        page.goto(theme_url(origin, "/", theme), wait_until="domcontentloaded")
        wait_for_board(page, "Home")
    elif scene == "nested":
        page.goto(
            theme_url(origin, "/#Websites", theme),
            wait_until="domcontentloaded",
        )
        wait_for_board(page, "Websites")
    elif scene == "text-document":
        page.goto(
            theme_url(origin, "/projects/programs", theme),
            wait_until="domcontentloaded",
        )
        page.locator(".mini-window-container.open").wait_for()
        page.frame_locator(".mini-window").locator("#location").wait_for()
        page.evaluate("document.fonts.ready")
    elif scene == "media-document":
        page.goto(
            theme_url(origin, "/projects/websites/this_website/v3", theme),
            wait_until="domcontentloaded",
        )
        page.locator(".mini-window-container.open").wait_for()
        page.frame_locator(".mini-window").locator("img.media").first.wait_for()
        page.evaluate("document.fonts.ready")
    elif scene == "focus":
        page.goto(theme_url(origin, "/", theme), wait_until="domcontentloaded")
        wait_for_board(page, "Home")
        page.get_by_role("button", name="Go to Projects").focus()
    else:
        raise ValueError(f"Unknown capture scene: {scene}")


def main() -> None:
    settings.THEME_LAB_ENABLED = True
    themes = review_theme_ids()
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
        raise RuntimeError("Portfolio preview server did not start")

    endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
    browser_host = os.environ.get("PLAYWRIGHT_BROWSER_HOST", "127.0.0.1")
    origin = f"http://{browser_host}:{port}"
    scenes = ("home", "nested", "text-document", "media-document", "focus")
    OUTPUT.mkdir(parents=True, exist_ok=True)
    for previous_capture in OUTPUT.glob("*.webp"):
        previous_capture.unlink()

    try:
        with sync_playwright() as playwright:
            browser = (
                playwright.chromium.connect(endpoint)
                if endpoint
                else playwright.chromium.launch(headless=True)
            )
            for viewport_name, viewport in VIEWPORTS.items():
                context = browser.new_context(
                    viewport=viewport,
                    device_scale_factor=1,
                    reduced_motion="reduce",
                    is_mobile=viewport_name == "phone",
                    has_touch=viewport_name == "phone",
                )
                page = context.new_page()
                for theme in themes:
                    for scene in scenes:
                        visit_scene(page, origin, theme, scene)
                        page.screenshot(
                            path=str(
                                OUTPUT
                                / f"{theme}-{viewport_name}-{scene}.webp"
                            ),
                            type="webp",
                            quality=90,
                            animations="disabled",
                        )
                context.close()
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    captures = sorted(OUTPUT.glob("*.webp"))
    expected = len(themes) * len(VIEWPORTS) * len(scenes)
    if len(captures) != expected:
        raise RuntimeError(
            f"Expected {expected} review captures for {len(themes)} packs, "
            f"found {len(captures)}"
        )
    print(f"Wrote {len(captures)} Theme Laboratory captures to {OUTPUT}")


if __name__ == "__main__":
    main()
