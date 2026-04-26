from fastapi import FastAPI, Request
from core.config import settings
from fastapi.staticfiles import StaticFiles
from apis.route_general import general_router
from apis.route_education import education_router
from apis.route_hobbies import hobby_router
from apis.route_other import other_router
from apis.route_projects import project_router
from pathlib import Path
import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def include_router(app):
    app.include_router(general_router)
    app.include_router(education_router)
    app.include_router(hobby_router)
    app.include_router(other_router)
    app.include_router(project_router)


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
