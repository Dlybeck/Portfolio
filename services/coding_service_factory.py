#!/usr/bin/env python3
"""Coding service factory

This module provides a lightweight factory to describe available coding
services (OpenCode and OpenHands). It exposes a single helper,
get_coding_service(), which returns a minimal configuration payload for the
requested service. The default service is OpenHands.
"""

import logging
from typing import Any, Dict

# Import proxies for health probes. If the actual modules are not available in
# the runtime environment, provide lightweight fallbacks to keep imports sane.
try:
    from OpenCodeWebProxy import OpenCodeWebProxy  # type: ignore
except Exception:  # pragma: no cover - fallback when not installed

    class OpenCodeWebProxy:  # type: ignore
        pass


try:
    from OpenHandsWebProxy import OpenHandsWebProxy  # type: ignore
except Exception:  # pragma: no cover - fallback when not installed

    class OpenHandsWebProxy:  # type: ignore
        pass


logger = logging.getLogger(__name__)

# Service configuration. Keys are service names; values describe their runtime
# characteristics such as port and health endpoints.
SERVICE_CONFIG = {
    "openhands": {
        "port": 3000,
        "health_endpoint": "/api/health",
        "proxy_class": OpenHandsWebProxy,
    },
    "opencode": {
        "port": 4096,
        "health_endpoint": "/global/health",
        "proxy_class": OpenCodeWebProxy,
    },
}


def get_coding_service(service_name: str | None = None) -> Dict[str, Any]:
    """Return the coding service descriptor.

    Args:
        service_name: Optional service name. If omitted, defaults to 'openhands'.

    Returns:
        A dictionary with keys: service_name, port, health_endpoint, proxy_class.
    """
    if service_name is None:
        service_name = "openhands"

    if service_name not in SERVICE_CONFIG:
        available = ", ".join(SERVICE_CONFIG.keys())
        raise ValueError(
            f"Unknown coding service '{service_name}'. Valid: {available}."
        )

    cfg = SERVICE_CONFIG[service_name]
    logger.info(
        "Selected coding service '%s' (port=%s, health=%s)",
        service_name,
        cfg["port"],
        cfg["health_endpoint"],
    )

    return {
        "service_name": service_name,
        "port": cfg["port"],
        "health_endpoint": cfg["health_endpoint"],
        "proxy_class": cfg["proxy_class"],
    }
