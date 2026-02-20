from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
from fastapi import Request
from fastapi.responses import StreamingResponse
import logging

logger = logging.getLogger(__name__)


class OpenHandsWebProxy(BaseProxy):
    def __init__(self, openhands_url: str = None):
        if not openhands_url:
            if IS_CLOUD_RUN:
                openhands_url = f"http://{MAC_SERVER_IP}:3000"
            else:
                openhands_url = "http://127.0.0.1:3000"

        super().__init__(openhands_url)
        logger.info(f"OpenHands Web Proxy initialized: {openhands_url}")

    def get_health_endpoint(self) -> str:
        # OpenHands health endpoint is at /api/health
        return "/api/health"

    @property
    def target_url(self) -> str:
        # Compatibility with existing tests that expect a 'target_url' attribute
        return self.base_url

    async def proxy_request(self, request: Request, path: str) -> StreamingResponse:
        response = await super().proxy_request(request, path)

        # Modify CSP to allow our locale-setting inline script and notification sounds
        for csp_header in ["content-security-policy", "Content-Security-Policy"]:
            csp = response.headers.get(csp_header)
            if csp:
                directives = [d.strip() for d in csp.split(";") if d.strip()]
                new_directives = []
                has_media_src = False

                has_connect_src = False
                for d in directives:
                    if d.startswith("script-src"):
                        # Allow inline scripts for locale injection
                        d = f"{d} 'unsafe-inline'"
                    elif d.startswith("media-src"):
                        # Allow data URIs for notification sounds
                        d = f"{d} data:"
                        has_media_src = True
                    elif d.startswith("connect-src"):
                        # Allow WebSocket connections from the proxy domain
                        d = f"{d} 'self' wss: ws:"
                        has_connect_src = True
                    new_directives.append(d)

                # Add media-src if it doesn't exist
                if not has_media_src:
                    new_directives.append("media-src 'self' data:")
                # Add connect-src if it doesn't exist
                if not has_connect_src:
                    new_directives.append("connect-src 'self' wss: ws:")

                response.headers[csp_header] = "; ".join(new_directives)

        is_static_asset = any(
            path.endswith(ext)
            for ext in [
                ".js",
                ".css",
                ".woff",
                ".woff2",
                ".ttf",
                ".png",
                ".svg",
                ".ico",
                ".webp",
            ]
        )

        if is_static_asset:
            response.headers["Cache-Control"] = "public, max-age=31536000, immutable"

        # Inject minimal locale fix for all HTML pages
        content_type = response.headers.get("content-type", "")
        logger.info(
            f"[OpenHandsWebProxy] Processing path: {path}, content-type: {content_type}"
        )
        if "text/html" in content_type:
            from fastapi.responses import Response

            logger.info("[OpenHandsWebProxy] Found HTML response, will inject scripts")

            body = b""
            async for chunk in response.body_iterator:
                body += chunk

            html = body.decode("utf-8", errors="ignore")
            logger.info(
                f"[OpenHandsWebProxy] HTML size: {len(html)} chars, has <head>: {'<head>' in html}"
            )

            # Injected scripts for OpenHands web interface
            # 1. Locale fix: Set i18next language to English before app initializes
            # 2. Mobile health check: Auto-recover from background suspension on mobile Chrome
            injected_scripts = """<script>
// Locale fix: Set i18next localStorage key so OpenHands v1.3+ loads English translations.
// 'i18nextLng' is the standard lookupLocalStorage key used by i18next in OpenHands v1.3.
// The old 'openhands.global.dat:language' key is not present in v1.3 and is ignored.
localStorage.setItem('i18nextLng','en');

// Mobile health check: Recover from background suspension
(function() {
  // Only run on mobile/touch devices
  if (!('ontouchstart' in window || navigator.maxTouchPoints > 0)) return;
  
  const MIN_HIDDEN_TIME = 2000;      // 2s - skip brief tab switches
  const DEBOUNCE_INTERVAL = 10000;   // 10s - no rapid-fire checks
  const CHECK_DELAY = 500;           // 0.5s - stabilize before checking
  const FETCH_TIMEOUT = 5000;        // 5s - health check timeout
  
  let lastHiddenTime = 0;
  let lastCheckTime = 0;
  
  document.addEventListener('visibilitychange', function() {
    if (document.visibilityState === 'visible') {
      const hiddenDuration = Date.now() - lastHiddenTime;
      const timeSinceLastCheck = Date.now() - lastCheckTime;
      
      // Skip if brief tab away or checked recently
      if (hiddenDuration < MIN_HIDDEN_TIME || timeSinceLastCheck < DEBOUNCE_INTERVAL) return;
      
      // Note: Previously skipped if user was typing, but this prevented recovery
      // when returning to a "failed to send" state. Health check is fast enough
      // that it won't interrupt typing, and reload only happens if connection is dead.
      
      setTimeout(checkConnectionHealth, CHECK_DELAY);
    } else {
      lastHiddenTime = Date.now();
    }
  });
  
  async function checkConnectionHealth() {
    lastCheckTime = Date.now();
    console.log('[MobileHealth] Checking connection...');
    
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT);
      
      const response = await fetch('/api/health', {
        signal: controller.signal,
        cache: 'no-store'
      });
      
      clearTimeout(timeoutId);
      
      if (response.ok) {
        console.log('[MobileHealth] Connection OK');
      } else {
        console.log('[MobileHealth] Health check failed (status ' + response.status + '), reloading...');
        window.location.reload();
      }
    } catch (error) {
      console.log('[MobileHealth] Connection dead, reloading...');
      window.location.reload();
    }
  }
})();
</script>"""

            if "<head>" in html:
                html = html.replace("<head>", f"<head>{injected_scripts}", 1)
            else:
                html = injected_scripts + html

            return Response(
                content=html.encode("utf-8"),
                status_code=response.status_code,
                headers=dict(response.headers),
                media_type="text/html",
            )
        return response


_proxy_instance = None


def get_openhands_proxy() -> OpenHandsWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenHandsWebProxy()
    return _proxy_instance
