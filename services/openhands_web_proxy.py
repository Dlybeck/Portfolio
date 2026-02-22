import json
import re
import logging
from fastapi import Request
from fastapi.responses import Response
from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP

logger = logging.getLogger(__name__)

# Matches the agent server base URL embedded in conversation JSON responses.
# OpenHands V1 conversations return e.g. "url": "http://localhost:36873/api/conversations/..."
# Also handles various URL formats: http://, ws://, just localhost:PORT, or 127.0.0.1:PORT
_LOCALHOST_RE = re.compile(r'(?:http://|ws://|wss://)?(?:localhost|127\.0\.0\.1):(\d+)')

# Injected into every HTML page served by the OpenHands proxy.
# Pre-fetches the English translation bundle synchronously so the Remix SSR
# hydration matches the client render (fixes Firefox React error #418).
_I18N_FIX = """<script>
localStorage.setItem('i18nextLng','en');
(function(){
  var data=null;
  try{var x=new XMLHttpRequest();x.open('GET','/locales/en/translation.json',false);x.send();if(x.status===200)data=x.responseText;}catch(e){}
  if(!data)return;
  var orig=window.fetch;
  window.fetch=function(){
    var url=arguments[0];
    if(typeof url==='string'&&url.indexOf('/locales/en/translation')!==-1){
      return Promise.resolve(new Response(data,{status:200,headers:{'Content-Type':'application/json'}}));
    }
    return orig.apply(this,arguments);
  };
})();
</script>"""


def _extract_agent_urls(data, cache: dict) -> None:
    """Walk JSON data and populate cache with conversation_id → agent base URL."""
    # Handle paginated response format: {"results": [...], "next_page_id": ...}
    if isinstance(data, dict) and "results" in data:
        logger.debug(f"[OpenHandsWebProxy] Found paginated response with {len(data.get('results', []))} results")
        _extract_agent_urls(data["results"], cache)
        # Also check other dict fields that might contain conversations
        for k, v in data.items():
            if k != "results" and isinstance(v, (dict, list)):
                _extract_agent_urls(v, cache)
        return
    
    if isinstance(data, dict):
        # Try multiple possible conversation ID field names
        conv_id = None
        for field in ["conversation_id", "id", "conversationId", "conversationID"]:
            if field in data:
                conv_id = data.get(field)
                break
        
        # Try multiple possible URL field names
        found_url = None
        for field in ["url", "agent_url", "server_url", "websocket_url", "connection_url", "agentUrl", "serverUrl"]:
            if field in data:
                url_value = data.get(field)
                if isinstance(url_value, str):
                    m = _LOCALHOST_RE.search(url_value)
                    if m:
                        found_url = url_value
                        break
        
        # Also search all string values for localhost:PORT patterns
        if not found_url:
            for k, v in data.items():
                if isinstance(v, str):
                    m = _LOCALHOST_RE.search(v)
                    if m:
                        found_url = v
                        logger.debug(f"[OpenHandsWebProxy] Found agent URL in field '{k}': {v}")
                        break
        
        if conv_id and found_url:
            m = _LOCALHOST_RE.search(found_url)
            if m:
                port = m.group(1)
                # Extract base URL: convert any localhost:PORT or 127.0.0.1:PORT to http://localhost:PORT
                # (for WebSocket connections, we'll convert http:// to ws:// later)
                cache[conv_id] = f"http://localhost:{port}"
                logger.info(f"[OpenHandsWebProxy] Cached agent for {conv_id}: {found_url} → http://localhost:{port}")
                
                # Debug: log the full found URL
                logger.debug(f"[OpenHandsWebProxy] Original URL: {found_url}")
            else:
                logger.debug(f"[OpenHandsWebProxy] Found conv_id {conv_id} but no localhost:PORT in URL: {found_url}")
        elif conv_id and not found_url:
            logger.debug(f"[OpenHandsWebProxy] Found conv_id {conv_id} but no agent URL in data")
        elif found_url and not conv_id:
            logger.debug(f"[OpenHandsWebProxy] Found agent URL {found_url} but no conversation ID")
            
        # Recursively search nested structures
        for v in data.values():
            if isinstance(v, (dict, list)):
                _extract_agent_urls(v, cache)
    elif isinstance(data, list):
        for item in data:
            _extract_agent_urls(item, cache)


