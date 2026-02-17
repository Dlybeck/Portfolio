from fastapi import APIRouter
import asyncio

from services.opencode_web_proxy import get_opencode_proxy
from services.openhands_web_proxy import get_openhands_proxy
from services.code_server_proxy import get_proxy

# Unified health endpoint for all OpenCode/OpenHands proxies
service_health_router = APIRouter(prefix="/api/service", tags=["Service Health"])


@service_health_router.get("/health")
async def service_health():
    """Aggregate health checks for OpenCode, OpenHands, and Code Server proxies."""
    opencode = get_opencode_proxy()
    openhands = get_openhands_proxy()
    code_server = get_proxy()

    # Run health checks in parallel
    results = await asyncio.gather(
        opencode.check_health(),
        openhands.check_health(),
        code_server.check_health(),
        return_exceptions=False,
    )

    overall = all(r.get("healthy", False) for r in results)

    return {
        "healthy": overall,
        "services": {
            "OpenCodeWebProxy": results[0] if len(results) > 0 else None,
            "OpenHandsWebProxy": results[1] if len(results) > 1 else None,
            "CodeServerProxy": results[2] if len(results) > 2 else None,
        },
    }
