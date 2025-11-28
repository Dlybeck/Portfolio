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


# Detect if running in Cloud Run (proxy mode) or locally (direct mode)
IS_CLOUD_RUN = os.environ.get("K_SERVICE") is not None

# Mac server configuration
MAC_SERVER_IP = "100.84.184.84"
MAC_SERVER_PORT = 8888
SOCKS5_PROXY = "socks5://localhost:1055"


class CodeServerProxy:
    """Reverse proxy for code-server"""

    def __init__(self, code_server_url: str = None):
        # Auto-detect URL based on environment
        if code_server_url:
            self.code_server_url = code_server_url
        elif IS_CLOUD_RUN:
            # In Cloud Run, connect to Mac via Tailscale
            self.code_server_url = f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}"
            print(f"[CodeServerProxy] Cloud Run mode: proxying to {self.code_server_url} via SOCKS5")
        else:
            # Local Mac, connect to localhost
            self.code_server_url = "http://127.0.0.1:8888"
            print(f"[CodeServerProxy] Local mode: connecting to {self.code_server_url}")

        self.client = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client with SOCKS5 proxy if in Cloud Run"""
        if self.client is None:
            # Create client with default decompression (httpx auto-decodes gzip/brotli/deflate)
            client_kwargs = {
                "timeout": httpx.Timeout(300.0, connect=10.0),
                "follow_redirects": False,
                # Disable keep-alive to prevent SOCKS5 connection stalling
                "limits": httpx.Limits(max_keepalive_connections=0, max_connections=20)
            }

            # Add SOCKS5 proxy if running in Cloud Run
            if IS_CLOUD_RUN:
                client_kwargs["proxy"] = SOCKS5_PROXY
                print(f"[CodeServerProxy] HTTP client using SOCKS5 proxy: {SOCKS5_PROXY}")

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
            print(f"[CodeServerProxy WS] Cloud Run mode: connecting to {ws_url} via SOCKS5")
        else:
            # Local: Connect to localhost
            ws_url = f"ws://127.0.0.1:8888/{path}"
            print(f"[CodeServerProxy WS] Local mode: connecting to {ws_url}")

        # Retry configuration (matching HTTP retry logic)
        max_retries = 3
        retry_delay = 0.5
        last_exception = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    # Wait before retry with exponential backoff
                    wait_time = min(retry_delay * (2 ** (attempt - 1)), 2.5)
                    print(f"[WS Proxy] Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    await asyncio.sleep(wait_time)

                await self._proxy_websocket_connection(client_ws, ws_url, path)
                return  # Success!

            except (OSError, ConnectionError, TimeoutError) as e:
                last_exception = e
                error_name = type(e).__name__
                print(f"[WS Proxy] ❌ Connection attempt {attempt + 1}/{max_retries} failed: {error_name}: {e}")

                if attempt < max_retries - 1:
                    print(f"[WS Proxy] 🔄 Will retry connection...")
                else:
                    print(f"[WS Proxy] 💀 All {max_retries} connection attempts failed")

            except Exception as e:
                # Non-retryable error
                print(f"[WS Proxy] ❌ Non-retryable error: {type(e).__name__}: {e}")
                await client_ws.close(code=1011, reason=f"Proxy error: {type(e).__name__}")
                return

        # All retries exhausted
        error_msg = f"Connection failed after {max_retries} attempts"
        if last_exception:
            error_msg += f": {last_exception}"
        print(f"[WS Proxy] {error_msg}")
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
            if IS_CLOUD_RUN:
                # Cloud Run: Use aiohttp with SOCKS5 proxy
                import aiohttp
                from aiohttp_socks import ProxyConnector

                connector = ProxyConnector.from_url(SOCKS5_PROXY)

                async with aiohttp.ClientSession(connector=connector) as session:
                    async with session.ws_connect(
                        ws_url,
                        timeout=aiohttp.ClientTimeout(total=43200),  # 12 hours
                        heartbeat=15.0,  # Send ping every 15s to keep SOCKS5/LB connection alive
                        autoping=True
                    ) as server_ws:
                        # Bidirectional proxy
                        async def forward_to_server():
                            """Forward messages from browser to code-server"""
                            try:
                                while True:
                                    message = await client_ws.receive()

                                    if message.get('type') == 'websocket.disconnect':
                                        break
                                    elif 'text' in message:
                                        await server_ws.send_str(message['text'])
                                    elif 'bytes' in message:
                                        await server_ws.send_bytes(message['bytes'])
                            except WebSocketDisconnect:
                                pass
                            except Exception as e:
                                print(f"[WS Proxy] Forward error: {e}")

                        async def forward_to_client():
                            """Forward messages from code-server to browser"""
                            try:
                                async for msg in server_ws:
                                    if msg.type == aiohttp.WSMsgType.TEXT:
                                        await client_ws.send_text(msg.data)
                                    elif msg.type == aiohttp.WSMsgType.BINARY:
                                        await client_ws.send_bytes(msg.data)
                                    elif msg.type == aiohttp.WSMsgType.ERROR:
                                        break
                            except WebSocketDisconnect:
                                pass
                            except Exception as e:
                                print(f"[WS Proxy] Backward error: {e}")

                        await asyncio.gather(
                            forward_to_server(),
                            forward_to_client(),
                            return_exceptions=True
                        )
            else:
                # Local: Use websockets library (direct connection)
                async with websockets.connect(
                    ws_url,
                    ping_interval=30,
                    ping_timeout=10,
                    close_timeout=10
                ) as server_ws:
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
                            print(f"[WS Proxy] Forward error: {e}")

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
                            print(f"[WS Proxy] Backward error: {e}")

                    await asyncio.gather(
                        forward_to_server(),
                        forward_to_client(),
                        return_exceptions=True
                    )

        except Exception as e:
            # Re-raise to be caught by retry logic in proxy_websocket()
            print(f"[WS Proxy] Connection error in _proxy_websocket_connection: {type(e).__name__}: {e}")
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
