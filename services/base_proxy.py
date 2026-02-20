import aiohttp
import asyncio
import os
import logging
import websockets
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

    async def proxy_websocket(self, client_ws: WebSocket, path: str):
        ws_base = self.base_url.replace("http://", "ws://").replace(
            "https://", "wss://"
        )
        ws_url = f"{ws_base}/{path}"

        if client_ws.query_params:
            query_string = str(client_ws.url.query)
            if query_string:
                ws_url += f"?{query_string}"
                logger.info(
                    f"[{self.__class__.__name__}] Forwarding query params: {query_string}"
                )

        logger.info(f"[{self.__class__.__name__}] ====== WS PROXY DEBUG ======")
        logger.info(f"[{self.__class__.__name__}] Client URL: {client_ws.url}")
        logger.info(f"[{self.__class__.__name__}] Target URL: {ws_url}")
        logger.info(f"[{self.__class__.__name__}] Path param: {path}")
        logger.info(
            f"[{self.__class__.__name__}] Query params: {client_ws.query_params}"
        )
        logger.info(f"[{self.__class__.__name__}] About to configure proxy...")
        logger.info(f"[{self.__class__.__name__}] ==============================")

        proxy_url = None
        if IS_CLOUD_RUN:
            proxy_url = SOCKS5_PROXY
            logger.info(
                f"[{self.__class__.__name__}] Using websockets proxy: {proxy_url}"
            )

            try:
                import socket

                test_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                test_sock.settimeout(2)
                test_sock.connect(("127.0.0.1", 1055))
                test_sock.send(b"\x05\x01\x00")
                response = test_sock.recv(2)
                test_sock.close()
                logger.info(
                    f"[{self.__class__.__name__}] SOCKS5 handshake test: sent=\\x05\\x01\\x00, received={response.hex()}"
                )
                if response == b"\x05\x00":
                    logger.info(
                        f"[{self.__class__.__name__}] ✅ SOCKS5 protocol working!"
                    )
                else:
                    logger.warning(
                        f"[{self.__class__.__name__}] ⚠️ SOCKS5 unexpected response: {response.hex()}"
                    )
            except Exception as e:
                logger.error(
                    f"[{self.__class__.__name__}] ❌ SOCKS5 test failed: {type(e).__name__}: {e}"
                )

        try:
            logger.info(
                f"[{self.__class__.__name__}] Connecting to upstream WebSocket..."
            )

            sock = None
            if IS_CLOUD_RUN:
                try:
                    from python_socks.async_.asyncio import Proxy

                    logger.info(
                        f"[{self.__class__.__name__}] Connecting to proxy: {SOCKS5_PROXY}"
                    )
                    proxy = Proxy.from_url(SOCKS5_PROXY)

                    from urllib.parse import urlparse

                    parsed = urlparse(ws_url)
                    target_host = parsed.hostname
                    target_port = parsed.port or (443 if parsed.scheme == "wss" else 80)

                    logger.info(
                        f"[{self.__class__.__name__}] Establish tunnel to {target_host}:{target_port}"
                    )

                    sock = await proxy.connect(
                        dest_host=target_host, dest_port=target_port
                    )
                    logger.info(
                        f"[{self.__class__.__name__}] ✅ SOCKS5 tunnel established"
                    )

                except Exception as e:
                    logger.error(
                        f"[{self.__class__.__name__}] ❌ Failed to create proxy tunnel: {e}"
                    )
                    raise

            ws_kwargs = {
                "open_timeout": 20,
                "ping_interval": 20,  # Send ping every 20s to keep SOCKS5 tunnel alive
                "ping_timeout": 60,  # Wait up to 60s for pong (generous for SOCKS5)
            }
            if sock:
                ws_kwargs["sock"] = sock
                logger.info(f"[{self.__class__.__name__}] Connecting via SOCKS5 tunnel")
            else:
                headers = dict(client_ws.headers.items())
                from urllib.parse import urlparse

                parsed = urlparse(ws_url)

                for key in list(headers.keys()):
                    if key.lower() in ["host", "origin"]:
                        del headers[key]

                headers["Host"] = f"{parsed.hostname}:{parsed.port}"

                scheme = "https" if parsed.scheme == "wss" else "http"
                headers["Origin"] = f"{scheme}://{parsed.hostname}:{parsed.port}"

                subprotocol_header = None
                for key, val in client_ws.headers.items():
                    if key.lower() == "sec-websocket-protocol":
                        subprotocol_header = val
                        break

                subprotocols = []
                if subprotocol_header:
                    subprotocols = [p.strip() for p in subprotocol_header.split(",")]
                    logger.info(
                        f"[{self.__class__.__name__}] Extracted subprotocols: {subprotocols}"
                    )
                else:
                    logger.warning(
                        f"[{self.__class__.__name__}] No sec-websocket-protocol in headers: {list(client_ws.headers.keys())}"
                    )

                for key in list(headers.keys()):
                    if key.lower() in [
                        "connection",
                        "upgrade",
                        "sec-websocket-key",
                        "sec-websocket-version",
                        "sec-websocket-extensions",
                        "sec-websocket-protocol",
                    ]:
                        del headers[key]

                ws_kwargs["additional_headers"] = headers
                if subprotocols:
                    ws_kwargs["subprotocols"] = subprotocols
                logger.info(
                    f"[{self.__class__.__name__}] Rewrote headers. Host: {headers.get('Host')}, Origin: {headers.get('Origin')}, Subprotocols: {subprotocols}"
                )

            # Disable proxy auto-detection in websockets v15 (default proxy=True picks up
            # system HTTP_PROXY env var, which can interfere with local ws://127.0.0.1 connections)
            ws_kwargs["proxy"] = None

            async with websockets.connect(ws_url, **ws_kwargs) as server_ws:
                logger.info(
                    f"[{self.__class__.__name__}] ✅ Connected! Subprotocol selected: {server_ws.subprotocol}"
                )

                await client_ws.accept(subprotocol=server_ws.subprotocol)
                logger.info(
                    f"[{self.__class__.__name__}] ✅ Client WebSocket accepted with subprotocol: {server_ws.subprotocol}"
                )

                message_count = {"client_to_server": 0, "server_to_client": 0}

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
                                message_count["client_to_server"] += 1
                                if message_count["client_to_server"] <= 3:
                                    logger.info(
                                        f"[{self.__class__.__name__}] C->S text msg #{message_count['client_to_server']}: {msg['text'][:100]}"
                                    )
                                await server_ws.send(msg["text"])
                            if "bytes" in msg:
                                message_count["client_to_server"] += 1
                                if message_count["client_to_server"] <= 3:
                                    logger.info(
                                        f"[{self.__class__.__name__}] C->S binary msg #{message_count['client_to_server']}: {len(msg['bytes'])} bytes"
                                    )
                                await server_ws.send(msg["bytes"])
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
                            message_count["server_to_client"] += 1

                            # Enhanced logging to diagnose UI freeze issue
                            msg_type = (
                                "TEXT"
                                if isinstance(msg, str)
                                else "BINARY"
                                if isinstance(msg, bytes)
                                else "UNKNOWN"
                            )
                            msg_len = len(msg) if isinstance(msg, (str, bytes)) else 0
                            logger.info(
                                f"[{self.__class__.__name__}] S->C #{message_count['server_to_client']}: {msg_type} ({msg_len} bytes) received from server"
                            )

                            if isinstance(msg, str):
                                await client_ws.send_text(msg)
                                logger.info(
                                    f"[{self.__class__.__name__}] S->C #{message_count['server_to_client']}: TEXT sent to client"
                                )
                            elif isinstance(msg, bytes):
                                # IMPORTANT: Ensure we send bytes as binary frame
                                await client_ws.send_bytes(msg)
                                logger.info(
                                    f"[{self.__class__.__name__}] S->C #{message_count['server_to_client']}: BINARY sent to client"
                                )
                            else:
                                logger.warning(
                                    f"[{self.__class__.__name__}] S->C #{message_count['server_to_client']}: Unknown msg type: {type(msg)}"
                                )

                            # Force event loop to process send before next message
                            # Prevents message batching that could confuse OpenCode UI
                            await asyncio.sleep(0)

                    except websockets.exceptions.ConnectionClosed as e:
                        logger.info(
                            f"[{self.__class__.__name__}] Server WebSocket closed: {e}"
                        )
                    except Exception as e:
                        logger.error(
                            f"[{self.__class__.__name__}] Server->Client error: {e}"
                        )

                await asyncio.gather(
                    forward_client_to_server(), forward_server_to_client()
                )

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] WS Connection failed: {e}")
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
        logger = logging.getLogger(__name__)
        logger.warning(
            f"[{service_name}] Health check failed after {retries} attempts: {type(last_exception).__name__}: {last_exception}"
        )
        return {"healthy": False, "service": service_name, "response_time": elapsed}
