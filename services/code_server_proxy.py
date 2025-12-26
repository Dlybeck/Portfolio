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
        injection = '''
<script>
// Store token from query parameter for code-server session persistence
(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('tkn');

    if (token) {
        // Store token and metadata in localStorage
        localStorage.setItem('access_token', token);
        localStorage.setItem('expires_in', '1800'); // 30 minutes in seconds
        localStorage.setItem('login_time', Math.floor(Date.now() / 1000).toString());
        console.log('[CodeServer] Stored authentication token from URL');

        // Create a dummy refresh token (not used for refresh in code-server context)
        // This prevents the auth service from skipping refresh checks
        if (!localStorage.getItem('refresh_token')) {
            localStorage.setItem('refresh_token', token);
        }

        // Clean URL to remove token from history
        if (window.history.replaceState) {
            const cleanUrl = window.location.pathname + window.location.search.replace(/[?&]tkn=[^&]+/, '').replace(/^&/, '?');
            window.history.replaceState({}, document.title, cleanUrl);
        }
    }

    // Simple token refresh service for code-server context
    // Checks every 5 minutes and refreshes 5 minutes before expiry
    setInterval(async function() {
        const accessToken = localStorage.getItem('access_token');
        const expiresIn = localStorage.getItem('expires_in');
        const loginTime = localStorage.getItem('login_time');

        if (!accessToken || !expiresIn || !loginTime) {
            return;
        }

        const now = Math.floor(Date.now() / 1000);
        const tokenAge = now - parseInt(loginTime);
        const expiresInSeconds = parseInt(expiresIn);
        const timeUntilExpiry = expiresInSeconds - tokenAge;

        console.log('[CodeServer] Token age:', tokenAge, 's, expires in:', timeUntilExpiry, 's');

        // Refresh if less than 5 minutes until expiry
        if (timeUntilExpiry <= 300) {
            console.log('[CodeServer] Token expiring soon, refreshing...');

            try {
                // Get the current origin (portfolio server, not code-server)
                // Code-server is served at /dev/vscode, so we go up to the root
                const portfolioOrigin = window.location.origin;
                const refreshToken = localStorage.getItem('refresh_token');

                const response = await fetch(portfolioOrigin + '/auth/refresh', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        refresh_token: refreshToken
                    })
                });

                if (response.ok) {
                    const data = await response.json();
                    localStorage.setItem('access_token', data.access_token);
                    localStorage.setItem('refresh_token', data.refresh_token);
                    localStorage.setItem('expires_in', data.expires_in.toString());
                    localStorage.setItem('login_time', Math.floor(Date.now() / 1000).toString());
                    console.log('[CodeServer] Token refreshed successfully');
                } else {
                    console.error('[CodeServer] Token refresh failed:', response.status);
                    if (response.status === 401) {
                        // Refresh token expired, redirect to login
                        console.log('[CodeServer] Session expired, redirecting to login...');
                        window.location.href = portfolioOrigin + '/dev/login';
                    }
                }
            } catch (error) {
                console.error('[CodeServer] Token refresh error:', error);
            }
        }
    }, 5 * 60 * 1000); // Check every 5 minutes
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
