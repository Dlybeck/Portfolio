from collections.abc import Callable, Iterator
import os
import socket
import threading
import time

import pytest
from fastapi.testclient import TestClient
from playwright.sync_api import Browser, BrowserContext, Page, sync_playwright
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


@pytest.fixture(scope="session")
def browser() -> Iterator[Browser]:
    """One browser for the whole run (one per xdist worker); tests get fresh contexts."""
    endpoint = os.environ.get("PLAYWRIGHT_WS_ENDPOINT")
    with sync_playwright() as playwright:
        shared = (
            playwright.chromium.connect(endpoint)
            if endpoint
            else playwright.chromium.launch(headless=True)
        )
        try:
            yield shared
        finally:
            shared.close()


@pytest.fixture
def new_page(browser: Browser) -> Iterator[Callable[..., Page]]:
    """Open a page in its own fresh context; every context closes after the test."""
    contexts: list[BrowserContext] = []

    def make(**context_options) -> Page:
        context = browser.new_context(**context_options)
        contexts.append(context)
        return context.new_page()

    try:
        yield make
    finally:
        for context in contexts:
            context.close()


@pytest.fixture
def browser_page(new_page, live_server_url: str) -> tuple[Page, str]:
    return new_page(viewport={"width": 1440, "height": 900}), live_server_url


@pytest.fixture
def mobile_browser_page(new_page, live_server_url: str) -> tuple[Page, str]:
    page = new_page(viewport={"width": 390, "height": 844}, is_mobile=True, has_touch=True)
    return page, live_server_url


BROWSER_FIXTURES = {"browser", "new_page", "browser_page", "mobile_browser_page"}


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Tag every test that drives a real browser, so `-m "not browser"` is the quick run."""
    for item in items:
        if BROWSER_FIXTURES & set(getattr(item, "fixturenames", ())):
            item.add_marker(pytest.mark.browser)
