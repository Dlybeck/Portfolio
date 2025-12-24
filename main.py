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
from apis.route_speckit import router as speckit_router
try:
    from apis.route_api_proxy import api_proxy_router
    HAS_API_PROXY = True
except Exception as e:
    logging.error(f"Failed to import API proxy router: {e}")
    HAS_API_PROXY = False
    api_proxy_router = None
try:
    from apis.route_agentbridge import router as agentbridge_router
    HAS_AGENTBRIDGE = True
except Exception as e:
    logging.error(f"Failed to import AgentBridge router: {e}")
    HAS_AGENTBRIDGE = False
    agentbridge_router = None
from core.security import validate_security_config
import asyncio
import logging
import subprocess
import socket
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


async def run_startup_diagnostics():
	"""Run comprehensive diagnostics on startup and log results"""
	MAC_SERVER_IP = settings.MAC_SERVER_IP
	MAC_SERVER_PORT = settings.MAC_SERVER_PORT
	SOCKS5_PROXY = settings.SOCKS5_PROXY
	SOCKS5_PORT = settings.SOCKS5_PORT

	# 1. Check Tailscale daemon
	try:
		result = subprocess.run(["pgrep", "-x", "tailscaled"], capture_output=True, timeout=5)
		if result.returncode == 0:
			logger.info("✅ tailscaled process running (PID: %s)", result.stdout.decode().strip())
		else:
			logger.error("❌ tailscaled process NOT running")
	except Exception as e:
		logger.error("❌ Error checking tailscaled: %s", e)

	# 2. Check Tailscale status
	try:
		result = subprocess.run(["tailscale", "status", "--json"], capture_output=True, text=True, timeout=5)
		if result.returncode == 0:
			import json
			status = json.loads(result.stdout)
			backend_state = status.get("BackendState", "unknown")
			if backend_state == "Running":
				self_ip = status.get("Self", {}).get("TailscaleIPs", ["unknown"])[0]
				logger.info("✅ Tailscale connected (IP: %s, State: %s)", self_ip, backend_state)
			else:
				logger.error("❌ Tailscale NOT connected (State: %s)", backend_state)
		else:
			logger.error("❌ tailscale status failed: %s", result.stderr)
	except Exception as e:
		logger.error("❌ Error checking Tailscale status: %s", e)

	# 3. Check SOCKS5 port
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		sock.settimeout(2)
		result = sock.connect_ex(("localhost", SOCKS5_PORT))
		sock.close()
		if result == 0:
			logger.info("✅ SOCKS5 proxy listening on port %d", SOCKS5_PORT)
		else:
			logger.error("❌ SOCKS5 proxy NOT listening on port %d", SOCKS5_PORT)
	except Exception as e:
		logger.error("❌ Error checking SOCKS5 port: %s", e)

	# 4. Test HTTP through SOCKS5
	try:
		async with httpx.AsyncClient(proxy=SOCKS5_PROXY, timeout=10.0) as client:
			response = await client.get(f"http://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/")
			logger.info("✅ HTTP via SOCKS5 successful (status: %d)", response.status_code)
	except Exception as e:
		logger.error("❌ HTTP via SOCKS5 failed: %s (%s)", type(e).__name__, e)

	# 5. Check python-socks installation
	try:
		import python_socks
		logger.info("✅ python-socks installed (version: %s)", python_socks.__version__)
	except ImportError:
		logger.error("❌ python-socks NOT installed")

	# 6. Test WebSocket through SOCKS5
	try:
		import websockets
		ws_url = f"ws://{MAC_SERVER_IP}:{MAC_SERVER_PORT}/"
		async with websockets.connect(ws_url, proxy=SOCKS5_PROXY, ping_interval=None, close_timeout=5) as ws:
			logger.info("✅ WebSocket via SOCKS5 successful")
	except Exception as e:
		logger.error("❌ WebSocket via SOCKS5 failed: %s (%s)", type(e).__name__, e)


def include_router(app):
      app.include_router(general_router)
      app.include_router(education_router)
      app.include_router(hobby_router)
      app.include_router(other_router)
      app.include_router(project_router)
      app.include_router(auth_router)
      app.include_router(dev_router)
      app.include_router(speckit_router)
      # Include API proxy for Cloud Run (conditional)
      if HAS_API_PROXY:
          app.include_router(api_proxy_router)
      # Include AgentBridge router for local/Ubuntu (conditional)
      if HAS_AGENTBRIDGE:
          app.include_router(agentbridge_router)

 
from pathlib import Path

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

	app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
	include_router(app)
	configure_static(app)

	# Start background tasks
	@app.on_event("startup")
	async def startup_event():
		from services.session_manager import cleanup_idle_sessions
		from services.tailscale_health_monitor import start_health_monitor

		# Run startup diagnostics if in Cloud Run
		if settings.K_SERVICE is not None:
			logger.info("=" * 60)
			logger.info("CLOUD RUN STARTUP DIAGNOSTICS")
			logger.info("=" * 60)
			await run_startup_diagnostics()
			logger.info("=" * 60)

		# Start session cleanup
		asyncio.create_task(cleanup_idle_sessions(idle_timeout=3600))
		logger.info("Session cleanup task started (1 hour idle timeout)")

		# Start Tailscale health monitor (only in Cloud Run)
		asyncio.create_task(start_health_monitor())
		logger.info("Tailscale health monitor started")

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
            ws_ping_interval=30,       # Keep frequent pings for connection health
            ws_ping_timeout=86400      # Allow very long idle sessions
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
            logger.warning("Browser will show security warning for self-signed certificate - this is expected")

            uvicorn.run(
                app,
                host=host,
                port=port,
                ssl_keyfile=str(ssl_key_path),
                ssl_certfile=str(ssl_cert_path)
            )
        else:
            # HTTP fallback
            port = 8080
            logger.info("Local development - HTTP mode (no SSL certificates found)")
            logger.info(f"Access via: http://localhost:{port}/dev")
            logger.warning("To enable HTTPS, generate certificates with:")
            logger.info("    openssl req -x509 -newkey rsa:2048 -nodes -keyout ~/.ssl/key.pem -out ~/.ssl/cert.pem -days 365")

            uvicorn.run(app, host=host, port=port)
