"""
Code-server HTTP and WebSocket Proxy
Handles reverse proxying to local code-server instance
"""

import httpx
import websockets
import asyncio
from fastapi import Request, Response, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import StreamingResponse
from typing import Dict, Any


class CodeServerProxy:
    """Reverse proxy for code-server"""

    def __init__(self, code_server_url: str = "http://127.0.0.1:8888"):
        self.code_server_url = code_server_url
        self.client = None

    async def get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self.client is None:
            # Create client with default decompression (httpx auto-decodes gzip/brotli/deflate)
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(300.0, connect=10.0),
                follow_redirects=False,
                limits=httpx.Limits(max_keepalive_connections=20)
            )
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
        Proxy WebSocket connection to code-server

        Args:
            client_ws: FastAPI WebSocket from browser
            path: WebSocket path (e.g., "ws/path")
        """
        # Build target WebSocket URL
        ws_url = f"ws://127.0.0.1:8888/{path}"

        try:
            # Connect to code-server WebSocket
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
                            # Receive from browser
                            message = await client_ws.receive()

                            # Forward to server
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
                            # Forward to browser
                            if isinstance(message, str):
                                await client_ws.send_text(message)
                            elif isinstance(message, bytes):
                                await client_ws.send_bytes(message)
                    except WebSocketDisconnect:
                        pass
                    except Exception as e:
                        print(f"[WS Proxy] Backward error: {e}")

                # Run both directions concurrently
                await asyncio.gather(
                    forward_to_server(),
                    forward_to_client(),
                    return_exceptions=True
                )

        except Exception as e:
            print(f"[WS Proxy] Connection error: {e}")
            await client_ws.close(code=1011, reason="Proxy error")

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
