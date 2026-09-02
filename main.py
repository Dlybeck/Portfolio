from fastapi import FastAPI, Request
from core.config import settings
from fastapi.staticfiles import StaticFiles
from apis.route_portfolio import portfolio_router
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def include_router(app):
    app.include_router(portfolio_router)


def configure_static(app):
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def start_application():
    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    include_router(app)
    configure_static(app)

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"INCOMING REQUEST: {request.method} {request.url.path}")
        response = await call_next(request)
        logger.info(f"RESPONSE STATUS: {response.status_code} for {request.url.path}")
        return response

    return app


app = start_application()

if __name__ == "__main__":
    import uvicorn

    port = 8080
    uvicorn.run(app, host="0.0.0.0", port=port)
