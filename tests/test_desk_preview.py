"""The desk board preview stays off the live site, and nothing about Desk reaches a page."""

from __future__ import annotations

import http.server
import json
import threading

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from core import desk_board


def test_preview_is_not_mounted_on_the_site(client):
    assert client.get("/preview/desk-board").status_code == 404
    home = client.get("/").text
    assert "At my desk" not in home and "desk.css" not in home  # no board on any existing page


@pytest.fixture
def preview(monkeypatch) -> TestClient:
    monkeypatch.setenv("DESK_BOARD_URL", "https://desk.invalid/board")
    monkeypatch.setenv("DESK_BOARD_SECRET", "s3cret-value")
    import importlib

    from apis import route_desk_preview

    module = importlib.reload(route_desk_preview)
    module._live = desk_board.DeskBoard("https://desk.invalid/board", "s3cret-value", fetch=lambda u, s: {"working": 2})
    app = FastAPI()
    app.include_router(module.desk_preview_router)
    return TestClient(app)


def test_side_by_side_shows_three_options(preview):
    html = preview.get("/preview/desk-board").text
    for name in ("A · A few lines on Say hi", "B · A card inside the back cover", "C · A live sticker on the cover"):
        assert name in html
    assert "3 AI chats working right now" in html and "Resting right now" in html and "My desk is offline" in html


@pytest.mark.parametrize("option", ["a", "b", "c"])
@pytest.mark.parametrize("state", ["working", "resting", "offline", "empty", "live"])
def test_in_notebook_never_leaks_the_address_or_secret(preview, option, state):
    response = preview.get(f"/preview/desk-board/{option}?state={state}")
    assert response.status_code == 200
    assert "desk.invalid" not in response.text and "s3cret" not in response.text
    assert 'name="robots" content="noindex"' in response.text


def test_unknown_option_is_404(preview):
    assert preview.get("/preview/desk-board/z").status_code == 404
    assert preview.get("/preview/desk-board/a?state=nope").status_code == 404


def test_http_fetch_sends_the_bearer_secret_and_reads_json():
    seen = {}

    class Handler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802
            seen["auth"] = self.headers.get("Authorization")
            body = json.dumps({"working": 1, "gpu": "idle"}).encode()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = http.server.HTTPServer(("127.0.0.1", 0), Handler)
    threading.Thread(target=server.handle_request, daemon=True).start()
    try:
        payload = desk_board.http_fetch(f"http://127.0.0.1:{server.server_port}/board", "tok")
    finally:
        server.server_close()
    assert payload == {"working": 1, "gpu": "idle"}
    assert seen["auth"] == "Bearer tok"
