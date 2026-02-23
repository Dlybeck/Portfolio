from fastapi import FastAPI, Request
from core.config import settings
from fastapi.staticfiles import StaticFiles
from apis.route_general import general_router
from apis.route_education import education_router
from apis.route_hobbies import hobby_router
from apis.route_other import other_router
from apis.route_projects import project_router
from apis.route_auth import auth_router
from apis.route_dev import dev_router
from apis.route_health import service_health_router
from apis.route_coding_subdomain import (
    coding_subdomain_middleware,
    CodingWebSocketMiddleware,
)
from core.security import validate_security_config
from pathlib import Path
import logging

# Configure logging early
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
    app.include_router(auth_router)
    app.include_router(dev_router)
    app.include_router(service_health_router)


def configure_static(app):
    static_dir = Path(__file__).parent / "static"
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


def start_application():
    # Validate security configuration on startup
    try:
        validate_security_config()
    except ValueError as e:
        logger.critical(f"Security configuration error: {e}")
        logger.critical("Run setup_security.py to configure authentication")
        logger.critical("Server startup aborted due to security configuration errors")
        import sys

        sys.exit(1)

    app = FastAPI(title=settings.PROJECT_NAME, version=settings.PROJECT_VERSION)
    app.add_middleware(CodingWebSocketMiddleware)
    app.add_middleware(coding_subdomain_middleware)
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
    import subprocess
    import os
    from pathlib import Path

    # Determine if running in Cloud Run
    is_cloud_run = settings.K_SERVICE is not None

    # Check if SSL certificates exist
    ssl_cert_path = Path.home() / ".ssl" / "cert.pem"
    ssl_key_path = Path.home() / ".ssl" / "key.pem"
    has_ssl = ssl_cert_path.exists() and ssl_key_path.exists()

    if is_cloud_run:
        # In Cloud Run, bind to all interfaces (HTTP only)
        logger.info("Running in Cloud Run - binding to 0.0.0.0:8080")
        host = "0.0.0.0"
        port = 8080
        uvicorn.run(
            app,
            host=host,
            port=port,
            timeout_keep_alive=86400,  # 24h for long code-server sessions
            ws_ping_interval=30,  # Keep frequent pings for connection health
            ws_ping_timeout=86400,  # Allow very long idle sessions
        )
    else:
        # Local development - use HTTPS if certificates available
        host = "0.0.0.0"

        if has_ssl:
            # HTTPS mode
            port = 8443
            logger.info("Local development - HTTPS enabled")
            logger.info(f"Binding to https://{host}:{port}")
            logger.info(f"Access via: https://100.84.184.84:{port}/dev")
            logger.info(f"Access via: https://localhost:{port}/dev")
            logger.warning(
                "Browser will show security warning for self-signed certificate - this is expected"
            )

            uvicorn.run(
                app,
                host=host,
                port=port,
                ssl_keyfile=str(ssl_key_path),
                ssl_certfile=str(ssl_cert_path),
                ws_ping_interval=30,
                ws_ping_timeout=86400,
            )
        else:
            # HTTP fallback
            port = 8080
            logger.info("Local development - HTTP mode (no SSL certificates found)")
            logger.info(f"Access via: http://localhost:{port}/dev")
            logger.warning("To enable HTTPS, generate certificates with:")
            logger.info(
                "    openssl req -x509 -newkey rsa:2048 -nodes -keyout ~/.ssl/key.pem -out ~/.ssl/cert.pem -days 365"
            )

            uvicorn.run(app, host=host, port=port, ws_ping_interval=30, ws_ping_timeout=86400)
