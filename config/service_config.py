"""Service configuration for coding services.

This module exposes a small, explicit mapping of available coding services
and helper functions to validate and fetch their configurations.
"""

from typing import Dict

# Core service configurations. Each entry describes the runtime port and the
# health endpoint for the corresponding service.
SERVICE_CONFIGS: Dict[str, Dict[str, object]] = {
    "openhands": {
        "port": 3000,
        "health_endpoint": "/api/health",
    },
}


def validate_service_name(name: str) -> bool:
    """Return True if the given service name is valid."""
    return name in SERVICE_CONFIGS


def get_service_config(service_name: str = "openhands") -> Dict[str, object]:
    """Return the config for the given service name.

    Args:
        service_name: The service name to fetch. Defaults to 'openhands'.

    Returns:
        A dict containing 'name', 'port', and 'health_endpoint'.
    Raises:
        ValueError: if the service_name is not known.
    """
    if not service_name:
        service_name = "openhands"

    if not validate_service_name(service_name):
        valid = ", ".join(SERVICE_CONFIGS.keys())
        raise ValueError(f"Unknown service '{service_name}'. Valid options: {valid}.")

    cfg = SERVICE_CONFIGS[service_name]
    return {
        "name": service_name,
        "port": cfg["port"],
        "health_endpoint": cfg["health_endpoint"],
    }
