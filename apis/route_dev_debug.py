"""
Dev Dashboard Debug Routes
"""

from fastapi import APIRouter, Depends
from core.security import get_current_user
from core.config import settings
import socket
import logging

from services.socks5_connection_manager import proxy_request
from services.tailscale_health_monitor import get_health_monitor
from services.socks5_connection_manager import get_connection_manager


logger = logging.getLogger(__name__)

dev_debug_router = APIRouter(prefix="/dev/debug", tags=["Dev Dashboard - Debug"])


@dev_debug_router.get("/connectivity")
async def debug_connectivity(user: dict = Depends(get_current_user)):
    """🔒 Debug endpoint to test Mac connectivity - requires authentication"""

    results = {
        "mac_ip": settings.MAC_SERVER_IP,
        "mac_port": settings.MAC_SERVER_PORT,
        "mac_url": f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}"
    }

    # Test socket connection
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((settings.MAC_SERVER_IP, settings.MAC_SERVER_PORT))
        sock.close()
        results["socket_test"] = {
            "success": result == 0,
            "error_code": result
        }
    except Exception as e:
        results["socket_test"] = {"error": str(e)}

    # Test HTTP request through connection manager
    try:
        response = await proxy_request("GET", f"http://{settings.MAC_SERVER_IP}:{settings.MAC_SERVER_PORT}/")
        results["http_test"] = {
            "status": response.status_code,
            "success": True
        }
    except Exception as e:
        results["http_test"] = {
            "error": str(e),
            "success": False
        }

    return results


@dev_debug_router.get("/tailscale-health")
async def debug_tailscale_health(user: dict = Depends(get_current_user)):
    """🔒 Debug endpoint for Tailscale and SOCKS5 health - requires authentication"""
    if settings.K_SERVICE is None:
        return {
            "environment": "local",
            "message": "Tailscale health monitoring only runs in Cloud Run",
            "tailscale_ip": settings.MAC_SERVER_IP,
        }

    # Get health status from monitor
    monitor = get_health_monitor()
    health_status = monitor.get_status()

    # Get SOCKS5 connection manager stats
    conn_manager = get_connection_manager()
    socks5_health = await conn_manager.check_socks5_health()
    conn_stats = conn_manager.get_stats()

    # Format timestamps
    from datetime import datetime

    def format_timestamp(ts):
        if ts:
            return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")
        return None

    return {
        "environment": "cloud_run",
        "tailscale_monitor": {
            "healthy": health_status["healthy"],
            "status": health_status["status"],
            "consecutive_failures": health_status["consecutive_failures"],
            "last_check": format_timestamp(health_status["last_check_time"]),
            "stats": {
                "total_checks": health_status["stats"]["total_checks"],
                "failures": health_status["stats"]["failures"],
                "recoveries": health_status["stats"]["recoveries"],
                "last_failure": format_timestamp(health_status["stats"].get("last_failure_time")),
                "last_recovery": format_timestamp(health_status["stats"].get("last_recovery_time")),
            }
        },
        "socks5_proxy": socks5_health,
        "connection_manager": {
            "client_active": conn_stats["client_active"],
            "client_age_seconds": round(conn_stats["client_age_seconds"], 1),
            "max_age_seconds": conn_stats["max_age_seconds"],
            "requests": {
                "total": conn_stats["stats"]["total_requests"],
                "failed": conn_stats["stats"]["failed_requests"],
                "retried": conn_stats["stats"]["retried_requests"],
                "last_error": conn_stats["stats"]["last_error"],
                "last_error_time": format_timestamp(conn_stats["stats"]["last_error_time"]),
            }
        },
        "target": {
            "mac_ip": settings.MAC_SERVER_IP,
            "mac_port": settings.MAC_SERVER_PORT,
        }
    }
