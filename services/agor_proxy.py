import httpx
import os
import asyncio
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.websockets import WebSocket, WebSocketDisconnect

class AgorProxy:
    """
    Proxies requests to the Agor server.
    """
    def __init__(self, agor_url: str):
        self.agor_url = agor_url
        self.client = httpx.AsyncClient(base_url=self.agor_url)
        print(f"Initialized AgorProxy for URL: {self.agor_url}")

    async def proxy_request(self, request: Request, path: str):
        # Build relative URL with query params (client already has base_url set)
        url = f"/{path}"
        if request.url.query:
            url += f"?{request.url.query}"

        # Prepare headers, removing host, referer, and existing content-length
        headers = {key: value for key, value in request.headers.items() if key.lower() not in ["host", "referer", "content-length"]}
        
        # Add X-Forwarded-For if not present
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            headers["x-forwarded-for"] = f"{x_forwarded_for}, {request.client.host}"
        else:
            headers["x-forwarded-for"] = request.client.host
            
        try:
            # Forward the request
            body = await request.body()
            resp = await self.client.request(
                method=request.method,
                url=url,
                headers=headers,
                content=body,
                follow_redirects=False
            )

            return StreamingResponse(
                resp.aiter_bytes(),
                status_code=resp.status_code,
                headers=resp.headers
            )
        except httpx.ConnectError as e:
            print(f"Agor proxy connection error: {e}")
            return StreamingResponse(
                iter([f"Agor server not reachable: {e}".encode()]),
                status_code=503,
                media_type="text/plain"
            )
        except Exception as e:
            print(f"Agor proxy error: {e}")
            return StreamingResponse(
                iter([f"Agor proxy error: {e}".encode()]),
                status_code=500,
                media_type="text/plain"
            )

    async def proxy_websocket(self, client_websocket: WebSocket, path: str):
        await client_websocket.accept()
        agor_ws_url = f"ws://{self.agor_url.replace('http://', '').replace('https://', '')}{path}"
        
        try:
            async with httpx.AsyncClient() as client:
                async with client.websocket_connect(agor_ws_url) as agor_websocket:
                    print(f"WebSocket connection established to Agor: {agor_ws_url}")

                    async def forward_client_to_agor():
                        try:
                            while True:
                                message = await client_websocket.receive_text()
                                await agor_websocket.send_text(message)
                        except WebSocketDisconnect:
                            print("Client disconnected from Agor WebSocket")
                        except Exception as e:
                            print(f"Error forwarding client to Agor: {e}")

                    async def forward_agor_to_client():
                        try:
                            while True:
                                message = await agor_websocket.receive_text()
                                await client_websocket.send_text(message)
                        except Exception as e:
                            print(f"Error forwarding Agor to client: {e}")
                            
                    await asyncio.gather(
                        forward_client_to_agor(),
                        forward_agor_to_client()
                    )
        except httpx.ConnectError as e:
            print(f"Could not connect to Agor WebSocket: {e}")
            await client_websocket.close(code=1011) # Internal Error
        except Exception as e:
            print(f"Agor WebSocket proxy error: {e}")
            await client_websocket.close(code=1011) # Internal Error

_agor_proxy_instance: AgorProxy = None

def get_proxy() -> AgorProxy:
    global _agor_proxy_instance
    if _agor_proxy_instance is None:
        # Use AGOR_URL environment variable if available, otherwise default to localhost:5678
        agor_url = os.environ.get("AGOR_URL", "http://localhost:3030")
        _agor_proxy_instance = AgorProxy(agor_url)
    return _agor_proxy_instance
