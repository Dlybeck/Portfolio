from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
from fastapi.responses import StreamingResponse
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

        return response

_proxy_instance = None

def get_opencode_proxy() -> OpenCodeWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenCodeWebProxy()
    return _proxy_instance
