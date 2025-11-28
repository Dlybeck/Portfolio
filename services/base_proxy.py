"""
Base Proxy Service for Tailscale/SOCKS5 Connections
Centralizes logic for:
- aiohttp session management
- SOCKS5 proxy negotiation (for Cloud Run)
- Header filtering/normalization
- Streaming responses
- WebSocket tunneling (using websockets library)
"""

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

# Configure logging
logger = logging.getLogger(__name__)

# Detect if running in Cloud Run (proxy mode) or locally (direct mode)
IS_CLOUD_RUN = settings.K_SERVICE is not None
SOCKS5_PROXY = settings.SOCKS5_PROXY
MAC_SERVER_IP = settings.MAC_SERVER_IP
MAC_SERVER_PORT = settings.MAC_SERVER_PORT

class BaseProxy:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        self.session: Optional[aiohttp.ClientSession] = None
        logger.info(f"[{self.__class__.__name__}] Initialized for {self.base_url}")

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp ClientSession with SOCKS5 proxy if in Cloud Run"""
        if self.session is None:
            connector = None
            if IS_CLOUD_RUN:
                # Use aiohttp-socks for SOCKS5 proxy
                connector = ProxyConnector.from_url(
                    SOCKS5_PROXY,
                    limit=20,
                    limit_per_host=20,
                    force_close=True # Disable keep-alive at connection level
                )
                logger.info(f"[{self.__class__.__name__}] Using SOCKS5 proxy: {SOCKS5_PROXY}")
            else:
                connector = aiohttp.TCPConnector(limit=20, force_close=True)

            # Create session with timeouts
            # 300s (5min) total timeout to match Cloud Run limits, 10s connect timeout
            timeout = aiohttp.ClientTimeout(total=300.0, connect=10.0)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                auto_decompress=False # Stream raw bytes
            )
        return self.session

    def _prepare_headers(self, request: Request) -> Dict[str, str]:
        """Prepare headers for proxying, filtering out hop-by-hop headers"""
        # Normalize and filter headers
        # Case-insensitive filtering
        excluded_headers = {
            'host', 
            'connection', 
            'content-length', 
            'transfer-encoding', 
            'upgrade',
            # 'accept-encoding' # We preserve this to allow Gzip/Brotli if supported
        }
        
        headers = {}
        for k, v in request.headers.items():
            if k.lower() not in excluded_headers:
                headers[k] = v

        # Force Gzip if we suspect Brotli issues (can be overridden by subclasses)
        # headers['accept-encoding'] = 'gzip'

        # Add X-Forwarded headers
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            headers["x-forwarded-for"] = f"{x_forwarded_for}, {request.client.host}"
        else:
            headers["x-forwarded-for"] = request.client.host
            
        headers['X-Forwarded-Proto'] = request.url.scheme
        
        return headers

    async def proxy_request(
        self,
        request: Request,
        path: str,
        rewrite_body_callback=None
    ) -> StreamingResponse:
        """
        Generic proxy request handler.
        
        Args:
            request: The incoming FastAPI request
            path: The path to proxy to
            rewrite_body_callback: Optional async function to process the body (requires buffering)
        """
        session = await self.get_session()
        
        # Build target URL
        url = f"{self.base_url}/{path}"
        if request.url.query:
            url += f"?{request.url.query}"

        headers = self._prepare_headers(request)
        method = request.method.upper()
        data = request.stream()

        try:
            # Create request context
            req_ctx = session.request(method, url, headers=headers, data=data)
            resp = await req_ctx.__aenter__()

            # Prepare response headers
            excluded_resp_headers = {'content-length', 'transfer-encoding', 'connection', 'content-encoding'}
            response_headers = {}
            for k, v in resp.headers.items():
                if k.lower() not in excluded_resp_headers:
                    response_headers[k] = v

            # Decide whether to stream or buffer & rewrite
            if rewrite_body_callback:
                try:
                    # Buffer full response for rewriting
                    body = await resp.read()
                finally:
                    await req_ctx.__aexit__(None, None, None)
                
                # Perform rewriting
                new_body, new_headers = await rewrite_body_callback(body, resp.headers, path)
                
                # Merge new headers
                response_headers.update(new_headers)
                
                return StreamingResponse(
                    iter([new_body]),
                    status_code=resp.status,
                    headers=response_headers
                )
            else:
                # Pure Streaming
                # Re-add content-encoding if we are streaming raw compressed data
                if 'Content-Encoding' in resp.headers:
                    response_headers['content-encoding'] = resp.headers['Content-Encoding']

                async def content_iterator():
                    try:
                        async for chunk in resp.content.iter_chunked(4096):
                            yield chunk
                    finally:
                        await req_ctx.__aexit__(None, None, None)

                return StreamingResponse(
                    content_iterator(),
                    status_code=resp.status,
                    headers=response_headers,
                    media_type=resp.headers.get('content-type')
                )

        except aiohttp.ClientConnectorError:
            logger.error(f"[{self.__class__.__name__}] Connection failed to {url}")
            raise HTTPException(status_code=503, detail="Upstream service unavailable")
        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] Error proxying to {url}: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    async def proxy_websocket(self, client_ws: WebSocket, path: str):
        """Generic WebSocket proxy with SOCKS5 support using websockets library

        NOTE: The WebSocket must be accepted by the caller BEFORE calling this function.
        This is already done in the route handlers (route_dev_proxy.py).
        """
        # WebSocket already accepted in route handler - do NOT accept again

        # Construct WebSocket URL
        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_base}/{path}"

        # CRITICAL: Preserve query parameters (e.g., reconnectionToken for VS Code)
        if client_ws.query_params:
            query_string = str(client_ws.url.query)
            if query_string:
                ws_url += f"?{query_string}"
                logger.info(f"[{self.__class__.__name__}] Forwarding query params: {query_string}")

        logger.info(f"[{self.__class__.__name__}] ====== WS PROXY DEBUG ======")
        logger.info(f"[{self.__class__.__name__}] Client URL: {client_ws.url}")
        logger.info(f"[{self.__class__.__name__}] Target URL: {ws_url}")
        logger.info(f"[{self.__class__.__name__}] Path param: {path}")
        logger.info(f"[{self.__class__.__name__}] Query params: {client_ws.query_params}")
        logger.info(f"[{self.__class__.__name__}] Headers type: {type(client_ws.headers)}")
        logger.info(f"[{self.__class__.__name__}] ==============================")

        # Configure Proxy for websockets library
        proxy_url = None
        if IS_CLOUD_RUN:
            proxy_url = SOCKS5_PROXY
            logger.info(f"[{self.__class__.__name__}] Using websockets proxy: {proxy_url}")

        try:
            logger.info(f"[{self.__class__.__name__}] Connecting to upstream WebSocket...")
            # CRITICAL: Use client_ws.headers directly like Terminal does, not a filtered dict
            async with websockets.connect(
                ws_url,
                extra_headers=client_ws.headers,  # Pass FastAPI WebSocket.headers directly
                proxy=proxy_url,
                open_timeout=10  # Match Terminal exactly
            ) as server_ws:
                logger.info(f"[{self.__class__.__name__}] ✅ Connected! Subprotocol selected: {server_ws.subprotocol}")

                # Bidirectional forwarding
                message_count = {"client_to_server": 0, "server_to_client": 0}

                async def forward_client_to_server():
                    try:
                        while True:
                            msg = await client_ws.receive()
                            if msg.get("type") == "websocket.disconnect":
                                logger.info(f"[{self.__class__.__name__}] Client disconnected")
                                break
                            if "text" in msg:
                                message_count["client_to_server"] += 1
                                if message_count["client_to_server"] <= 3:
                                    logger.info(f"[{self.__class__.__name__}] C->S text msg #{message_count['client_to_server']}: {msg['text'][:100]}")
                                await server_ws.send(msg["text"])
                            if "bytes" in msg:
                                message_count["client_to_server"] += 1
                                if message_count["client_to_server"] <= 3:
                                    logger.info(f"[{self.__class__.__name__}] C->S binary msg #{message_count['client_to_server']}: {len(msg['bytes'])} bytes")
                                await server_ws.send(msg["bytes"])
                    except WebSocketDisconnect:
                        logger.info(f"[{self.__class__.__name__}] Client WebSocket disconnected normally")
                    except Exception as e:
                        logger.error(f"[{self.__class__.__name__}] Client->Server error: {e}")

                async def forward_server_to_client():
                    try:
                        async for msg in server_ws:
                            message_count["server_to_client"] += 1
                            if isinstance(msg, str):
                                if message_count["server_to_client"] <= 3:
                                    logger.info(f"[{self.__class__.__name__}] S->C text msg #{message_count['server_to_client']}: {msg[:100]}")
                                await client_ws.send_text(msg)
                            elif isinstance(msg, bytes):
                                if message_count["server_to_client"] <= 3:
                                    logger.info(f"[{self.__class__.__name__}] S->C binary msg #{message_count['server_to_client']}: {len(msg)} bytes")
                                await client_ws.send_bytes(msg)
                    except websockets.exceptions.ConnectionClosed as e:
                        logger.info(f"[{self.__class__.__name__}] Server WebSocket closed: {e}")
                    except Exception as e:
                        logger.error(f"[{self.__class__.__name__}] Server->Client error: {e}")

                await asyncio.gather(forward_client_to_server(), forward_server_to_client())

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] WS Connection failed: {e}")
            await client_ws.close(code=1011, reason=str(e))

    async def close(self):
        if self.session:
            await self.session.close()
