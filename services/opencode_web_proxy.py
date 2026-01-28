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

        # Relax Content Security Policy to allow connections to opencode.ai and data: URIs for media
        for csp_header in ['content-security-policy', 'Content-Security-Policy']:
            csp = response.headers.get(csp_header)
            if csp:
                directives = [d.strip() for d in csp.split(';') if d.strip()]
                new_directives = []
                found_connect = False
                found_media = False
                
                for d in directives:
                    # Allow opencode.ai for API calls
                    if d.startswith('connect-src'):
                        if 'https://opencode.ai' not in d:
                            d = f"{d} https://opencode.ai"
                        if 'data:' not in d:
                            d = f"{d} data:"
                        found_connect = True
                    
                    # Allow data: for audio/video (like notification sounds)
                    if d.startswith('media-src'):
                        if 'data:' not in d:
                            d = f"{d} data:"
                        if "'self'" not in d:
                            d = f"{d} 'self'"
                        found_media = True
                        
                    new_directives.append(d)
                
                if not found_connect:
                    new_directives.append("connect-src 'self' data: https://opencode.ai")
                if not found_media:
                    new_directives.append("media-src 'self' data:")
                
                response.headers[csp_header] = "; ".join(new_directives)
        
        if path == '' or path == '/':
            content_type = response.headers.get('content-type', '')
            if 'text/html' in content_type:
                body = b''
                async for chunk in response.body_iterator:
                    body += chunk
                
                html = body.decode('utf-8', errors='ignore')
                
                lang_script = '''<script>
// Locale Fix: Clear Service Workers and caches first
console.log('[OpenCode Locale Fix] Starting locale enforcement');

// Unregister all service workers
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.getRegistrations().then(function(registrations) {
        registrations.forEach(function(registration) {
            console.log('[OpenCode Locale Fix] Unregistering Service Worker:', registration.scope);
            registration.unregister();
        });
    });
}

// Clear all caches
if ('caches' in window) {
    caches.keys().then(function(keys) {
        keys.forEach(function(key) {
            console.log('[OpenCode Locale Fix] Clearing cache:', key);
            caches.delete(key);
        });
    });
}

// Set locale in localStorage
localStorage.setItem('vscode-nls-locale', 'en-US');
localStorage.setItem('locale', 'en-US');
localStorage.setItem('oc-locale', 'en-US');
console.log('[OpenCode Locale Fix] localStorage set:', {
    'vscode-nls-locale': localStorage.getItem('vscode-nls-locale'),
    'locale': localStorage.getItem('locale'),
    'oc-locale': localStorage.getItem('oc-locale')
});

// Override navigator.language
Object.defineProperty(navigator, 'language', {
  get: function() { return 'en-US'; },
  configurable: true
});
Object.defineProperty(navigator, 'languages', {
  get: function() { return ['en-US', 'en']; },
  configurable: true
});
console.log('[OpenCode Locale Fix] navigator.language overridden to:', navigator.language);
</script>'''

                logger.info(f"[OpenCodeWebProxy] Injecting locale enforcement script (len={len(lang_script)})")

                if '<head>' in html:
                    html = html.replace('<head>', f'<head>{lang_script}', 1)
                    logger.info(f"[OpenCodeWebProxy] Locale script injected into <head>")
                else:
                    html = lang_script + html
                    logger.info(f"[OpenCodeWebProxy] Locale script prepended to HTML (no <head> tag found)")
                
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
