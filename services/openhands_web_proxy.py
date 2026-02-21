from .base_proxy import BaseProxy, IS_CLOUD_RUN, MAC_SERVER_IP
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
        return "/health"

    @property
    def target_url(self) -> str:
        return self.base_url


_proxy_instance = None


def get_openhands_proxy() -> OpenHandsWebProxy:
    global _proxy_instance
    if _proxy_instance is None:
        _proxy_instance = OpenHandsWebProxy()
    return _proxy_instance
