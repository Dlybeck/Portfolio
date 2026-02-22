"""Environment-aware coding subdomain routing middleware.

Reads the CODING_SERVICE environment variable to select which coding service
to proxy to (default: openhands). Uses the coding service factory for dynamic
service selection.

Supported values for CODING_SERVICE:
  - "openhands" (default when env var is unset)
  - Legacy "opencode" hostnames are automatically mapped to "openhands"
"""

import os
import re
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

from services.base_proxy import IS_CLOUD_RUN, MAC_SERVER_IP

from core.dev_utils import extract_token

# Matches /sockets/events/{conversation_id} — OpenHands V1 agent server WebSocket path
_SOCKETS_EVENTS_RE = re.compile(r'^/sockets/events/([^/?]+)')

# Conversation ID extracted from a Referer URL like /conversations/{id}
_REFERER_CONV_RE = re.compile(r'/conversations/([^/?#]+)')

# Path prefixes served by the agent server (not by port 3000).
# Port 3000 falls through to the React SPA for these, returning HTML instead of JSON.
_AGENT_API_PREFIXES = (
    "api/git/",
    "api/list-files",
    "api/save-file",
    "api/select-file",
    "api/refresh-files",
)

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


def _resolve_service_name(host: str = None) -> str:
    # Infer service from hostname if possible
    if host:
        if "opencode." in host:
            logger.debug(f"Mapping legacy 'opencode' host to 'openhands': {host}")
            return "openhands"
        if "openhands." in host:
            logger.debug(f"Inferred service 'openhands' from host: {host}")
            return "openhands"
    # Fall back to environment variable
    raw = (os.environ.get("CODING_SERVICE") or "").strip().lower()
    service = raw or "openhands"
    # Map legacy 'opencode' service name to 'openhands'
    if service == "opencode":
        logger.debug(f"Mapping legacy service name 'opencode' to 'openhands'")
        service = "openhands"
    logger.debug(f"Resolved service '{service}' from CODING_SERVICE env var (host: {host})")
    return service


def _get_proxy_for_service(service_name: str):
    if service_name == "openhands":
        return get_openhands_proxy()
    raise ValueError(f"Unknown service '{service_name}'")


def _get_health_endpoint(service_name: str) -> str:
    cfg = get_coding_service(service_name)
    return cfg["health_endpoint"]


def _find_agent_url(request: Request, openhands_proxy) -> str | None:
    """Resolve the agent server base URL for this request.

    1. Try to extract the conversation ID from the Referer header
       (e.g. Referer: https://opencode.davidlybeck.com/conversations/<id>)
    2. Fall back to the cached URL when exactly one conversation is active.
    Returns None if no agent URL can be determined.
    """
    referer = request.headers.get("referer", "")
    if referer:
        m = _REFERER_CONV_RE.search(referer)
        if m:
            conv_id = m.group(1)
            url = openhands_proxy.get_agent_url(conv_id)
            if url:
                logger.debug("[OpenHands] Agent URL from Referer conv %s: %s", conv_id, url)
                return url
    # Single-conversation fallback
    url = openhands_proxy.get_fallback_agent_url()
    if url:
        logger.debug("[OpenHands] Agent URL from fallback cache: %s", url)
    return url


class CodingSubdomainMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        host = request.headers.get("host", "")

        if "opencode.davidlybeck.com" in host or "opencode." in host:
            service_name = _resolve_service_name(host)
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
                path_clean = path.lstrip("/")

                # Agent-server API routing: paths like /api/git/*, /api/list-files, etc.
                # are served by the per-conversation agent server (random port), NOT by
                # port 3000. Port 3000 falls through to the React SPA for these, returning
                # HTML instead of JSON → "Invalid response from runtime" in the UI.
                override_url = None
                if service_name == "openhands" and any(
                    path_clean.startswith(p) for p in _AGENT_API_PREFIXES
                ):
                    agent_url = _find_agent_url(request, get_openhands_proxy())
                    if agent_url:
                        override_url = (
                            agent_url.replace("localhost", MAC_SERVER_IP)
                            if IS_CLOUD_RUN
                            else agent_url
                        )
                        logger.info(
                            "[%s] routing %s → agent server %s",
                            service_name, path, override_url,
                        )

                response = await proxy.proxy_request(request, path_clean, override_base_url=override_url)
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
                service_name = _resolve_service_name(host)
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
                elif "session_api_key" in query_params:
                    token = query_params["session_api_key"][0]

                if not token:
                    cookie_header = headers_dict.get("cookie", "")
                    if "session_token=" in cookie_header:
                        for cookie_part in cookie_header.split(";"):
                            cookie_part = cookie_part.strip()
                            if cookie_part.startswith("session_token="):
                                token = cookie_part.split("=", 1)[1]
                                break

                logger.debug(f"WebSocket token extracted: {'<present>' if token else '<missing'}")
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

                # OpenHands V1: agent server runs on a random port separate from port 3000.
                # The browser builds ws://localhost:PORT/sockets/events/{id} from the conversation
                # URL — unreachable from the user's browser.  We rewrite conversation URLs in
                # JSON responses to point at our proxy, then here we look up the real agent URL
                # and forward the WebSocket directly to the agent server port.
                target_base_url = None
                if service_name == "openhands":
                    m = _SOCKETS_EVENTS_RE.match(path)
                    if m:
                        conv_id = m.group(1)
                        logger.info(f"[OpenHands] WebSocket for conversation {conv_id}")
                        openhands_proxy = get_openhands_proxy()
                        agent_url = openhands_proxy.get_agent_url(conv_id)
                        logger.info(f"[OpenHands] Cached agent_url for {conv_id}: {agent_url}")
                        if not agent_url:
                            # Cache miss — fetch directly (handles proxy restarts / race conditions)
                            logger.info(f"[OpenHands] Cache miss, fetching agent URL for {conv_id}")
                            agent_url = await openhands_proxy.fetch_agent_url(conv_id)
                            logger.info(f"[OpenHands] Fetched agent_url for {conv_id}: {agent_url}")
                        if agent_url:
                            # On Cloud Run, tailscaled's SOCKS5 server resolves "localhost"
                            # to 127.0.0.1 on the container itself — not the Mac. We must
                            # use MAC_SERVER_IP (Tailscale IP) so the CONNECT target routes
                            # through Tailscale to the Mac's agent server port.
                            target_base_url = (
                                agent_url.replace("localhost", MAC_SERVER_IP)
                                if IS_CLOUD_RUN
                                else agent_url
                            )
                            # base_proxy.proxy_websocket handles http:// → ws:// conversion
                            logger.info(
                                "[OpenHands] /sockets/events/%s: agent_url=%r → target=%r",
                                conv_id, agent_url, target_base_url,
                            )
                        else:
                            logger.error(
                                "[OpenHands] No agent URL for conversation %s — closing WS. "
                                "Reload the page to re-populate the agent URL cache.",
                                conv_id,
                            )
                            await websocket.close(code=4001, reason="Agent not ready — please reload")
                            return

                logger.info("Proxying WebSocket to '%s': %s", service_name, path_clean)

                try:
                    proxy = _get_proxy_for_service(service_name)
                    await proxy.proxy_websocket(websocket, path_clean, target_base_url=target_base_url)
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
