"""Recreate the v3 retrospective images from the repository states they describe."""

from __future__ import annotations

import os
from pathlib import Path
import socket
import subprocess
import tempfile
import threading
import time
from urllib.request import urlopen

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from playwright.sync_api import sync_playwright
import uvicorn


REPOSITORY = Path(__file__).resolve().parents[1]
OUTPUT_DIRECTORY = (
    REPOSITORY / "static" / "images" / "projects" / "this_website" / "v3"
)
PLAYWRIGHT_WS_ENDPOINT = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
PLAYWRIGHT_BROWSER_HOST = os.environ.get("PLAYWRIGHT_BROWSER_HOST", "hostmachine")

SNAPSHOTS = (
    # First paper-on-tabletop implementation, dated April 22, 2026.
    ("1.webp", "31e2ba3", None),
    # Side-sliding paper viewer after the April 23 interaction polish.
    ("2.webp", "4fd2f2c", "/projects/websites/this_website"),
    # Public-only site immediately after the April 25 /dev removal.
    ("3.webp", "0eacd53", "/jobs"),
)


def available_port() -> int:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        return listener.getsockname()[1]


def wait_until_ready(url: str) -> None:
    deadline = time.monotonic() + 20
    while time.monotonic() < deadline:
        try:
            with urlopen(url, timeout=1) as response:
                if response.status == 200:
                    return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"Historical portfolio did not start at {url}")


def historical_public_app(checkout: Path) -> FastAPI:
    templates = Jinja2Templates(directory=checkout / "templates")
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=checkout / "static"), name="static")

    template_by_path = {
        "": "pages/home.html",
        "projects/websites/this_website": "pages/projects/websites/this_website.html",
        "jobs": "pages/jobs.html",
    }

    @app.get("/{path:path}")
    async def public_page(request: Request, path: str):
        template = template_by_path.get(path)
        if template is None:
            raise HTTPException(status_code=404)
        return templates.TemplateResponse(request, template, {})

    return app


def capture(commit: str, open_route: str | None, destination: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="portfolio-v3-history-") as temp:
        checkout = Path(temp) / "checkout"
        subprocess.run(
            ["git", "worktree", "add", "--detach", str(checkout), commit],
            cwd=REPOSITORY,
            check=True,
        )

        port = available_port()
        server = uvicorn.Server(
            uvicorn.Config(
                historical_public_app(checkout),
                host="0.0.0.0",
                port=port,
                log_level="error",
            )
        )
        server_thread = threading.Thread(target=server.run, daemon=True)
        server_thread.start()

        try:
            local_origin = f"http://127.0.0.1:{port}"
            browser_origin = (
                f"http://{PLAYWRIGHT_BROWSER_HOST}:{port}"
                if PLAYWRIGHT_WS_ENDPOINT
                else local_origin
            )
            wait_until_ready(local_origin)
            with sync_playwright() as playwright:
                browser = (
                    playwright.chromium.connect(PLAYWRIGHT_WS_ENDPOINT)
                    if PLAYWRIGHT_WS_ENDPOINT
                    else playwright.chromium.launch(headless=True)
                )
                context = browser.new_context(
                    viewport={"width": 1440, "height": 900},
                    device_scale_factor=1,
                    reduced_motion="no-preference",
                )
                page = context.new_page()
                page.goto(browser_origin, wait_until="domcontentloaded")
                page.wait_for_function("typeof window.openPage === 'function'")
                page.wait_for_timeout(800)
                if open_route:
                    page.evaluate("route => window.openPage(route)", open_route)
                    page.wait_for_selector(".mini-window-container.open")
                    page.wait_for_timeout(800)

                page.screenshot(path=destination, quality=86)
                browser.close()
        finally:
            server.should_exit = True
            server_thread.join(timeout=5)
            subprocess.run(
                ["git", "worktree", "remove", "--force", str(checkout)],
                cwd=REPOSITORY,
                check=True,
            )


def main() -> None:
    OUTPUT_DIRECTORY.mkdir(parents=True, exist_ok=True)
    for filename, commit, open_route in SNAPSHOTS:
        destination = OUTPUT_DIRECTORY / filename
        capture(commit, open_route, destination)
        print(f"Recovered {destination.relative_to(REPOSITORY)} from {commit}")


if __name__ == "__main__":
    main()
