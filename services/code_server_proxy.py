"""

Code-server HTTP and WebSocket Proxy
Inherits from BaseProxy to reuse connection logic
"""

from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP, CODE_SERVER_PORT
from fastapi import Request

class CodeServerProxy(BaseProxy):
    """Reverse proxy for code-server"""

    def __init__(self, code_server_url: str = None):
        if not code_server_url:
            if IS_CLOUD_RUN:
                code_server_url = f"http://{MAC_SERVER_IP}:{CODE_SERVER_PORT}"
            else:
                code_server_url = "http://127.0.0.1:8888"
        
        super().__init__(code_server_url)

    def _prepare_headers(self, request: Request):
        # Override to force gzip for VS Code
        headers = super()._prepare_headers(request)
        headers['accept-encoding'] = 'gzip'
        return headers

    async def proxy_request(self, request: Request, path: str):
        # No rewrite logic needed for Code Server, just stream it
        return await super().proxy_request(request, path)

# Global instance logic
_proxy_instance = None

def get_proxy() -> CodeServerProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = CodeServerProxy()
    return _proxy_instance
