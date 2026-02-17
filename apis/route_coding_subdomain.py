"""Environment-aware coding subdomain routing middleware.

Reads the CODING_SERVICE environment variable to select which coding service
to proxy to (default: openhands). Uses the coding service factory for dynamic
service selection.

Supported values for CODING_SERVICE:
  - "openhands" (default when env var is unset)
  - "opencode"
"""

import os
import time
import logging
from urllib.parse import parse_qs
from typing import Literal

from fastapi import Request
from fastapi.responses import RedirectResponse, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket as StarletteWebSocket

from services.coding_service_factory import get_coding_service
from services.openhands_web_proxy import get_openhands_proxy
from services.opencode_web_proxy import get_opencode_proxy
from core.dev_utils import extract_token

logger = logging.getLogger(__name__)

_STATIC_EXTENSIONS = frozenset(
    {
        ".js",
        ".css",
        ".woff",
        ".woff2",
        ".ttf",
        ".otf",
        ".eot",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".webp",
        ".map",
        ".json",
    }
)

PathKind = Literal["static_asset", "api", "html", "websocket", "other"]


def _classify_request_path(path: str) -> PathKind:
    lower = path.lower()

    if lower.startswith("/ws") or lower.startswith("/socket.io"):
        return "websocket"

    if lower.startswith("/api/") or lower.startswith("/global/"):
        return "api"

    if any(lower.endswith(ext) for ext in _STATIC_EXTENSIONS):
        return "static_asset"

    if lower.endswith(".html") or lower in {"/", ""}:
        return "html"

    return "other"


def _resolve_service_name() -> str:
    raw = (os.environ.get("CODING_SERVICE") or "").strip().lower()
    return raw or "openhands"


def _get_proxy_for_service(service_name: str):
    if service_name == "opencode":
        return get_opencode_proxy()
    if service_name == "openhands":
        return get_openhands_proxy()
    raise ValueError(f"Unknown service '{service_name}'")


def _get_health_endpoint(service_name: str) -> str:
    cfg = get_coding_service(service_name)
    return cfg["health_endpoint"]


class CodingSubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")

        if "opencode.davidlybeck.com" in host or "opencode." in host:
            service_name = _resolve_service_name()
            path = request.url.path
            path_kind = _classify_request_path(path)
            start_time = time.monotonic()

            logger.info(
                "[%s] %s %s (kind=%s)",
                service_name,
                request.method,
                path,
                path_kind,
            )

            health_endpoint = _get_health_endpoint(service_name)

            if path == health_endpoint:
                try:
                    proxy = _get_proxy_for_service(service_name)
                    response = await proxy.proxy_request(request, path.lstrip("/"))
                    response.headers["X-Service-Name"] = service_name
                    elapsed = time.monotonic() - start_time
                    logger.debug("[%s] health check OK (%.3fs)", service_name, elapsed)
                    return response
                except Exception as exc:
                    logger.error("[%s] health check unavailable: %s", service_name, exc)
                    return Response(
                        content=(
                            f"Coding service '{service_name}' is currently unavailable. "
                            "Please try again later."
                        ),
                        status_code=503,
                        media_type="text/plain",
                        headers={"X-Service-Name": service_name},
                    )

            token = extract_token(request)
            if not token:
                return_url = str(request.url)
                login_url = f"https://davidlybeck.com/dev/login?redirect={return_url}"
                logger.warning("[%s] unauthenticated access: %s", service_name, path)
                return RedirectResponse(url=login_url, status_code=307)

            try:
                proxy = _get_proxy_for_service(service_name)
                response = await proxy.proxy_request(request, path.lstrip("/"))
                response.headers["X-Service-Name"] = service_name
                elapsed = time.monotonic() - start_time
                logger.info(
                    "[%s] %s %s → %s (%.3fs, kind=%s)",
                    service_name,
                    request.method,
                    path,
                    getattr(response, "status_code", "?"),
                    elapsed,
                    path_kind,
                )
                return response
            except Exception as exc:
                elapsed = time.monotonic() - start_time
                logger.error(
                    "[%s] proxy error after %.3fs: %s",
                    service_name,
                    elapsed,
                    exc,
                    exc_info=True,
                )
                return Response(
                    content=(
                        f"Coding service '{service_name}' is currently unavailable. "
                        "Set the CODING_SERVICE environment variable to switch services. "
                        f"Error: {exc}"
                    ),
                    status_code=503,
                    media_type="text/plain",
                    headers={"X-Service-Name": service_name},
                )

        return await call_next(request)


class CodingWebSocketMiddleware:
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send):
        if scope["type"] == "websocket":
            headers_dict = {k.decode(): v.decode() for k, v in scope.get("headers", [])}
            host = headers_dict.get("host", "")
            path = scope["path"]

            logger.info(
                "CodingWebSocketMiddleware: connection host=%s path=%s", host, path
            )

            if "opencode.davidlybeck.com" in host or "opencode." in host:
                service_name = _resolve_service_name()
                logger.info(
                    "CodingWebSocketMiddleware: routing WebSocket to service='%s' "
                    "(CODING_SERVICE=%r), path=%s",
                    service_name,
                    os.environ.get("CODING_SERVICE"),
                    path,
                )

                query_string = scope.get("query_string", b"").decode()
                query_params = parse_qs(query_string)

                token = None

                if "tkn" in query_params:
                    token = query_params["tkn"][0]

                if not token:
                    cookie_header = headers_dict.get("cookie", "")
                    if "session_token=" in cookie_header:
                        for cookie_part in cookie_header.split(";"):
                            cookie_part = cookie_part.strip()
                            if cookie_part.startswith("session_token="):
                                token = cookie_part.split("=", 1)[1]
                                break

                if not token:
                    logger.warning(
                        "Unauthenticated WebSocket attempt to coding subdomain: %s",
                        path,
                    )
                    websocket = StarletteWebSocket(scope, receive=receive, send=send)
                    await websocket.close(code=1008, reason="Not authenticated")
                    return

                logger.info(
                    "Authenticated WebSocket to coding subdomain via '%s': %s",
                    service_name,
                    path,
                )

                if path.startswith("/pty/"):
                    logger.info(
                        "[%s] PTY WebSocket via local router: %s", service_name, path
                    )
                    await self.app(scope, receive, send)
                    return

                websocket = StarletteWebSocket(scope, receive=receive, send=send)
                path_clean = path.lstrip("/")

                logger.info("Proxying WebSocket to '%s': %s", service_name, path_clean)

                try:
                    proxy = _get_proxy_for_service(service_name)
                    await proxy.proxy_websocket(websocket, path_clean)
                except Exception as exc:
                    logger.error(
                        "WebSocket proxy error for service '%s': %s",
                        service_name,
                        exc,
                        exc_info=True,
                    )
                    try:
                        await websocket.close(code=1011, reason=str(exc))
                    except Exception:
                        pass
                return

        await self.app(scope, receive, send)


coding_subdomain_middleware = CodingSubdomainMiddleware
coding_subdomain_ws_middleware = CodingWebSocketMiddleware
