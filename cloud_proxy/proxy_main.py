"""
Cloud Run Proxy - Tailscale Gateway
Forwards all /dev/* requests to Mac via Tailscale network
"""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response, StreamingResponse
import httpx
import os
import asyncio

app = FastAPI()

# Target Mac server on Tailscale network
MAC_SERVER_URL = "http://100.84.184.84:8080"

# HTTP client for proxying requests
client = httpx.AsyncClient(timeout=60.0)


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


@app.websocket("/dev/ws/terminal")
async def proxy_websocket(websocket: WebSocket):
    """
    Proxy WebSocket connections for terminal
    """
    await websocket.accept()

    # Get query parameters (working directory)
    query_params = dict(websocket.query_params)
    query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
    target_url = f"ws://100.84.184.84:8080/dev/ws/terminal"
    if query_string:
        target_url += f"?{query_string}"

    try:
        # Connect to Mac WebSocket
        async with httpx.AsyncClient() as ws_client:
            async with ws_client.stream(
                "GET",
                target_url,
                headers={
                    "Upgrade": "websocket",
                    "Connection": "Upgrade",
                },
            ) as mac_ws:
                # Bi-directional proxying
                async def forward_to_mac():
                    """Forward messages from client to Mac"""
                    try:
                        while True:
                            data = await websocket.receive_text()
                            await mac_ws.send(data)
                    except WebSocketDisconnect:
                        pass

                async def forward_to_client():
                    """Forward messages from Mac to client"""
                    try:
                        async for chunk in mac_ws.aiter_text():
                            await websocket.send_text(chunk)
                    except Exception:
                        pass

                # Run both directions concurrently
                await asyncio.gather(
                    forward_to_mac(),
                    forward_to_client(),
                )

    except Exception as e:
        print(f"WebSocket proxy error: {e}")
        try:
            await websocket.close()
        except:
            pass


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    uvicorn.run(app, host="0.0.0.0", port=port)
