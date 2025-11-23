"""
Main Dev Dashboard Router
Includes all dev-related sub-routers
"""

from fastapi import APIRouter
from .route_dev_core import dev_core_router
from .route_dev_debug import dev_debug_router
from .route_dev_api import dev_api_router
from .route_dev_proxy import dev_proxy_router

dev_router = APIRouter()

dev_router.include_router(dev_core_router)
dev_router.include_router(dev_debug_router)
dev_router.include_router(dev_api_router)
dev_router.include_router(dev_proxy_router)