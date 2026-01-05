from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class TerminalProxy(BaseProxy):
    def __init__(self, terminal_url: str = None):
        if not terminal_url:
            if IS_CLOUD_RUN:
                terminal_url = f"http://{MAC_SERVER_IP}:7681/dev/terminal-proxy"
            else:
                terminal_url = "http://127.0.0.1:7681/dev/terminal-proxy"
        
        super().__init__(terminal_url)

    def _prepare_headers(self, request: Request):
        headers = super()._prepare_headers(request)
        headers['accept-encoding'] = 'identity'
        return headers

    async def _inject_csp(self, body: bytes, headers: dict, path: str):
        content_type = headers.get('content-type', '')
        if not content_type.startswith('text/html'):
            return body, {}

        # Permissive CSP for ttyd (allows inline scripts/styles and WebSocket)
        permissive_csp = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https: http: wss: ws:;"
        
        new_headers = {
            'content-security-policy': permissive_csp
        }
        
        return body, new_headers

    async def proxy_request(self, request: Request, path: str, rewrite_body_callback=None):
        # Skip callback for static assets to preserve streaming and headers
        skip_extensions = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.ico', '.wasm', '.map')
        is_static_asset = any(path.lower().endswith(ext) for ext in skip_extensions)

        if is_static_asset:
            return await super().proxy_request(request, path)
        else:
            return await super().proxy_request(request, path, rewrite_body_callback=self._inject_csp)

_proxy_instance = None

def get_terminal_proxy() -> TerminalProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = TerminalProxy()
    return _proxy_instance
