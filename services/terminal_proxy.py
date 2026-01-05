from .base_proxy import BaseProxy
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

class TerminalProxy(BaseProxy):
    def __init__(self):
        super().__init__("http://127.0.0.1:7681/dev/terminal-proxy")

    def _prepare_headers(self, request: Request):
        headers = super()._prepare_headers(request)
        headers['accept-encoding'] = 'identity'
        return headers

    async def proxy_request(self, request: Request, path: str, rewrite_body_callback=None):
        async def force_read(body, headers, p):
            return body, {}
            
        return await super().proxy_request(request, path, rewrite_body_callback=force_read)

_proxy_instance = None

def get_terminal_proxy() -> TerminalProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = TerminalProxy()
    return _proxy_instance
