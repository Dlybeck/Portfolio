#!/usr/bin/env python3
"""Coding service factory

This module provides a lightweight factory to describe available coding
services (OpenHands only, OpenCode removed as legacy). It exposes a single helper,
get_coding_service(), which returns a minimal configuration payload for the
requested service. The default service is OpenHands.
"""

import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)

# Service configuration. Keys are service names; values describe their runtime
# characteristics such as port and health endpoints.
SERVICE_CONFIG = {
    "openhands": {
        "port": 3000,
        "health_endpoint": "/api/health",
    },
}


def get_coding_service(service_name: str | None = None) -> Dict[str, Any]:
    """Return the coding service descriptor.

    Args:
        service_name: Optional service name. If omitted, defaults to 'openhands'.

    Returns:
        A dictionary with keys: service_name, port, health_endpoint.
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
    }
