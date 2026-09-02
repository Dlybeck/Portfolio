#!/usr/bin/env python3
"""Render the canonical Home Board social preview at 1200 by 630 pixels."""

from __future__ import annotations

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

from main import app  # noqa: E402


OUTPUT = ROOT / "static/images/social/home-board.webp"


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def main() -> None:
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
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    try:
        with sync_playwright() as playwright:
            browser = (
                playwright.chromium.connect(endpoint)
                if endpoint
                else playwright.chromium.launch(headless=True)
            )
            context = browser.new_context(
                viewport={"width": 1200, "height": 630},
                device_scale_factor=1,
                reduced_motion="no-preference",
            )
            page = context.new_page()
            page.goto(
                f"http://{browser_host}:{port}/",
                wait_until="domcontentloaded",
            )
            page.locator(
                '.tile-container[data-title="Home"].expanded'
            ).wait_for()
            page.evaluate("document.fonts.ready")
            page.screenshot(
                path=str(OUTPUT),
                type="webp",
                quality=90,
                animations="disabled",
            )
            context.close()
            browser.close()
    finally:
        server.should_exit = True
        thread.join(timeout=5)

    print(f"Wrote {OUTPUT} (1200x630)")


if __name__ == "__main__":
    main()
