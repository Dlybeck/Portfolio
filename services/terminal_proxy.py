from .base_proxy import BaseProxy
from fastapi import Request
from fastapi.responses import Response
import subprocess
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
        if path == "" or path == "/" or path == "token":
            endpoint = "/" if path in ("", "/") else f"/{path}"
            media = "text/html" if path in ("", "/") else "application/json"
            try:
                cmd = ["curl", "-s", f"http://127.0.0.1:7681/dev/terminal-proxy{endpoint}"]
                result = subprocess.run(cmd, capture_output=True, timeout=5)
                if result.returncode == 0 and result.stdout:
                    return Response(content=result.stdout, media_type=media)
                else:
                    logger.error(f"Curl failed for {endpoint}: {result.stderr}")
            except Exception as e:
                logger.error(f"Curl fetch error for {endpoint}: {e}")

        async def force_read(body, headers, p):
            return body, {}
            
        return await super().proxy_request(request, path, rewrite_body_callback=force_read)

_proxy_instance = None

def get_terminal_proxy() -> TerminalProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = TerminalProxy()
    return _proxy_instance
