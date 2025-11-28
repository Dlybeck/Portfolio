"""
Base Proxy Service for Tailscale/SOCKS5 Connections
Centralizes logic for:
- aiohttp session management
- SOCKS5 proxy negotiation (for Cloud Run)
- Header filtering/normalization
- Streaming responses
- WebSocket tunneling
"""

import aiohttp
import asyncio
import os
import logging
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
        """Generic WebSocket proxy with SOCKS5 support"""
        await client_ws.accept()
        
        # Construct WebSocket URL
        scheme = "ws" if not self.base_url.startswith("https") else "wss"
        # Extract host/port from base_url logic
        # But wait, the base_url might be http://IP:PORT
        # We need to convert http:// -> ws://
        ws_base = self.base_url.replace("http://", "ws://").replace("https://", "wss://")
        ws_url = f"{ws_base}/{path}"

        logger.info(f"[{self.__class__.__name__}] WS Proxy to {ws_url}")

        try:
            connector = None
            if IS_CLOUD_RUN:
                connector = ProxyConnector.from_url(SOCKS5_PROXY)
            
            # Forward only essential headers for authentication and context
            # Filtering out WS protocol headers that aiohttp will regenerate or conflict with
            ws_headers = {}
            allowed_headers = {'authorization', 'cookie', 'origin', 'user-agent', 'x-forwarded-for', 'x-forwarded-proto'}
            for k, v in client_ws.headers.items():
                if k.lower() in allowed_headers:
                    ws_headers[k] = v

            async with aiohttp.ClientSession(connector=connector) as ws_session:
                try:
                    async with ws_session.ws_connect(
                        ws_url,
                        timeout=aiohttp.ClientTimeout(total=43200, connect=60), # Increased connect timeout
                        heartbeat=15.0,
                        autoping=True,
                        headers=ws_headers # Forward filtered headers
                    ) as server_ws:
                        
                        # Bidirectional forwarding
                        async def forward_client_to_server():
                            try:
                                while True:
                                    msg = await client_ws.receive()
                                    if msg.get("type") == "websocket.disconnect":
                                        break
                                    if "text" in msg:
                                        await server_ws.send_str(msg["text"])
                                    if "bytes" in msg:
                                        await server_ws.send_bytes(msg["bytes"])
                            except Exception as e:
                                logger.error(f"[{self.__class__.__name__}] Client->Server error: {e}")

                        async def forward_server_to_client():
                            try:
                                async for msg in server_ws:
                                    if msg.type == aiohttp.WSMsgType.TEXT:
                                        await client_ws.send_text(msg.data)
                                    elif msg.type == aiohttp.WSMsgType.BINARY:
                                        await client_ws.send_bytes(msg.data)
                                    elif msg.type == aiohttp.WSMsgType.ERROR:
                                        break
                            except Exception as e:
                                logger.error(f"[{self.__class__.__name__}] Server->Client error: {e}")

                        await asyncio.gather(forward_client_to_server(), forward_server_to_client())
                except Exception as e:
                    logger.error(f"[{self.__class__.__name__}] WS Connection failed: {e}")
                    await client_ws.close(code=1011, reason=str(e))

        except Exception as e:
            logger.error(f"[{self.__class__.__name__}] WS Setup Error: {e}")
            await client_ws.close(code=1011)

    async def close(self):
        if self.session:
            await self.session.close()
