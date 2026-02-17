#!/usr/bin/env python3
"""
Service status monitoring helpers.

Provides:
- check_port_availability(port, host='127.0.0.1', timeout=5.0)
- check_service_health(service_name)
- internal uptime tracking per service

Notes:
- Uses non-blocking port checks via asyncio.open_connection
- Health checks are performed via a lightweight HTTP GET executed in a thread
  to avoid adding runtime HTTP dependencies.
- All checks have a configurable 5s health-check timeout by default.
- Returns structured data suitable for dashboards or tests.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Optional

import urllib.request
import urllib.error


# Simple in-process uptime tracker per service name
_service_start_times: Dict[str, float] = {}


def _start_time_for(service_name: str) -> float:
    """Record and return the start time for a service (in seconds since epoch)."""
    if service_name not in _service_start_times:
        _service_start_times[service_name] = time.time()
    return _service_start_times[service_name]


def _uptime_seconds_for(service_name: str) -> Optional[float]:
    """Return uptime in seconds for a service, or None if unknown."""
    start = _service_start_times.get(service_name)
    if start is None:
        return None
    return time.time() - start


async def check_port_availability(
    port: int, host: str = "127.0.0.1", timeout: float = 5.0
) -> Dict[str, Any]:
    """Asynchronously check if a local TCP port is open.

    Returns a dict with: port, open (bool), latency_ms (float|None), error (str|None)
    """
    result: Dict[str, Any] = {
        "port": port,
        "open": False,
        "latency_ms": None,
        "error": None,
    }
    start = time.perf_counter()
    try:
        # Open a connection; timeout is handled by wait_for
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(host, port), timeout=timeout
        )
        writer.close()
        try:
            await writer.wait_closed()
        except Exception:
            pass
        latency = (time.perf_counter() - start) * 1000.0
        result["open"] = True
        result["latency_ms"] = latency
        return result
    except asyncio.TimeoutError:
        result["error"] = "timeout"
        return result
    except (ConnectionRefusedError, OSError) as e:
        result["error"] = str(e)
        return result
    except Exception as e:
        result["error"] = f"unexpected: {e}"
        return result


async def _http_health_check(url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """Perform a lightweight HTTP GET using a thread to avoid extra deps.

    Returns a dict with: status_code (int|None), response_ms (float|None), error (str|None)
    """
    loop = asyncio.get_event_loop()
    start = time.perf_counter()

    def _get():
        try:
            with urllib.request.urlopen(url, timeout=int(timeout)) as resp:
                resp.read()  # drain body
                return resp.getcode()
        except Exception as ex:
            raise ex

    try:
        code = await loop.run_in_executor(None, _get)
        duration = (time.perf_counter() - start) * 1000.0
        return {"status_code": int(code), "response_ms": duration, "error": None}
    except Exception as ex:
        duration = (time.perf_counter() - start) * 1000.0
        return {"status_code": None, "response_ms": duration, "error": str(ex)}


HEALTH_MAP = {
    # service_name: { host, port, endpoint }
    "OpenCode": {"host": "127.0.0.1", "port": 4096, "endpoint": "/global/health"},
    "OpenHands": {"host": "127.0.0.1", "port": 3000, "endpoint": "/api/health"},
}


async def check_service_health(service_name: str) -> Dict[str, Any]:
    """Poll the health endpoint for a named service.

    Returns a structured dict including port status, health status, response time, and uptime.
    """
    # Resolve mapping; fall back to a best-effort default if unknown
    mapping = HEALTH_MAP.get(service_name)
    if mapping is None:
        # Unknown service: mark as unhealthy and return without endpoint
        _start_time_for(service_name)
        return {
            "service": service_name,
            "port": None,
            "endpoint": None,
            "healthy": False,
            "status_code": None,
            "response_ms": None,
            "uptime_s": None,
        }

    host = mapping["host"]
    port = mapping["port"]
    endpoint = mapping["endpoint"]
    url = f"http://{host}:{port}{endpoint}"

    # Ensure we start uptime tracking when we first probe this service
    _start_time_for(service_name)

    # First, check port availability (fast fail if port down)
    port_status = await check_port_availability(port, host=host, timeout=5.0)
    if not port_status.get("open"):
        return {
            "service": service_name,
            "port": port,
            "endpoint": endpoint,
            "healthy": False,
            "status_code": None,
            "response_ms": None,
            "uptime_s": _uptime_seconds_for(service_name),
            "port_status": port_status,
        }

    # Port is open; perform HTTP health check
    http_result = await _http_health_check(url, timeout=5.0)
    code = http_result.get("status_code")
    resp_ms = http_result.get("response_ms")
    healthy = isinstance(code, int) and 200 <= code < 300

    return {
        "service": service_name,
        "port": port,
        "endpoint": endpoint,
        "healthy": healthy,
        "status_code": code,
        "response_ms": resp_ms,
        "uptime_s": _uptime_seconds_for(service_name),
        "port_status": port_status,
    }


async def monitor_all_services() -> Dict[str, Any]:
    """Convenience helper to check all known services' health in parallel."""
    results = {}
    tasks = {
        name: asyncio.create_task(check_service_health(name))
        for name in HEALTH_MAP.keys()
    }
    for name, task in tasks.items():
        results[name] = await task
    return results


__all__ = [
    "check_port_availability",
    "check_service_health",
    "monitor_all_services",
]