class OpenHandsWebProxy(BaseProxy):
    def __init__(self, openhands_url: str = None):
        if not openhands_url:
            if IS_CLOUD_RUN:
                openhands_url = f"http://{MAC_SERVER_IP}:3000"
            else:
                openhands_url = "http://127.0.0.1:3000"
        super().__init__(openhands_url)
        # Maps conversation_id → "http://localhost:PORT" (agent server base URL)
        self._agent_urls: dict = {}
        logger.info(f"OpenHands Web Proxy initialized: {openhands_url}")

    def get_health_endpoint(self) -> str:
        return "/health"

    @property
    def target_url(self) -> str:
        return self.base_url

    def get_agent_url(self, conversation_id: str) -> str | None:
        return self._agent_urls.get(conversation_id)

    async def fetch_agent_url(self, conversation_id: str) -> str | None:
        """Fetch agent URL directly from OpenHands API when not yet cached."""
        # Try multiple API endpoint patterns - OpenHands v1.3 might use different paths
        api_patterns = [
            f"{self.base_url}/api/conversations/{conversation_id}",
            f"{self.base_url}/api/v1/conversations/{conversation_id}",
            f"{self.base_url}/api/agent/{conversation_id}",
            f"{self.base_url}/api/agents/{conversation_id}",
        ]
        
        for url in api_patterns:
            try:
                session = await self.get_session()
                logger.info(f"[OpenHandsWebProxy] fetch_agent_url: Attempting GET {url}")
                async with session.get(url) as resp:
                    logger.info(f"[OpenHandsWebProxy] fetch_agent_url: GET {url} → {resp.status}")
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        _extract_agent_urls(data, self._agent_urls)
                        result = self._agent_urls.get(conversation_id)
                        if result:
                            logger.info(f"[OpenHandsWebProxy] Fetched agent URL via API for {conversation_id}: {result}")
                            return result
                        else:
                            logger.debug(f"[OpenHandsWebProxy] No agent URL found in response from {url}")
                            # Try next pattern
                            continue
                    elif resp.status == 404:
                        logger.debug(f"[OpenHandsWebProxy] Endpoint not found: {url}")
                        continue  # Try next pattern
                    else:
                        # Try to read error response
                        try:
                            error_text = await resp.text()
                            logger.warning(f"[OpenHandsWebProxy] fetch_agent_url got status {resp.status} from {url}: {error_text[:200]}")
                        except:
                            logger.warning(f"[OpenHandsWebProxy] fetch_agent_url got status {resp.status} from {url}")
                        continue  # Try next pattern
            except Exception as e:
                logger.debug(f"[OpenHandsWebProxy] fetch_agent_url failed for {url}: {e}")
                continue  # Try next pattern
        
        # If all patterns fail, also try to get from conversations list
        logger.info(f"[OpenHandsWebProxy] All direct endpoints failed, trying conversations list")
        try:
            session = await self.get_session()
            list_patterns = [
                f"{self.base_url}/api/conversations",
                f"{self.base_url}/api/v1/conversations",
            ]
            
            for list_url in list_patterns:
                logger.info(f"[OpenHandsWebProxy] fetch_agent_url: Trying list endpoint {list_url}")
                async with session.get(list_url) as resp:
                    if resp.status == 200:
                        data = await resp.json(content_type=None)
                        _extract_agent_urls(data, self._agent_urls)
                        result = self._agent_urls.get(conversation_id)
                        if result:
                            logger.info(f"[OpenHandsWebProxy] Found agent URL in conversations list for {conversation_id}: {result}")
                            return result
        except Exception as e:
            logger.debug(f"[OpenHandsWebProxy] Conversations list fetch failed: {e}")
        
        logger.warning(f"[OpenHandsWebProxy] No agent URL found for {conversation_id} after trying all endpoints")
        return None

    async def proxy_request(self, request: Request, path: str, rewrite_body_callback=None):
        """Proxy with JSON rewriting and HTML i18n injection.

        - api/ paths: rewrites agent localhost:PORT URLs with the public host.
        - HTML responses: injects _I18N_FIX and adds unsafe-inline to CSP.
        - All other paths stream normally.
        """
        # Step 1: JSON rewriting for api/ paths (existing behavior)
        if not rewrite_body_callback and path.startswith("api/"):
            cache = self._agent_urls
            host = request.headers.get("host", "opencode.davidlybeck.com")
            replacement = f"https://{host}"

            async def _rewrite(body: bytes, headers, path: str):
                content_type = headers.get("content-type", "")
                if "application/json" not in content_type or b"localhost" not in body:
                    return body, {}
                try:
                    text = body.decode("utf-8")
                    data = json.loads(text)
                    _extract_agent_urls(data, cache)
                    rewritten = _LOCALHOST_RE.sub(replacement, text)
                    return rewritten.encode("utf-8"), {"content-type": "application/json; charset=utf-8"}
                except Exception as e:
                    logger.warning(f"[OpenHandsWebProxy] JSON rewrite failed: {e}")
                    return body, {}

            response = await super().proxy_request(request, path, rewrite_body_callback=_rewrite)
        else:
            response = await super().proxy_request(request, path, rewrite_body_callback)

        # Step 2: HTML injection (new behavior) — only for HTML responses
        if "text/html" not in response.headers.get("content-type", ""):
            return response

        # Fix CSP to allow our inline i18n script
        for csp_header in ["content-security-policy", "Content-Security-Policy"]:
            csp = response.headers.get(csp_header)
            if csp:
                directives = [d.strip() for d in csp.split(";") if d.strip()]
                new_directives = []
                for d in directives:
                    if d.startswith("script-src"):
                        d = f"{d} 'unsafe-inline'"
                    new_directives.append(d)
                response.headers[csp_header] = "; ".join(new_directives)

        # Buffer body and inject _I18N_FIX after <head>
        body = b""
        async for chunk in response.body_iterator:
            body += chunk

        html = body.decode("utf-8", errors="ignore")
        if "<head>" in html:
            html = html.replace("<head>", f"<head>{_I18N_FIX}", 1)
        else:
            html = _I18N_FIX + html

        return Response(
            content=html.encode("utf-8"),
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type="text/html",
        )


_proxy_instance = None


def get_openhands_proxy() -> OpenHandsWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenHandsWebProxy()
    return _proxy_instance
