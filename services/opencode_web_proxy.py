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

        # Modify CSP to allow our locale-setting inline script and notification sounds
        for csp_header in ['content-security-policy', 'Content-Security-Policy']:
            csp = response.headers.get(csp_header)
            if csp:
                directives = [d.strip() for d in csp.split(';') if d.strip()]
                new_directives = []
                has_media_src = False

                for d in directives:
                    if d.startswith('script-src'):
                        # Add hash for our locale script
                        d = f"{d} 'sha256-BGsTYpR42e+MgCy/lAURzGJrGoBW7AgW2ntbkoRIvRQ='"
                    elif d.startswith('media-src'):
                        # Allow data URIs for notification sounds
                        d = f"{d} data:"
                        has_media_src = True
                    new_directives.append(d)

                # Add media-src if it doesn't exist
                if not has_media_src:
                    new_directives.append("media-src 'self' data:")

                response.headers[csp_header] = "; ".join(new_directives)

        is_static_asset = any(path.endswith(ext) for ext in ['.js', '.css', '.woff', '.woff2', '.ttf', '.png', '.svg', '.ico', '.webp'])

        if is_static_asset:
            response.headers['Cache-Control'] = 'public, max-age=31536000, immutable'

        # Inject minimal locale fix for all HTML pages
        content_type = response.headers.get('content-type', '')
        if 'text/html' in content_type:
            from fastapi.responses import Response

            body = b''
            async for chunk in response.body_iterator:
                body += chunk

            html = body.decode('utf-8', errors='ignore')

            # Minimal locale fix: set OpenCode language and theme preferences
            # Run after DOM loads to ensure OpenCode doesn't overwrite
            locale_script = """<script>
(function() {
  function setDefaults() {
    localStorage.setItem('opencode.global.dat:language','{"locale":"en"}');
    localStorage.setItem('opencode-theme-id','nord');
  }
  // Try immediately
  setDefaults();
  // And on DOMContentLoaded in case OpenCode clears it
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', setDefaults);
  }
})();
</script>"""

            if '<head>' in html:
                html = html.replace('<head>', f'<head>{locale_script}', 1)
            else:
                html = locale_script + html

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
