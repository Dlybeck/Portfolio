"""
Cloud Run Proxy - Tailscale Gateway
Forwards all /dev/* requests to Mac via Tailscale network
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse
import httpx
import os
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = FastAPI()

# Target Ubuntu server on Tailscale network
MAC_SERVER_URL = "http://100.79.140.119:8080"

# HTTP client for proxying requests
# Use longer timeout for initial code-server/Agor loads via Tailscale
client = httpx.AsyncClient(timeout=300.0)


@app.get("/health")
async def health_check():
    """Health check endpoint for Cloud Run"""
    import subprocess

    # Check Tailscale connection
    try:
        result = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            import json
            status = json.loads(result.stdout)
            return {
                "status": "healthy",
                "service": "tailscale-proxy",
                "tailscale": {
                    "connected": True,
                    "backend_state": status.get("BackendState", "unknown")
                }
            }
    except Exception as e:
        pass

    return {
        "status": "healthy",
        "service": "tailscale-proxy",
        "tailscale": {"connected": False}
    }


@app.get("/oauth-status")
async def oauth_status():
    """Check OAuth client health - shows renewal instructions if needed"""
    import os
    import requests

    oauth_id = os.getenv('TAILSCALE_OAUTH_CLIENT_ID')
    oauth_secret = os.getenv('TAILSCALE_OAUTH_CLIENT_SECRET')

    if not oauth_id or not oauth_secret:
        return {
            "status": "error",
            "message": "OAuth credentials not configured",
            "instructions": [
                "1. Go to https://login.tailscale.com/admin/settings/oauth",
                "2. Create OAuth client with 'Devices: Write' scope",
                "3. Update Cloud Run env vars with TAILSCALE_OAUTH_CLIENT_ID and TAILSCALE_OAUTH_CLIENT_SECRET",
                "4. Redeploy service"
            ]
        }

    # Test OAuth credentials
    try:
        response = requests.post(
            'https://api.tailscale.com/api/v2/oauth/token',
            auth=(oauth_id, oauth_secret),
            data={'grant_type': 'client_credentials'},
            timeout=10
        )

        if response.status_code == 200:
            return {
                "status": "healthy",
                "message": "OAuth client is valid",
                "last_checked": str(subprocess.check_output(["date"], text=True).strip())
            }
        else:
            return {
                "status": "error",
                "message": f"OAuth client invalid: {response.status_code}",
                "instructions": [
                    "⚠️ YOUR OAUTH CLIENT NEEDS RENEWAL",
                    "",
                    "1. Go to: https://login.tailscale.com/admin/settings/oauth",
                    "2. Generate new OAuth client (or find existing 'cloud-proxy')",
                    "3. Scopes: 'Devices: Write'",
                    "4. Run:",
                    "   gcloud run services update dev-proxy \\",
                    "     --region=us-central1 \\",
                    "     --update-env-vars TAILSCALE_OAUTH_CLIENT_ID=YOUR_ID,TAILSCALE_OAUTH_CLIENT_SECRET=YOUR_SECRET"
                ]
            }
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error checking OAuth: {str(e)}",
            "instructions": ["Check network connectivity", "Verify OAuth credentials"]
        }


@app.api_route("/dev/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def proxy_http(path: str, request: Request):
    """
    Proxy all HTTP requests to Mac server via Tailscale
    """
    target_url = f"{MAC_SERVER_URL}/dev/{path}"

    # Get query parameters
    query_params = dict(request.query_params)

    # Get headers (exclude hop-by-hop headers)
    headers = {
        key: value
        for key, value in request.headers.items()
        if key.lower() not in ["host", "connection", "transfer-encoding"]
    }

    # Get body for POST/PUT/PATCH
    body = None
    if request.method in ["POST", "PUT", "PATCH"]:
        body = await request.body()

    try:
        # Forward request to Mac
        response = await client.request(
            method=request.method,
            url=target_url,
            params=query_params,
            headers=headers,
            content=body,
        )

        # Return response from Mac
        return Response(
            content=response.content,
            status_code=response.status_code,
            headers=dict(response.headers),
        )

    except httpx.RequestError as e:
        return Response(
            content=f"Error connecting to Mac: {str(e)}",
            status_code=502,
        )


@app.websocket("/{path:path}")
async def proxy_websocket_all(websocket: WebSocket, path: str):
    """
    Proxy all WebSocket connections (OpenCode PTY, terminal, chat, etc)
    """
    import websockets
    
    await websocket.accept()
    logger.info(f"WebSocket proxy: /{path}")

    # Build target URL
    query_params = dict(websocket.query_params)
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    
    ws_url = f"ws://100.79.140.119:8080/{path}"
    if query_string:
        ws_url += f"?{query_string}"
    
    logger.info(f"Connecting to: {ws_url}")

    try:
        async with websockets.connect(ws_url) as backend_ws:
            logger.info(f"Connected to backend WebSocket")
            
            async def forward_to_backend():
                try:
                    while True:
                        msg = await websocket.receive()
                        if msg.get("type") == "websocket.disconnect":
                            break
                        if "text" in msg:
                            await backend_ws.send(msg["text"])
                        elif "bytes" in msg:
                            await backend_ws.send(msg["bytes"])
                except Exception as e:
                    logger.error(f"Forward to backend error: {e}")

            async def forward_to_client():
                try:
                    async for msg in backend_ws:
                        if isinstance(msg, str):
                            await websocket.send_text(msg)
                        else:
                            await websocket.send_bytes(msg)
                except Exception as e:
                    logger.error(f"Forward to client error: {e}")

            await asyncio.gather(forward_to_backend(), forward_to_client())

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        try:
            await websocket.close(code=1011, reason=str(e))
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
