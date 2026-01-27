from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
from fastapi.responses import StreamingResponse, Response
import logging

logger = logging.getLogger(__name__)

class OpenCodeWebProxy(BaseProxy):
    def __init__(self, opencode_url: str = None):
        if not opencode_url:
            if IS_CLOUD_RUN:
                opencode_url = f"http://{MAC_SERVER_IP}:4096"
            else:
                opencode_url = "http://127.0.0.1:4096"

        super().__init__(opencode_url)
        logger.info(f"OpenCode Web Proxy initialized: {opencode_url}")
    
    async def proxy_request(self, request: Request, path: str) -> StreamingResponse:
        response = await super().proxy_request(request, path)
        
        is_static_asset = any(path.endswith(ext) for ext in ['.js', '.css', '.woff', '.woff2', '.ttf', '.png', '.svg', '.ico', '.webp'])
        
        if is_static_asset:
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'
        
        if path == '' or path == '/':
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                body = b''
                async for chunk in response.body_iterator:
                    body += chunk
                
                html = body.decode('utf-8', errors='ignore')
                
                lang_script = '''<script>
localStorage.setItem('oc-locale', 'en-US');
Object.defineProperty(navigator, 'language', {
  get: function() { return 'en-US'; },
  configurable: true
});
Object.defineProperty(navigator, 'languages', {
  get: function() { return ['en-US', 'en']; },
  configurable: true
});
</script>'''
                
                if '<head>' in html:
                    html = html.replace('<head>', f'<head>{lang_script}', 1)
                else:
                    html = lang_script + html
                
                return Response(
                    content=html.encode('utf-8'),
                    status_code=response.status_code,
                    headers=dict(response.headers),
                    media_type='text/html'
                )
        
        return response

_proxy_instance = None

def get_opencode_proxy() -> OpenCodeWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenCodeWebProxy()
    return _proxy_instance
