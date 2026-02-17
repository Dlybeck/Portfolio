import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.testclient import TestClient

from apis.route_coding_subdomain import (
    _classify_request_path,
    _resolve_service_name,
    CodingSubdomainMiddleware,
)


# ── _classify_request_path ────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "path,expected",
    [
        ("/app.js", "static_asset"),
        ("/styles.css", "static_asset"),
        ("/fonts/roboto.woff2", "static_asset"),
        ("/logo.png", "static_asset"),
        ("/api/health", "api"),
        ("/api/sessions", "api"),
        ("/global/health", "api"),
        ("/global/event", "api"),
        ("/ws", "websocket"),
        ("/ws/data", "websocket"),
        ("/socket.io/", "websocket"),
        ("/", "html"),
        ("", "html"),
        ("/index.html", "html"),
        ("/dashboard", "other"),
        ("/pty/1/abc", "other"),
    ],
)
def test_classify_request_path(path, expected):
    assert _classify_request_path(path) == expected


# ── _resolve_service_name ─────────────────────────────────────────────────────


def test_resolve_service_name_defaults_to_openhands(monkeypatch):
    monkeypatch.delenv("CODING_SERVICE", raising=False)
    assert _resolve_service_name() == "openhands"


def test_resolve_service_name_blank_defaults_to_openhands(monkeypatch):
    monkeypatch.setenv("CODING_SERVICE", "   ")
    assert _resolve_service_name() == "openhands"


def test_resolve_service_name_opencode(monkeypatch):
    monkeypatch.setenv("CODING_SERVICE", "opencode")
    assert _resolve_service_name() == "opencode"


def test_resolve_service_name_normalises_case(monkeypatch):
    monkeypatch.setenv("CODING_SERVICE", "  OpenCode  ")
    assert _resolve_service_name() == "opencode"


# ── middleware: X-Service-Name header and routing ─────────────────────────────


def _make_app(service_name: str, proxy_status: int = 200, raise_exc: bool = False):
    """Build a minimal ASGI app with CodingSubdomainMiddleware for testing."""
    inner = FastAPI()

    @inner.get("/{path:path}")
    @inner.post("/{path:path}")
    async def fallthrough():
        return {"ok": True}

    inner.add_middleware(CodingSubdomainMiddleware)

    fake_response = StreamingResponse(
        iter([b"hello"]),
        status_code=proxy_status,
        headers={"content-type": "text/plain"},
    )

    async def _mock_proxy(request, path):
        if raise_exc:
            raise OSError("connection refused")
        return fake_response

    return inner, _mock_proxy


def _get_client(service_name: str, proxy_status: int = 200, raise_exc: bool = False):
    app, mock_proxy = _make_app(service_name, proxy_status, raise_exc)

    with (
        patch(
            "apis.route_coding_subdomain._resolve_service_name",
            return_value=service_name,
        ),
        patch("apis.route_coding_subdomain._get_proxy_for_service") as mock_get_proxy,
        patch("apis.route_coding_subdomain.extract_token", return_value="valid-token"),
    ):
        proxy_instance = MagicMock()
        proxy_instance.proxy_request = AsyncMock(side_effect=mock_proxy)
        mock_get_proxy.return_value = proxy_instance
        yield app, mock_get_proxy, proxy_instance


@pytest.fixture
def opencode_client():
    with (
        patch(
            "apis.route_coding_subdomain._resolve_service_name", return_value="opencode"
        ),
        patch("apis.route_coding_subdomain._get_proxy_for_service") as mock_get_proxy,
        patch("apis.route_coding_subdomain.extract_token", return_value="tok"),
    ):
        proxy_instance = MagicMock()
        proxy_instance.proxy_request = AsyncMock(
            return_value=StreamingResponse(
                iter([b"data"]),
                status_code=200,
                headers={"content-type": "text/plain"},
            )
        )
        mock_get_proxy.return_value = proxy_instance

        app = FastAPI()

        @app.get("/{path:path}")
        @app.post("/{path:path}")
        async def _fallthrough():
            return {"ok": True}

        app.add_middleware(CodingSubdomainMiddleware)

        client = TestClient(app, base_url="http://opencode.davidlybeck.com")
        yield client, proxy_instance


