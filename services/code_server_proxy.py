"""

Code-server HTTP and WebSocket Proxy
Inherits from BaseProxy to reuse connection logic
"""

from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP, CODE_SERVER_PORT
from fastapi import Request
import re
import gzip

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

    async def _inject_auth_service(self, body: bytes, headers: dict, path: str):
        """Inject authentication service into HTML responses to enable token refresh"""
        content_type = headers.get('content-type', '')

        # Only inject into HTML responses
        if not content_type.startswith('text/html'):
            return body, {}

        # Decompress if gzipped
        content_encoding = headers.get('content-encoding', '').lower()
        if content_encoding == 'gzip':
            try:
                body = gzip.decompress(body)
            except Exception as e:
                # If decompression fails, return original body
                return body, {}

        # Decode body
        try:
            html = body.decode('utf-8')
        except UnicodeDecodeError:
            return body, {}

        # Only inject into the main page (not iframes or other HTML fragments)
        if '</head>' not in html or '</body>' not in html:
            return body, {}

        # Create the injection script
        # Note: The parent page (dev_dashboard.html) runs auth-service.js which handles
        # automatic token refresh. Since iframe and parent share localStorage (same origin),
        # this script only needs to sync the initial token - the parent handles refresh.
        injection = '''
<script>
// Sync authentication token from query parameter
// The parent window's auth-service.js handles automatic refresh
(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('tkn');

    if (token) {
        // Only update access token if it's different (avoid overwriting during refresh)
        const currentToken = localStorage.getItem('access_token');
        if (currentToken !== token) {
            localStorage.setItem('access_token', token);
            // Update login time to match the new token
            localStorage.setItem('login_time', Math.floor(Date.now() / 1000).toString());
            console.log('[CodeServer] Synced authentication token from URL');
        }

        // Clean URL to remove token from history
        if (window.history.replaceState) {
            const cleanUrl = window.location.pathname + window.location.search.replace(/[?&]tkn=[^&]+/, '').replace(/^&/, '?');
            window.history.replaceState({}, document.title, cleanUrl);
        }
    }

    // Monitor token expiration and redirect to login if session expires
    // The parent's auth-service.js handles refresh, we just monitor for failures
    setInterval(function() {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');

        // If both tokens are missing, session has expired
        if (!accessToken && !refreshToken) {
            console.log('[CodeServer] Session expired, redirecting to login...');
            window.location.href = window.location.origin + '/dev/login';
        }
    }, 60 * 1000); // Check every minute
})();
</script>
'''

        # Inject before closing </head> tag
        html = html.replace('</head>', f'{injection}</head>', 1)

        new_body = html.encode('utf-8')
        new_headers = {
            'content-length': str(len(new_body)),
            'content-type': 'text/html; charset=utf-8'
            # Note: content-encoding is intentionally omitted since we return uncompressed HTML
            # BaseProxy already excludes it from response_headers, so it won't be included
        }

        return new_body, new_headers

    async def proxy_request(self, request: Request, path: str):
        # Inject auth service into HTML responses
        return await super().proxy_request(request, path, rewrite_body_callback=self._inject_auth_service)

# Global instance logic
_proxy_instance = None

def get_proxy() -> CodeServerProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = CodeServerProxy()
    return _proxy_instance
