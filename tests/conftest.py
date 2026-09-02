from collections.abc import Iterator
import os
import socket
import threading
import time

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Page, sync_playwright
import uvicorn

from main import app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app, base_url="http://testserver") as test_client:
        yield test_client


@pytest.fixture(scope="session")
def live_server_url() -> Iterator[str]:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        port = listener.getsockname()[1]

    server = uvicorn.Server(
        uvicorn.Config(app, host="0.0.0.0", port=port, log_level="error")
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    deadline = time.monotonic() + 10
    while not server.started and time.monotonic() < deadline:
        time.sleep(0.05)
    if not server.started:
        raise RuntimeError("Portfolio test server did not start")

    browser_host = os.environ.get("PLAYWRIGHT_BROWSER_HOST", "127.0.0.1")
    try:
        yield f"http://{browser_host}:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)


@pytest.fixture
def browser_page(live_server_url: str) -> Iterator[tuple[Page, str]]:
    endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
    with sync_playwright() as playwright:
        browser = (
            playwright.chromium.connect(endpoint)
            if endpoint
            else playwright.chromium.launch(headless=True)
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()
        try:
            yield page, live_server_url
        finally:
            context.close()
            browser.close()
