from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
import logging

logger = logging.getLogger(__name__)

# Keyboard bridge script to inject into ttyd HTML
# This listens for postMessage events from the parent page and converts them to terminal input
KEYBOARD_BRIDGE_SCRIPT = '''
<script>
(function() {
    // Wait for terminal to be ready
    function waitForTerminal(callback, maxAttempts) {
        let attempts = 0;
        const check = function() {
            attempts++;
            // ttyd exposes terminal as window.term
            const term = window.term;
            if (term) {
                callback(term);
            } else if (attempts < maxAttempts) {
                setTimeout(check, 100);
            }
        };
        check();
    }

    // Map key events to ANSI escape sequences
    function mapKeyToSequence(key, ctrlKey) {
        // Handle Ctrl+letter combinations (Ctrl+A=1, Ctrl+B=2, ... Ctrl+Z=26)
        if (ctrlKey && key.length === 1) {
            const code = key.toLowerCase().charCodeAt(0) - 96;
            if (code >= 1 && code <= 26) {
                return String.fromCharCode(code);
            }
        }

        // Handle special keys
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

    // Listen for keyboard events from parent window
    window.addEventListener('message', function(event) {
        if (!event.data || event.data.type !== 'keyboard-event') return;

        const { key, ctrlKey, altKey } = event.data;

        waitForTerminal(function(term) {
            const sequence = mapKeyToSequence(key, ctrlKey);
            if (sequence) {
                // Send to terminal
                term.write(sequence);
            }
        }, 50);
    });

    console.log('[keyboard-bridge] Mobile keyboard bridge initialized');
})();
</script>
'''

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

    async def _modify_html_response(self, body: bytes, headers: dict, path: str):
        content_type = headers.get('content-type', '')
        if not content_type.startswith('text/html'):
            return body, {}

        # Decode HTML and inject keyboard bridge script before </body>
        try:
            html = body.decode('utf-8')
            if '</body>' in html:
                html = html.replace('</body>', KEYBOARD_BRIDGE_SCRIPT + '</body>')
            body = html.encode('utf-8')
        except Exception as e:
            logger.warning(f"Failed to inject keyboard bridge: {e}")

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
            return await super().proxy_request(request, path, rewrite_body_callback=self._modify_html_response)

_proxy_instance = None

def get_terminal_proxy() -> TerminalProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = TerminalProxy()
    return _proxy_instance
