import aiohttp
import asyncio
import os
import logging
from contextlib import suppress
from urllib.parse import urlparse
from typing import Dict, Any, Optional, AsyncGenerator
from fastapi import Request, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from aiohttp_socks import ProxyConnector
from core.config import settings
import time

logger = logging.getLogger(__name__)

IS_CLOUD_RUN = settings.K_SERVICE is not None
SOCKS5_PROXY = settings.SOCKS5_PROXY
MAC_SERVER_IP = settings.MAC_SERVER_IP
MAC_SERVER_PORT = settings.MAC_SERVER_PORT
CODE_SERVER_PORT = settings.CODE_SERVER_PORT


class BaseProxy:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"[{self.__class__.__name__}] Initialized for {self.base_url}")

    async def get_session(self) -> aiohttp.ClientSession:
        if self.session is None:
            connector = None
            if IS_CLOUD_RUN:
                connector = ProxyConnector.from_url(
                    SOCKS5_PROXY, limit=20, limit_per_host=20, force_close=False
                )
                logger.info(
                    f"[{self.__class__.__name__}] Using SOCKS5 proxy: {SOCKS5_PROXY}"
                )
            else:
                connector = aiohttp.TCPConnector(limit=20, force_close=False)

            # Allow long-running streaming responses with NO read timeout
            # OpenCode uses HTTP streaming for /message endpoint, not WebSocket
            # sock_read defaults to 15s which kills idle connections - disable it
            timeout = aiohttp.ClientTimeout(total=86400.0, connect=10.0, sock_read=None)
            self.session = aiohttp.ClientSession(
                connector=connector, timeout=timeout, auto_decompress=False
            )
        return self.session

    def _prepare_headers(self, request: Request) -> Dict[str, str]:
        excluded_headers = {
            "host",
            "connection",
            "content-length",
            "transfer-encoding",
            "upgrade",
        }

        headers = {}
        for k, v in request.headers.items():
            if k.lower() not in excluded_headers:
                headers[k] = v

        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            headers["x-forwarded-for"] = f"{x_forwarded_for}, {request.client.host}"
        else:
            headers["x-forwarded-for"] = request.client.host

        headers["X-Forwarded-Proto"] = request.url.scheme

        return headers

    async def proxy_request(
        self, request: Request, path: str, rewrite_body_callback=None
    ) -> StreamingResponse:
        session = await self.get_session()

        url = f"{self.base_url}/{path}"
        if request.url.query:
            url += f"?{request.url.query}"

        headers = self._prepare_headers(request)
        method = request.method.upper()
        data = request.stream()

        try:
            req_ctx = session.request(method, url, headers=headers, data=data)
            resp = await req_ctx.__aenter__()

            excluded_resp_headers = {
                "content-length",
                "transfer-encoding",
                "connection",
                "content-encoding",
            }
            response_headers = {}
            for k, v in resp.headers.items():
                if k.lower() not in excluded_resp_headers:
                    response_headers[k] = v

            if "service-worker" in path.lower() and path.endswith(".js"):
                response_headers["Service-Worker-Allowed"] = "/"

            if rewrite_body_callback:
                try:
                    try:
                        body = await resp.read()
                    except aiohttp.ClientPayloadError as e:
                        logger.warning(
                            f"[{self.__class__.__name__}] Incomplete payload read: {e}"
                        )
                        if hasattr(resp.content, "_buffer"):
                            body = b"".join(resp.content._buffer)
                        else:
                            body = b""
                finally:
                    await req_ctx.__aexit__(None, None, None)

                new_body, new_headers = await rewrite_body_callback(
                    body, resp.headers, path
                )

                new_headers_lower = {k.lower() for k in new_headers.keys()}
                for key in list(response_headers.keys()):
                    if key.lower() in new_headers_lower:
                        del response_headers[key]

                response_headers.update(new_headers)

                return StreamingResponse(
                    iter([new_body]), status_code=resp.status, headers=response_headers
                )
            else:
                if "Content-Encoding" in resp.headers:
                    response_headers["content-encoding"] = resp.headers[
                        "Content-Encoding"
                    ]

                is_sse = resp.headers.get("content-type", "").startswith(
                    "text/event-stream"
                )
                SSE_KEEPALIVE_INTERVAL = 15  # seconds

                async def content_iterator():
                    try:
                        if is_sse:
                            # SSE-aware streaming with keepalive comments.
                            # Prevents browser from closing idle stream during machine sleep,
                            # which would kill OpenCode's /global/event subscription silently.
                            # ": keepalive" is a valid SSE comment — clients ignore it but the stream stays alive.
                            while True:
                                try:
                                    chunk = await asyncio.wait_for(
                                        resp.content.readany(),
                                        timeout=SSE_KEEPALIVE_INTERVAL,
                                    )
                                    if not chunk:
                                        break  # upstream closed normally
                                    yield chunk
                                except asyncio.TimeoutError:
                                    logger.debug(
                                        f"[{self.__class__.__name__}] SSE keepalive sent on {url}"
                                    )
                                    yield b": keepalive\n\n"
                        else:
                            async for chunk in resp.content.iter_chunked(4096):
                                yield chunk
                    except aiohttp.ClientPayloadError as e:
                        logger.warning(
                            f"[{self.__class__.__name__}] Incomplete payload from upstream: {e}"
                        )
                    finally:
                        await req_ctx.__aexit__(None, None, None)

                return StreamingResponse(
                    content_iterator(),
                    status_code=resp.status,
                    headers=response_headers,
                    media_type=resp.headers.get("content-type"),
                )

        except aiohttp.ClientConnectorError:
            logger.error(f"[{self.__class__.__name__}] Connection failed to {url}")
            raise HTTPException(status_code=503, detail="Upstream service unavailable")
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Error proxying to {url}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def proxy_websocket(self, client_ws: WebSocket, path: str, target_base_url: str = None):
        base = (target_base_url or self.base_url).rstrip("/")
        # aiohttp.ws_connect accepts http:// directly — no need to convert to ws://
        ws_url = f"{base}/{path}"

        if client_ws.query_params:
            query_string = str(client_ws.url.query)
            if query_string:
                ws_url += f"?{query_string}"
                logger.debug(
                    f"[{self.__class__.__name__}] Forwarding query params: {query_string}"
                )

        parsed = urlparse(ws_url)

        # Strip WS-specific headers; aiohttp sets them automatically.
        # Keep everything else (cookies, auth headers, etc.) to forward to upstream.
        _strip = {
            "host", "origin", "connection", "upgrade",
            "sec-websocket-key", "sec-websocket-version",
            "sec-websocket-extensions", "sec-websocket-protocol",
        }
        headers = {k: v for k, v in client_ws.headers.items() if k.lower() not in _strip}
        scheme = "https" if parsed.scheme in ("https", "wss") else "http"
        port_part = f":{parsed.port}" if parsed.port else ""
        headers["Origin"] = f"{scheme}://{parsed.hostname}{port_part}"

        subprotocol_header = next(
            (v for k, v in client_ws.headers.items() if k.lower() == "sec-websocket-protocol"),
            None,
        )
        subprotocols = tuple(p.strip() for p in subprotocol_header.split(",")) if subprotocol_header else ()

        # Accept client immediately so the browser gets its 101 without waiting for upstream.
        # If upstream later fails, we close the already-accepted socket with code 1011.
        await client_ws.accept()
        logger.info(
            f"[{self.__class__.__name__}] Client accepted, connecting upstream: {ws_url} "
            f"(proxy={'SOCKS5' if IS_CLOUD_RUN else 'none'})"
        )

        # Use the existing aiohttp session which already has the SOCKS5 ProxyConnector
        # configured for Cloud Run — same path that successfully handles HTTP requests.
        session = await self.get_session()
        try:
            async with session.ws_connect(
                ws_url,
                headers=headers,
                protocols=subprotocols,
                heartbeat=20.0,  # send WS ping every 20s to keep connection alive
            ) as server_ws:
                logger.info(
                    f"[{self.__class__.__name__}] Connected to upstream. Protocol: {server_ws.protocol}"
                )

                async def forward_client_to_server():
                    try:
                        while True:
                            msg = await client_ws.receive()
                            if msg.get("type") == "websocket.disconnect":
                                logger.info(
                                    f"[{self.__class__.__name__}] Client disconnected"
                                )
                                break
                            if "text" in msg:
                                logger.debug(
                                    f"[{self.__class__.__name__}] C->S text: {msg['text'][:100]}"
                                )
                                await server_ws.send_str(msg["text"])
                            if "bytes" in msg:
                                logger.debug(
                                    f"[{self.__class__.__name__}] C->S binary: {len(msg['bytes'])} bytes"
                                )
                                await server_ws.send_bytes(msg["bytes"])
                    except WebSocketDisconnect:
                        logger.info(
                            f"[{self.__class__.__name__}] Client WebSocket disconnected normally"
                        )
                    except Exception as e:
                        logger.error(
                            f"[{self.__class__.__name__}] Client->Server error: {e}"
                        )

                async def forward_server_to_client():
                    try:
                        async for msg in server_ws:
                            if msg.type == aiohttp.WSMsgType.TEXT:
                                logger.debug(
                                    f"[{self.__class__.__name__}] S->C text: {len(msg.data)} chars"
                                )
                                await client_ws.send_text(msg.data)
                            elif msg.type == aiohttp.WSMsgType.BINARY:
                                logger.debug(
                                    f"[{self.__class__.__name__}] S->C binary: {len(msg.data)} bytes"
                                )
                                await client_ws.send_bytes(msg.data)
                            elif msg.type == aiohttp.WSMsgType.ERROR:
                                logger.error(
                                    f"[{self.__class__.__name__}] Server WS error: {server_ws.exception()}"
                                )
                                break
                            elif msg.type == aiohttp.WSMsgType.CLOSED:
                                logger.info(
                                    f"[{self.__class__.__name__}] Server WebSocket closed"
                                )
                                break
                            await asyncio.sleep(0)
                    except Exception as e:
                        logger.error(
                            f"[{self.__class__.__name__}] Server->Client error: {e}"
                        )

                t1 = asyncio.create_task(forward_client_to_server())
                t2 = asyncio.create_task(forward_server_to_client())
                done, pending = await asyncio.wait({t1, t2}, return_when=asyncio.FIRST_COMPLETED)
                for task in pending:
                    task.cancel()
                    with suppress(asyncio.CancelledError):
                        await task
                logger.info(f"[{self.__class__.__name__}] WebSocket session ended cleanly")

        except aiohttp.ClientConnectorError as e:
            logger.error(f"[{self.__class__.__name__}] Upstream WS connection failed: {e}")
            await client_ws.close(code=1011, reason="Upstream unavailable")
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] WS connection failed: {e}")
            with suppress(Exception):
                await client_ws.close(code=1011, reason=str(e))

    async def close(self):
        if self.session:
            await self.session.close()

    # Health-check helpers
    def get_health_endpoint(self) -> str:
        """Return the health-check endpoint path for this proxy/service.

        Subclasses should override this to point to their specific health URL.
        """
        return "/health"

    async def check_health(
        self, timeout: float = 5.0, retries: int = 3
    ) -> Dict[str, Any]:
        """Perform a lightweight, asynchronous health check against the service.

        - Uses the service-specific health endpoint as defined by get_health_endpoint().
        - Retries on failure up to `retries` times with a short backoff.
        - Returns a structured dict: { 'healthy': bool, 'service': str, 'response_time': float }
        - Gracefully handles failures so it doesn't raise exceptions for callers.
        """
        endpoint = self.get_health_endpoint()
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint
        url = f"{self.base_url.rstrip('/')}{endpoint}"
        service_name = self.__class__.__name__

        # Ensure we have an HTTP session (re-uses existing one)
        session = await self.get_session()

        # Time the request
        start_time = time.perf_counter()
        last_exception = None
        for attempt in range(1, retries + 1):
            try:
                # Apply per-request timeout to avoid blocking on slow services
                resp = await session.get(url, timeout=timeout)
                response_time = time.perf_counter() - start_time
                healthy = resp.status == 200
                # Consume/close response to avoid leaking connections
                try:
                    _ = await resp.json(content_type=None)
                except Exception:
                    pass
                await resp.release()
                if healthy:
                    return {
                        "healthy": True,
                        "service": service_name,
                        "response_time": response_time,
                    }
                # If non-200, continue to retry until attempts exhausted
            except Exception as e:
                last_exception = e
                # Small backoff before retrying
                await asyncio.sleep(0.2)

        # All attempts failed
        elapsed = time.perf_counter() - start_time
        logger.warning(
            f"[{service_name}] Health check failed after {retries} attempts: {type(last_exception).__name__}: {last_exception}"
        )
        return {"healthy": False, "service": service_name, "response_time": elapsed}
