import json
import re
import logging
from fastapi import Request
from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP

logger = logging.getLogger(__name__)

# Matches the agent server base URL embedded in conversation JSON responses.
# OpenHands V1 conversations return e.g. "url": "http://localhost:36873/api/conversations/..."
_LOCALHOST_RE = re.compile(r'http://localhost:(\d+)')


def _extract_agent_urls(data, cache: dict) -> None:
    """Walk JSON data and populate cache with conversation_id → agent base URL."""
    if isinstance(data, dict):
        conv_id = data.get("conversation_id")
        url = data.get("url") or ""
        m = _LOCALHOST_RE.search(url)
        if conv_id and m:
            port = m.group(1)
            cache[conv_id] = f"http://localhost:{port}"
            logger.info(f"[OpenHandsWebProxy] Cached agent for {conv_id}: localhost:{port}")
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
        try:
            session = await self.get_session()
            url = f"{self.base_url}/api/conversations/{conversation_id}"
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json(content_type=None)
                    _extract_agent_urls(data, self._agent_urls)
                    result = self._agent_urls.get(conversation_id)
                    if result:
                        logger.info(f"[OpenHandsWebProxy] Fetched agent URL via API for {conversation_id}: {result}")
                    return result
        except Exception as e:
            logger.warning(f"[OpenHandsWebProxy] fetch_agent_url failed for {conversation_id}: {e}")
        return None

    async def proxy_request(self, request: Request, path: str, rewrite_body_callback=None):
        """Proxy with JSON rewriting: replaces agent localhost:PORT URLs with the public host.

        Only intercepts api/ responses (small JSON blobs). All other paths stream normally.
        """
        if rewrite_body_callback or not path.startswith("api/"):
            return await super().proxy_request(request, path, rewrite_body_callback)

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

        return await super().proxy_request(request, path, rewrite_body_callback=_rewrite)


_proxy_instance = None


def get_openhands_proxy() -> OpenHandsWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenHandsWebProxy()
    return _proxy_instance
