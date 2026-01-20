"""

Code-server HTTP and WebSocket Proxy
Inherits from BaseProxy to reuse connection logic
"""

from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP, CODE_SERVER_PORT
from fastapi import Request
import re
import gzip

# Keyboard bridge script for code-server terminal
# Listens for postMessage and dispatches keyboard events to VS Code
KEYBOARD_BRIDGE_SCRIPT = '''
<script>
(function() {
    // Map key events to ANSI escape sequences
    function mapKeyToSequence(key, ctrlKey) {
        if (ctrlKey && key.length === 1) {
            const code = key.toLowerCase().charCodeAt(0) - 96;
            if (code >= 1 && code <= 26) {
                return String.fromCharCode(code);
            }
        }
        const keyMap = {
            'Escape': '\\x1b',
            'Tab': '\\t',
            'ArrowUp': '\\x1b[A',
            'ArrowDown': '\\x1b[B',
            'ArrowRight': '\\x1b[C',
            'ArrowLeft': '\\x1b[D',
            'Enter': '\\r',
            'Backspace': '\\x7f'
        };
        return keyMap[key] || null;
    }

    // Try to find and write to the terminal
    function sendToTerminal(sequence) {
        // Method 1: Try xterm.js terminals in VS Code
        const xtermElements = document.querySelectorAll('.xterm');
        for (const el of xtermElements) {
            if (el._xterm) {
                el._xterm.write(sequence);
                return true;
            }
        }

        // Method 2: Dispatch keyboard event to focused element
        const activeEl = document.activeElement;
        if (activeEl && activeEl.closest('.xterm')) {
            // Create and dispatch a custom input event
            const inputEvent = new InputEvent('input', {
                data: sequence,
                inputType: 'insertText',
                bubbles: true
            });
            activeEl.dispatchEvent(inputEvent);
            return true;
        }

        return false;
    }

    window.addEventListener('message', function(event) {
        if (!event.data || event.data.type !== 'keyboard-event') return;

        const { key, ctrlKey } = event.data;
        const sequence = mapKeyToSequence(key, ctrlKey);

        if (sequence) {
            sendToTerminal(sequence);
        }
    });

    console.log('[keyboard-bridge] Code-server keyboard bridge initialized');
})();
</script>
'''

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
        content_type = headers.get('content-type', '')

        if not content_type.startswith('text/html'):
            return body, {}

        content_encoding = headers.get('content-encoding', '').lower()
        if content_encoding == 'gzip':
            try:
                body = gzip.decompress(body)
            except Exception as e:
                return body, {}

        try:
            html = body.decode('utf-8')
        except UnicodeDecodeError:
            return body, {}

        permissive_csp = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob: https: http: wss: ws:;"

        if '</head>' in html and '</body>' in html:
            auth_injection = '''
<script>
(function() {
    const urlParams = new URLSearchParams(window.location.search);
    const token = urlParams.get('tkn');

    if (token) {
        const currentToken = localStorage.getItem('access_token');
        if (currentToken !== token) {
            localStorage.setItem('access_token', token);
            localStorage.setItem('login_time', Math.floor(Date.now() / 1000).toString());
            console.log('[CodeServer] Synced authentication token from URL');
        }

        if (window.history.replaceState) {
            const cleanUrl = window.location.pathname + window.location.search.replace(/[?&]tkn=[^&]+/, '').replace(/^&/, '?');
            window.history.replaceState({}, document.title, cleanUrl);
        }
    }

    setInterval(function() {
        const accessToken = localStorage.getItem('access_token');
        const refreshToken = localStorage.getItem('refresh_token');

        if (!accessToken && !refreshToken) {
            console.log('[CodeServer] Session expired, redirecting to login...');
            window.location.href = window.location.origin + '/dev/login';
        }
    }, 60 * 1000);
})();
</script>
'''
            html = html.replace('</head>', f'{auth_injection}</head>', 1)
            # Inject keyboard bridge before </body>
            html = html.replace('</body>', f'{KEYBOARD_BRIDGE_SCRIPT}</body>', 1)

        new_body = html.encode('utf-8')
        
        new_headers = {
            'content-length': str(len(new_body)),
            'content-type': 'text/html; charset=utf-8',
            'content-security-policy': permissive_csp
        }

        return new_body, new_headers

    async def proxy_request(self, request: Request, path: str):
        # Only inject auth service into HTML responses (skip callback for JS/CSS/images)
        # This avoids buffering non-HTML files and preserves their content-encoding headers

        # Check if this is likely a non-HTML file by extension
        # Skip callback for JS, CSS, images, fonts, WASM, etc. to preserve compression headers
        skip_extensions = ('.js', '.css', '.png', '.jpg', '.jpeg', '.gif', '.svg', '.woff', '.woff2', '.ttf', '.eot', '.ico', '.wasm', '.map')
        is_static_asset = any(path.lower().endswith(ext) for ext in skip_extensions)

        if is_static_asset:
            # Stream without callback to preserve content-encoding headers
            return await super().proxy_request(request, path)
        else:
            # Use callback for HTML pages and other content
            return await super().proxy_request(request, path, rewrite_body_callback=self._inject_auth_service)

# Global instance logic
_proxy_instance = None

def get_proxy() -> CodeServerProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = CodeServerProxy()
    return _proxy_instance
