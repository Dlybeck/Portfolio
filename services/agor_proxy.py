import httpx
import websockets
import os
import asyncio
from starlette.requests import Request
from starlette.responses import StreamingResponse
from starlette.websockets import WebSocket, WebSocketDisconnect
from core.config import settings
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Detect if running in Cloud Run (proxy mode) or locally (direct mode)
IS_CLOUD_RUN = settings.K_SERVICE is not None

# Mac server configuration
MAC_SERVER_IP = settings.MAC_SERVER_IP
SOCKS5_PROXY = settings.SOCKS5_PROXY

class AgorProxy:
    """
    Proxies requests to the Agor server.
    When in Cloud Run, connects via Tailscale SOCKS5 proxy.
    """
    def __init__(self, agor_url: str = None):
        # Auto-detect URL based on environment
        if agor_url:
            self.agor_url = agor_url
        elif IS_CLOUD_RUN:
            # In Cloud Run, connect to Mac via Tailscale
            self.agor_url = f"http://{MAC_SERVER_IP}:3030"
            logger.info(f"Cloud Run mode: proxying to {self.agor_url} via SOCKS5")
        else:
            # Local Mac, connect to localhost
            self.agor_url = "http://127.0.0.1:3030"
            logger.info(f"Local mode: connecting to {self.agor_url}")

        # Create client with SOCKS5 proxy if in Cloud Run
        # Use longer timeouts for Tailscale relay connections
        client_kwargs = {
            "base_url": self.agor_url,
            "timeout": httpx.Timeout(600.0, connect=30.0),  # Increased for slow Tailscale relay
            "follow_redirects": False,
            # Disable keep-alive to prevent SOCKS5 connection stalling
            "limits": httpx.Limits(max_keepalive_connections=0, max_connections=20, keepalive_expiry=5.0)
        }

        if IS_CLOUD_RUN:
            client_kwargs["proxy"] = SOCKS5_PROXY
            logger.info(f"HTTP client using SOCKS5 proxy: {SOCKS5_PROXY}")

        self.client = httpx.AsyncClient(**client_kwargs)
        logger.info(f"Initialized AgorProxy for URL: {self.agor_url}")

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

            content_type = resp.headers.get('content-type', '').lower()

            # Rewrite paths for HTML, JavaScript, and CSS responses
            is_html = 'text/html' in content_type
            is_js = 'javascript' in content_type or path.endswith('.js')
            is_css = 'text/css' in content_type or path.endswith('.css')

            if is_html:
                # Read the full response
                body_bytes = await resp.aread()

                # Decode with proper charset
                charset = 'utf-8'
                if 'charset=' in content_type:
                    charset = content_type.split('charset=')[-1]

                try:
                    body_str = body_bytes.decode(charset)
                except (UnicodeDecodeError, LookupError):
                    body_str = body_bytes.decode('utf-8', errors='replace')

                # Rewrite absolute paths /ui/ to /dev/agor/ui/ for proper routing
                # This fixes paths like /ui/assets/index.js to /dev/agor/ui/assets/index.js
                body_str = body_str.replace('"/ui/', '"/dev/agor/ui/')
                body_str = body_str.replace("'/ui/", "'/dev/agor/ui/")

                # Fix Socket.IO connection path from "/socket.io" to "/dev/agor/socket.io"
                # This is critical for WebSocket authentication to work
                body_str = body_str.replace('"/socket.io/', '"/dev/agor/socket.io/')
                body_str = body_str.replace("'/socket.io/", "'/dev/agor/socket.io/")
                body_str = body_str.replace('"/socket.io"', '"/dev/agor/socket.io"')
                body_str = body_str.replace("'/socket.io'", "'/dev/agor/socket.io'")
                body_str = body_str.replace('||"/socket.io"', '||"/dev/agor/socket.io"')
                body_str = body_str.replace("||'/socket.io'", "||'/dev/agor/socket.io'")

                # Fix React Router basename by injecting script before app loads
                # The Agor app has <Router basename="/ui"> but we're serving at /dev/agor/ui/
                # Inject a base tag to fix routing
                if '<head>' in body_str:
                    base_injection = '<head>\n    <base href="/dev/agor/ui/">'
                    body_str = body_str.replace('<head>', base_injection, 1)

                logger.info("Rewrote /ui/ and /socket.io/ paths to /dev/agor/* and injected base tag in Agor HTML")

                # Encode and update headers
                new_body_bytes = body_str.encode('utf-8')
                response_headers = dict(resp.headers)
                response_headers['content-length'] = str(len(new_body_bytes))
                response_headers.pop('content-encoding', None)

                return StreamingResponse(
                    iter([new_body_bytes]),
                    status_code=resp.status_code,
                    headers=response_headers
                )
            elif is_js:
                # Rewrite JavaScript files to fix React Router basename
                body_bytes = await resp.aread()

                try:
                    body_str = body_bytes.decode('utf-8')

                    # Fix React Router basename from "/ui" to "/dev/agor/ui"
                    # Match patterns like: basename="/ui" or basename:"/ui" or basename='/ui'
                    body_str = body_str.replace('basename:"/ui"', 'basename:"/dev/agor/ui"')
                    body_str = body_str.replace('basename="/ui"', 'basename="/dev/agor/ui"')
                    body_str = body_str.replace("basename:'/ui'", "basename:'/dev/agor/ui'")
                    body_str = body_str.replace("basename='/ui'", "basename='/dev/agor/ui'")

                    # Fix all /ui/ asset paths in strings (images, fonts, etc)
                    # Matches: "/ui/assets/...", '/ui/assets/...', "/ui/fonts/...", etc
                    body_str = body_str.replace('"/ui/assets/', '"/dev/agor/ui/assets/')
                    body_str = body_str.replace("'/ui/assets/", "'/dev/agor/ui/assets/")
                    body_str = body_str.replace('"/ui/fonts/', '"/dev/agor/ui/fonts/')
                    body_str = body_str.replace("'/ui/fonts/", "'/dev/agor/ui/fonts/")
                    body_str = body_str.replace('"/ui/images/', '"/dev/agor/ui/images/')
                    body_str = body_str.replace("'/ui/images/", "'/dev/agor/ui/images/")
                    body_str = body_str.replace('"/ui/static/', '"/dev/agor/ui/static/')
                    body_str = body_str.replace("'/ui/static/", "'/dev/agor/ui/static/")

                    # Fix Socket.IO connection path from "/socket.io" to "/dev/agor/socket.io"
                    # This is critical for WebSocket authentication to work
                    # Match all patterns: quoted strings and default values (||"/socket.io")
                    body_str = body_str.replace('"/socket.io/', '"/dev/agor/socket.io/')
                    body_str = body_str.replace("'/socket.io/", "'/dev/agor/socket.io/")
                    body_str = body_str.replace('"/socket.io"', '"/dev/agor/socket.io"')
                    body_str = body_str.replace("'/socket.io'", "'/dev/agor/socket.io'")
                    body_str = body_str.replace('||"/socket.io"', '||"/dev/agor/socket.io"')
                    body_str = body_str.replace("||'/socket.io'", "||'/dev/agor/socket.io'")

                    # Fix Agor 0.9.0 path detection for proxy environments
                    # Agor checks if(window.location.pathname.startsWith("/ui")) to decide whether to add :3030
                    # We're serving at /dev/agor/ui/ so we need to patch this check
                    body_str = body_str.replace(
                        'window.location.pathname.startsWith("/ui")',
                        '(window.location.pathname.startsWith("/ui")||window.location.pathname.includes("/agor/ui"))'
                    )

                    # Increase Socket.IO connection timeout for slow Tailscale relay
                    # Find and replace the Socket.IO options object to add timeout
                    # Pattern: transports:["polling","websocket"] or similar config objects
                    import re
                    # Add timeout to Socket.IO initialization (increase from default ~20s to 60s)
                    body_str = re.sub(
                        r'(transports:\s*\[[^\]]+\])',
                        r'\1,timeout:60000',
                        body_str
                    )

                    new_body_bytes = body_str.encode('utf-8')
                    response_headers = dict(resp.headers)
                    response_headers['content-length'] = str(len(new_body_bytes))
                    response_headers.pop('content-encoding', None)

                    logger.debug(f"Rewrote React Router basename and Socket.IO paths in JS file: {path}")

                    return StreamingResponse(
                        iter([new_body_bytes]),
                        status_code=resp.status_code,
                        headers=response_headers
                    )
                except Exception as e:
                    logger.warning(f"Failed to rewrite JS file {path}: {e}, streaming as-is")
                    # Fall back to streaming if rewrite fails
                    response_headers = dict(resp.headers)
                    response_headers.pop('content-encoding', None)
                    response_headers.pop('transfer-encoding', None)
                    return StreamingResponse(
                        iter([body_bytes]),
                        status_code=resp.status_code,
                        headers=response_headers
                    )
            elif is_css:
                # Rewrite CSS files to fix asset paths
                body_bytes = await resp.aread()

                try:
                    body_str = body_bytes.decode('utf-8')

                    # Fix CSS url() references from /ui/ to /dev/agor/ui/
                    # Matches: url('/ui/...'), url("/ui/..."), url(/ui/...)
                    import re
                    body_str = re.sub(r'url\(["\']?/ui/', r'url(/dev/agor/ui/', body_str)

                    new_body_bytes = body_str.encode('utf-8')
                    response_headers = dict(resp.headers)
                    response_headers['content-length'] = str(len(new_body_bytes))
                    response_headers.pop('content-encoding', None)

                    logger.debug(f"Rewrote CSS asset paths in: {path}")

                    return StreamingResponse(
                        iter([new_body_bytes]),
                        status_code=resp.status_code,
                        headers=response_headers
                    )
                except Exception as e:
                    logger.warning(f"Failed to rewrite CSS file {path}: {e}, streaming as-is")
                    # Fall back to streaming if rewrite fails
                    response_headers = dict(resp.headers)
                    response_headers.pop('content-encoding', None)
                    response_headers.pop('transfer-encoding', None)
                    return StreamingResponse(
                        iter([body_bytes]),
                        status_code=resp.status_code,
                        headers=response_headers
                    )
            else:
                # Stream non-HTML/JS/CSS responses directly
                response_headers = dict(resp.headers)
                response_headers.pop('content-encoding', None)
                response_headers.pop('transfer-encoding', None)

                return StreamingResponse(
                    resp.aiter_bytes(),
                    status_code=resp.status_code,
                    headers=response_headers
                )
        except httpx.ConnectError as e:
            logger.error(f"Agor proxy connection error: {e}")
            return StreamingResponse(
                iter([f"Agor server not reachable: {e}".encode()]),
                status_code=503,
                media_type="text/plain"
            )
        except Exception as e:
            logger.error(f"Agor proxy error: {e}")
            return StreamingResponse(
                iter([f"Agor proxy error: {e}".encode()]),
                status_code=500,
                media_type="text/plain"
            )

    async def proxy_websocket(self, client_websocket: WebSocket, path: str):
        """
        Proxy WebSocket connection to Agor with retry logic and SOCKS5 support
        """
        await client_websocket.accept()

        # Build target WebSocket URL
        if IS_CLOUD_RUN:
            ws_url = f"ws://{MAC_SERVER_IP}:3030{path}"
            logger.info(f"🔌 Cloud Run mode: WebSocket proxy starting")
            logger.info(f"   Target: {ws_url}")
            logger.info(f"   SOCKS5: {SOCKS5_PROXY}")
        else:
            ws_url = f"ws://127.0.0.1:3030{path}"
            logger.info(f"🔌 Local mode: WebSocket proxy to {ws_url}")

        # Retry configuration
        max_retries = 3
        retry_delay = 0.5
        last_exception = None

        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    wait_time = min(retry_delay * (2 ** (attempt - 1)), 2.5)
                    logger.info(f"Retry attempt {attempt + 1}/{max_retries} after {wait_time}s delay...")
                    await asyncio.sleep(wait_time)

                await self._proxy_websocket_connection(client_websocket, ws_url)
                return  # Success!

            except (OSError, ConnectionError, TimeoutError) as e:
                last_exception = e
                logger.error(f"❌ Connection attempt {attempt + 1}/{max_retries} failed: {type(e).__name__}: {e}")
                if attempt < max_retries - 1:
                    logger.info("🔄 Will retry connection...")
                else:
                    logger.error(f"💀 All {max_retries} connection attempts failed")

            except Exception as e:
                logger.error(f"❌ Non-retryable error in proxy_websocket: {type(e).__name__}: {e}")
                logger.exception(e)  # Print full stack trace
                await client_websocket.close(code=1011, reason=f"Proxy error: {type(e).__name__}")
                return

        # All retries exhausted
        error_msg = f"Connection failed after {max_retries} attempts"
        if last_exception:
            error_msg += f": {last_exception}"
        logger.error(error_msg)
        await client_websocket.close(code=1011, reason="Agor proxy unavailable")

    async def _proxy_websocket_connection(self, client_websocket: WebSocket, ws_url: str):
        """
        Establish and maintain WebSocket proxy connection (internal method)
        """
        try:
            if IS_CLOUD_RUN:
                # Cloud Run: Use aiohttp with SOCKS5 proxy (same as code-server proxy)
                import aiohttp
                from aiohttp_socks import ProxyConnector

                connector = ProxyConnector.from_url(SOCKS5_PROXY)
                logger.info(f"🔌 SOCKS5 connector created, attempting connection...")

                async with aiohttp.ClientSession(connector=connector) as session:
                    logger.info(f"🔌 aiohttp session created, connecting to {ws_url}...")
                    async with session.ws_connect(
                        ws_url,
                        timeout=aiohttp.ClientTimeout(total=43200, connect=60),  # 12 hours total, 60s connect for slow Tailscale relay
                        heartbeat=15.0,  # Send ping every 15s to keep SOCKS5/LB connection alive
                        autoping=True
                    ) as server_ws:
                        logger.info(f"✅ WebSocket connection ESTABLISHED to Agor: {ws_url}")
                        logger.info(f"🔌 Starting bidirectional message forwarding...")

                        async def forward_to_server():
                            """Forward messages from browser to Agor"""
                            try:
                                while True:
                                    message = await client_websocket.receive()

                                    if message.get('type') == 'websocket.disconnect':
                                        logger.info("Browser disconnected from Agor WebSocket")
                                        break
                                    elif 'text' in message:
                                        logger.debug(f"Browser → Agor: {message['text'][:100]}")
                                        await server_ws.send_str(message['text'])
                                    elif 'bytes' in message:
                                        logger.debug(f"Browser → Agor: {len(message['bytes'])} bytes")
                                        await server_ws.send_bytes(message['bytes'])
                            except WebSocketDisconnect:
                                logger.info("Browser WebSocket disconnect")
                                pass
                            except Exception as e:
                                logger.error(f"Forward error: {e}")

                        async def forward_to_client():
                            """Forward messages from Agor to browser"""
                            try:
                                async for msg in server_ws:
                                    if msg.type == aiohttp.WSMsgType.TEXT:
                                        logger.debug(f"Agor → Browser: {msg.data[:100]}")
                                        await client_websocket.send_text(msg.data)
                                    elif msg.type == aiohttp.WSMsgType.BINARY:
                                        logger.debug(f"Agor → Browser: {len(msg.data)} bytes")
                                        await client_websocket.send_bytes(msg.data)
                                    elif msg.type == aiohttp.WSMsgType.ERROR:
                                        logger.error("Agor WebSocket error message received")
                                        break
                            except WebSocketDisconnect:
                                logger.info("Browser disconnected during forward_to_client")
                                pass
                            except Exception as e:
                                logger.error(f"Backward error: {e}")

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
                    logger.info(f"WebSocket connection established to Agor: {ws_url}")

                    async def forward_to_server():
                        """Forward messages from browser to Agor"""
                        try:
                            while True:
                                message = await client_websocket.receive()

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
                        """Forward messages from Agor to browser"""
                        try:
                            async for message in server_ws:
                                if isinstance(message, str):
                                    await client_websocket.send_text(message)
                                elif isinstance(message, bytes):
                                    await client_websocket.send_bytes(message)
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
            logger.error(f"Connection error in _proxy_websocket_connection: {type(e).__name__}: {e}")
            raise

_agor_proxy_instance: AgorProxy = None

def get_proxy() -> AgorProxy:
    """Get global Agor proxy instance"""
    global _agor_proxy_instance
    if _agor_proxy_instance is None:
        # Auto-detects environment and configures SOCKS5 if needed
        _agor_proxy_instance = AgorProxy()
    return _agor_proxy_instance