def test_x_service_name_header_present(opencode_client):
    client, _ = opencode_client
    resp = client.get("/")
    assert "x-service-name" in resp.headers
    assert resp.headers["x-service-name"] == "opencode"


def test_get_request_routed(opencode_client):
    client, proxy = opencode_client
    client.get("/some/path")
    proxy.proxy_request.assert_called_once()
    _, call_path = proxy.proxy_request.call_args.args
    assert call_path == "some/path"


def test_post_request_routed(opencode_client):
    client, proxy = opencode_client
    client.post("/api/messages", json={"text": "hello"})
    proxy.proxy_request.assert_called_once()


def test_503_when_service_unavailable():
    with (
        patch(
            "apis.route_coding_subdomain._resolve_service_name",
            return_value="openhands",
        ),
        patch("apis.route_coding_subdomain._get_proxy_for_service") as mock_get_proxy,
        patch("apis.route_coding_subdomain.extract_token", return_value="tok"),
    ):
        proxy_instance = MagicMock()
        proxy_instance.proxy_request = AsyncMock(side_effect=OSError("refused"))
        mock_get_proxy.return_value = proxy_instance

        app = FastAPI()

        @app.get("/{path:path}")
        async def _():
            return {}

        app.add_middleware(CodingSubdomainMiddleware)

        client = TestClient(
            app,
            base_url="http://opencode.davidlybeck.com",
            raise_server_exceptions=False,
        )
        resp = client.get("/dashboard")
        assert resp.status_code == 503
        assert "x-service-name" in resp.headers
        assert resp.headers["x-service-name"] == "openhands"


def test_unauthenticated_redirects_to_login():
    with (
        patch(
            "apis.route_coding_subdomain._resolve_service_name",
            return_value="openhands",
        ),
        patch("apis.route_coding_subdomain.extract_token", return_value=None),
    ):
        app = FastAPI()

        @app.get("/{path:path}")
        async def _():
            return {}

        app.add_middleware(CodingSubdomainMiddleware)

        client = TestClient(
            app, base_url="http://opencode.davidlybeck.com", follow_redirects=False
        )
        resp = client.get("/private")
        assert resp.status_code == 307
        assert "login" in resp.headers["location"]


def test_health_endpoint_bypasses_auth():
    with (
        patch(
            "apis.route_coding_subdomain._resolve_service_name", return_value="opencode"
        ),
        patch(
            "apis.route_coding_subdomain._get_health_endpoint",
            return_value="/global/health",
        ),
        patch("apis.route_coding_subdomain._get_proxy_for_service") as mock_get_proxy,
        patch("apis.route_coding_subdomain.extract_token", return_value=None),
    ):
        proxy_instance = MagicMock()
        proxy_instance.proxy_request = AsyncMock(
            return_value=StreamingResponse(
                iter([b'{"healthy":true}']),
                status_code=200,
                headers={"content-type": "application/json"},
            )
        )
        mock_get_proxy.return_value = proxy_instance

        app = FastAPI()

        @app.get("/{path:path}")
        async def _():
            return {}

        app.add_middleware(CodingSubdomainMiddleware)

        client = TestClient(app, base_url="http://opencode.davidlybeck.com")
        resp = client.get("/global/health")
        assert resp.status_code == 200
        assert resp.headers.get("x-service-name") == "opencode"


def test_non_coding_host_passes_through():
    with patch("apis.route_coding_subdomain.extract_token", return_value=None):
        app = FastAPI()

        @app.get("/test")
        async def _():
            return {"pass": True}

        app.add_middleware(CodingSubdomainMiddleware)

        client = TestClient(app, base_url="http://davidlybeck.com")
        resp = client.get("/test")
        assert resp.status_code == 200
        assert resp.json() == {"pass": True}
