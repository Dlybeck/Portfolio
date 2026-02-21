from fastapi import APIRouter
import asyncio

from services.openhands_web_proxy import get_openhands_proxy
from services.code_server_proxy import get_proxy

# Unified health endpoint for OpenHands and Code Server proxies
service_health_router = APIRouter(prefix="/api/service", tags=["Service Health"])


@service_health_router.get("/health")
async def service_health():
    """Aggregate health checks for OpenHands and Code Server proxies."""
    openhands = get_openhands_proxy()
    code_server = get_proxy()

    # Run health checks in parallel
    results = await asyncio.gather(
        openhands.check_health(),
        code_server.check_health(),
        return_exceptions=False,
    )

    overall = all(r.get("healthy", False) for r in results)

    return {
        "healthy": overall,
        "services": {
            "OpenHandsWebProxy": results[0] if len(results) > 0 else None,
            "CodeServerProxy": results[1] if len(results) > 1 else None,
        },
    }
