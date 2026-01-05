from fastapi import APIRouter
from .route_dev_pages import dev_pages_router
from .route_dev_proxy import dev_proxy_router

dev_router = APIRouter(prefix="/dev", tags=["Dev Environment"])

dev_router.include_router(dev_pages_router)
dev_router.include_router(dev_proxy_router)
