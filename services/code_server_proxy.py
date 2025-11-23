"""
Code-server HTTP and WebSocket Proxy
Handles reverse proxying to local code-server instance
When in Cloud Run, proxies through Tailscale SOCKS5
"""

import httpx
import websockets
import asyncio
import os
from fastapi import Request, Response, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Dict, Any
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Detect if running in Cloud Run (proxy mode) or locally (direct mode)
IS_CLOUD_RUN = settings.K_SERVICE is not None

# Mac server configuration
MAC_SERVER_IP = settings.MAC_SERVER_IP
MAC_SERVER_PORT = settings.MAC_SERVER_PORT
SOCKS5_PROXY = settings.SOCKS5_PROXY


class CodeServerProxy:
    """Reverse proxy for code-server"""

    def __init__(self, code_server_url: str = None):
        # Auto-detect URL based on environment
        if code_server_url:
            self.code_server_url = code_server_url
        elif IS_CLOUD_RUN:
            # In Cloud Run, connect to Mac via Tailscale
            self.code_server_url = f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}"
            logger.info(f"Cloud Run mode: proxying to {self.code_server_url} via SOCKS5")
        else:
            # Local Mac, connect to localhost
            self.code_server_url = "http://127.0.0.1:8888"
            logger.info(f"Local mode: connecting to {self.code_server_url}")

        self.client = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with SOCKS5 proxy if in Cloud Run"""
        if self.client is None:
            # Create client with default decompression (httpx auto-decodes gzip/brotli/deflate)
            client_kwargs = {
                "timeout": httpx.Timeout(300.0, connect=10.0),
                "follow_redirects": False,
                "limits": httpx.Limits(max_keepalive_connections=20)
            }

            # Add SOCKS5 proxy if running in Cloud Run
            if IS_CLOUD_RUN:
                client_kwargs["proxy"] = SOCKS5_PROXY
                logger.info(f"HTTP client using SOCKS5 proxy: {SOCKS5_PROXY}")

            self.client = httpx.AsyncClient(**client_kwargs)
        return self.client

    def _prepare_headers(self, request: Request) -> Dict[str, str]:
        """Prepare headers for proxying"""
        headers = dict(request.headers)

        # Remove headers that shouldn't be forwarded
        headers.pop('host', None)
        headers.pop('connection', None)

        # Remove accept-encoding to prevent double compression issues
        # httpx will handle decompression automatically
        headers.pop('accept-encoding', None)

        # Add code-server specific headers
        headers['X-Forwarded-For'] = request.client.host
        headers['X-Forwarded-Proto'] = request.url.scheme
        headers['X-Forwarded-Prefix'] = '/dev/vscode'

        return headers

    async def proxy_request(
        self,
        request: Request,
        path: str
    ) -> Response:
        """
        Proxy HTTP request to code-server

        Args:
            request: FastAPI request object
            path: Path to proxy (e.g., "index.html")

        Returns:
            Response from code-server
        """
        client = await self.get_client()

        # Build target URL
        url = f"{self.code_server_url}/{path}"
        if request.url.query:
            url += f"?{request.url.query}"

        # Prepare headers
        headers = self._prepare_headers(request)

        try:
            # Proxy the request
            if request.method == "GET":
                response = await client.get(url, headers=headers)
            elif request.method == "POST":
                body = await request.body()
                response = await client.post(url, headers=headers, content=body)
            elif request.method == "PUT":
                body = await request.body()
                response = await client.put(url, headers=headers, content=body)
            elif request.method == "DELETE":
                response = await client.delete(url, headers=headers)
            elif request.method == "PATCH":
                body = await request.body()
                response = await client.patch(url, headers=headers, content=body)
            else:
                raise HTTPException(status_code=405, detail="Method not allowed")

            # Prepare response headers (remove compression headers since httpx already decoded)
            response_headers = dict(response.headers)
            response_headers.pop('content-encoding', None)  # Remove gzip/brotli encoding
            response_headers.pop('content-length', None)    # Length changed after decoding

            # Return response
            return Response(
                content=response.content,
                status_code=response.status_code,
                headers=response_headers,
                media_type=response.headers.get('content-type')
            )

        except httpx.ConnectError:
            raise HTTPException(
                status_code=503,
                detail="code-server is not running. Please start it first."
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    async def proxy_websocket(
        self,
        client_ws: WebSocket,
        path: str
    ):
        """
        Proxy WebSocket connection to code-server with retry logic

        Args:
            client_ws: FastAPI WebSocket from browser
            path: WebSocket path (e.g., "ws/path")
        """
        # Build target WebSocket URL based on environment
        if IS_CLOUD_RUN:
            # Cloud Run: Connect to Mac via SOCKS5
            ws_url = f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/{path}"
            logger.info(f"Cloud Run mode: connecting to {ws_url} via SOCKS5")
        else:
            # Local: Connect to localhost
            ws_url = f"ws://127.0.0.1:8888/{path}"
            logger.info(f"Local mode: connecting to {ws_url}")

        # Retry configuration (matching HTTP retry logic)
        max_retries = 3
        retry_delay = 0.5
        last_exception = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Wait before retry with exponential backoff
                    wait_time = min(retry_delay * (2 ** (attempt - 1)), 2.5)
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    await asyncio.sleep(wait_time)

                await self._proxy_websocket_connection(client_ws, ws_url, path)
                return  # Success!

            except (OSError, ConnectionError, TimeoutError) as e:
                last_exception = e
                error_name = type(e).__name__
                logger.error(f"Connection attempt {attempt + 1}/{max_retries} failed: {error_name}: {e}")

                if attempt < max_retries - 1:
                    logger.info("Will retry connection...")
                else:
                    logger.error(f"All {max_retries} connection attempts failed")

            except Exception as e:
                # Non-retryable error
                logger.error(f"Non-retryable error: {type(e).__name__}: {e}")
                await client_ws.close(code=1011, reason=f"Proxy error: {type(e).__name__}")
                return

        # All retries exhausted
        error_msg = f"Connection failed after {max_retries} attempts"
        if last_exception:
            error_msg += f": {last_exception}"
        logger.error(f"{error_msg}")
        await client_ws.close(code=1011, reason="SOCKS5 proxy unavailable")

    async def _proxy_websocket_connection(
        self,
        client_ws: WebSocket,
        ws_url: str,
        path: str
    ):
        """
        Establish and maintain WebSocket proxy connection (internal method)

        Args:
            client_ws: FastAPI WebSocket from browser
            ws_url: Target WebSocket URL
            path: WebSocket path
        """
        try:
            # Unified proxy logic using websockets library
            connect_kwargs = {
                "ping_interval": 30,
                "ping_timeout": 10,
                "close_timeout": 10
            }
            if IS_CLOUD_RUN:
                connect_kwargs["proxy"] = SOCKS5_PROXY

            async with websockets.connect(ws_url, **connect_kwargs) as server_ws:
                # Bidirectional proxy
                async def forward_to_server():
                    """Forward messages from browser to code-server"""
                    try:
                        while True:
                            message = await client_ws.receive()

                            if message.get('type') == 'websocket.disconnect':
                                break
                            elif 'text' in message:
                                await server_ws.send(message['text'])
                            elif 'bytes' in message:
                                await server_ws.send(message['bytes'])
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        logger.error(f"Forward error: {e}")

                async def forward_to_client():
                    """Forward messages from code-server to browser"""
                    try:
                        async for message in server_ws:
                            if isinstance(message, str):
                                await client_ws.send_text(message)
                            elif isinstance(message, bytes):
                                await client_ws.send_bytes(message)
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        logger.error(f"Backward error: {e}")

                await asyncio.gather(
                    forward_to_server(),
                    forward_to_client(),
                    return_exceptions=True
                )

        except Exception as e:
            # Re-raise to be caught by retry logic in proxy_websocket()
            logger.error(f"Connection error in _proxy_websocket_connection: {type(e).__name__}: {e}")
            raise

    async def close(self):
        """Close HTTP client"""
        if self.client:
            await self.client.aclose()


# Global instance
_proxy_instance = None


def get_proxy() -> CodeServerProxy:
    """Get global proxy instance"""
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = CodeServerProxy()
    return _proxy_instance
