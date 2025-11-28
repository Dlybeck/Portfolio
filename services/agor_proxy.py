
"""
Agor HTTP and WebSocket Proxy
Inherits from BaseProxy to reuse connection logic but adds custom rewriting
"""

from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP, SOCKS5_PROXY
from fastapi import Request, Response, HTTPException
from fastapi.responses import StreamingResponse
from starlette.websockets import WebSocket
import logging
import re

logger = logging.getLogger(__name__)

class AgorProxy(BaseProxy):
    """
    Proxies requests to the Agor server.
    """
    def __init__(self, agor_url: str = None):
        if not agor_url:
            if IS_CLOUD_RUN:
                agor_url = f"http://{MAC_SERVER_IP}:3030"
            else:
                agor_url = "http://127.0.0.1:3030"
        
        super().__init__(agor_url)

    async def _rewrite_response_body(self, body_bytes: bytes, headers: dict, path: str):
        """
        Callback to rewrite Agor's HTML/JS/CSS to fix paths and routing.
        """
        content_type = headers.get('content-type', '').lower()
        charset = 'utf-8'
        if 'charset=' in content_type:
            charset = content_type.split('charset=')[-1]

        try:
            body_str = body_bytes.decode(charset)
        except (UnicodeDecodeError, LookupError):
            body_str = body_bytes.decode('utf-8', errors='replace')

        # === REWRITE LOGIC ===
        
        # 1. Rewrite absolute paths /ui/ to /dev/agor/ui/
        body_str = body_str.replace('"/ui/', '"/dev/agor/ui/')
        body_str = body_str.replace("'/ui/", "'/dev/agor/ui/")
        
        # 2. Fix Socket.IO connection path
        # Agor defaults to /socket.io, we need /dev/agor/socket.io
        # Replace string literals
        body_str = body_str.replace('"/socket.io/"', '"/dev/agor/socket.io/"') # trailing slash?
        body_str = body_str.replace('"/socket.io"', '"/dev/agor/socket.io"')
        body_str = body_str.replace("'/socket.io'", "'/dev/agor/socket.io'")
        # Replace potential JS defaults
        body_str = body_str.replace('||"/socket.io"', '||"/dev/agor/socket.io"')
        body_str = body_str.replace("||'/socket.io'", "||'/dev/agor/socket.io'")

        # 3. Fix React Router basename (usually in JS)
        body_str = body_str.replace('basename:"/ui"', 'basename:"/dev/agor/ui"')
        body_str = body_str.replace('basename="/ui"', 'basename="/dev/agor/ui"')
        body_str = body_str.replace("basename:'/ui'", "basename:'/dev/agor/ui'")
        body_str = body_str.replace("basename='/ui'", "basename='/dev/agor/ui'")

        # 4. Fix asset paths in JS/CSS
        # "/ui/assets/..." -> "/dev/agor/ui/assets/..."
        body_str = body_str.replace('"/ui/assets/', '"/dev/agor/ui/assets/')
        body_str = body_str.replace("'/ui/assets/", "'/dev/agor/ui/assets/")
        body_str = body_str.replace('"/ui/fonts/', '"/dev/agor/ui/fonts/')
        body_str = body_str.replace('"/ui/images/', '"/dev/agor/ui/images/')
        body_str = body_str.replace('"/ui/static/', '"/dev/agor/ui/static/')
        
        # CSS url() rewrites
        # url(/ui/...) -> url(/dev/agor/ui/...)
        body_str = re.sub(r'url(["\\]?)/ui/', r'url(/dev/agor/ui/', body_str)

        # 5. Agor 0.9.0 specific path check fix
        body_str = body_str.replace(
            'window.location.pathname.startsWith("/ui")',
            '(window.location.pathname.startsWith("/ui")||window.location.pathname.includes("/agor/ui"))'
        )

        # 6. Inject <base> tag in HTML
        if '<head>' in body_str:
            base_injection = '<head>\n    <base href="/dev/agor/ui/">' # Note: escaped newline for clarity in string literal
            body_str = body_str.replace('<head>', base_injection, 1)

        # 7. Increase Socket.IO timeout in JS
        body_str = re.sub(
            r'(transports:\s*\[[^\]]+\])',
            r'\1,timeout:60000',
            body_str
        )

        # 8. Rewrite API paths (critical for login and health checks)
        # Matches: "/health", '/health', etc.
        body_str = body_str.replace('"/health"', '"/dev/agor/health"')
        body_str = body_str.replace("'/health'", "'/dev/agor/health'")
        
        body_str = body_str.replace('"/auth"', '"/dev/agor/auth"')
        body_str = body_str.replace("'/auth'", "'/dev/agor/auth'")
        
        body_str = body_str.replace('"/api"', '"/dev/agor/api"')
        body_str = body_str.replace("'/api'", "'/dev/agor/api'")

        logger.info(f"Rewrote content for {path} ({len(body_bytes)} -> {len(body_str)} chars)")
        
        new_body = body_str.encode('utf-8')
        
        # Calculate new headers
        new_headers = {
            'content-length': str(len(new_body)),
            'content-encoding': '' # We decoded it, so remove gzip header
        }
        
        return new_body, new_headers

    async def proxy_request(self, request: Request, path: str):
        # Determine if we need to rewrite this response
        # Ideally we check the RESPONSE content-type, but we need to pass the callback *before* request
        # However, BaseProxy.proxy_request logic:
        # We can check headers after response starts? 
        # My BaseProxy.proxy_request needs to be smart enough to conditionally call the callback
        # OR we override proxy_request here entirely but reuse get_session.
        
        # Actually, let's reuse the BaseProxy logic but wrapped.
        # Wait, BaseProxy accepts a callback. But we only know if we need to use it AFTER seeing headers.
        # The current BaseProxy implementation takes the callback and uses it unconditionally if provided.
        # Let's modify BaseProxy to allow decision based on headers, OR we just override here. 
        
        # Easier to override for now to keep BaseProxy simple
        
        session = await self.get_session()
        
        # Build target URL
        url = f"{self.base_url}/{path}"
        if request.url.query:
            url += f"?{request.url.query}"

        headers = self._prepare_headers(request)
        # Do NOT force gzip for Agor request headers, let it auto-negotiate
        # Robustly remove accept-encoding to avoid double-compression issues during rewrite
        keys_to_remove = [k for k in headers.keys() if k.lower() == 'accept-encoding']
        for k in keys_to_remove:
            del headers[k]

        method = request.method.upper()
        data = request.stream()

        try:
            # Create request context
            req_ctx = session.request(method, url, headers=headers, data=data)
            resp = await req_ctx.__aenter__()

            content_type = resp.headers.get('content-type', '').lower()
            content_encoding = resp.headers.get('content-encoding', '').lower()
            
            # Check if we need to rewrite
            should_rewrite = (
                'text/html' in content_type or 
                'javascript' in content_type or 
                'text/css' in content_type or
                path.endswith('.js') or 
                path.endswith('.css')
            )

            if should_rewrite:
                try:
                    body = await resp.read()
                finally:
                    await req_ctx.__aexit__(None, None, None)
                
                # Handle decompression if needed
                if content_encoding == 'gzip':
                    import gzip
                    try:
                        body = gzip.decompress(body)
                    except Exception as e:
                        logger.error(f"Failed to decompress gzip body: {e}")
                elif content_encoding == 'deflate':
                    import zlib
                    try:
                        body = zlib.decompress(body)
                    except Exception as e:
                        logger.error(f"Failed to decompress deflate body: {e}")
                elif content_encoding == 'br':
                    try:
                        import brotli
                        body = brotli.decompress(body)
                    except ImportError:
                        logger.error("Brotli compression received but 'brotli' module not installed")
                    except Exception as e:
                        logger.error(f"Failed to decompress brotli body: {e}")

                # Rewrite the body
                new_body, new_headers = await self._rewrite_response_body(body, resp.headers, path)
                
                # Prepare response headers
                excluded_resp_headers = {'content-length', 'transfer-encoding', 'connection', 'content-encoding'}
                response_headers = {}
                for k, v in resp.headers.items():
                    if k.lower() not in excluded_resp_headers:
                        response_headers[k] = v
                
                response_headers.update(new_headers)
                
                return StreamingResponse(
                    iter([new_body]),
                    status_code=resp.status,
                    headers=response_headers,
                    media_type=content_type
                )
            else:
                # Standard Streaming (Images, Fonts, API data)
                
                # Prepare response headers
                excluded_resp_headers = {'content-length', 'transfer-encoding', 'connection', 'content-encoding'}
                response_headers = {}
                for k, v in resp.headers.items():
                    if k.lower() not in excluded_resp_headers:
                        response_headers[k] = v
                
                # Re-add content-encoding if upstream sent it (e.g. gzip)
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
                    media_type=content_type
                )

        except Exception as e:
            logger.error(f"[AgorProxy] Error: {e}")
            # Clean up if context manager was entered but not exited? 
            # aiohttp handles this if exception raised inside block.
            raise HTTPException(status_code=500, detail=str(e))

_agor_proxy_instance: AgorProxy = None

def get_proxy() -> AgorProxy:
    global _agor_proxy_instance
    if _agor_proxy_instance is None:
        # Auto-detects environment and configures SOCKS5 if needed
        _agor_proxy_instance = AgorProxy()
    return _agor_proxy_instance