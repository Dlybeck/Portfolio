from fastapi import FastAPI
from core.config import settings
from fastapi.staticfiles import StaticFiles
from apis.route_general import general_router
from apis.route_education import education_router
from apis.route_hobbies import hobby_router
from apis.route_other import other_router
from apis.route_projects import project_router
from apis.route_auth import auth_router
from apis.route_dev import dev_router
from core.security import validate_security_config
import asyncio


def include_router(app):
      app.include_router(general_router)
      app.include_router(education_router)
      app.include_router(hobby_router)
      app.include_router(other_router)
      app.include_router(project_router)
      app.include_router(auth_router)
      app.include_router(dev_router)

 
def configure_static(app):
    app.mount("/static", StaticFiles(directory="static"), name="static")

def start_application():
	# Validate security configuration on startup
	try:
		validate_security_config()
	except ValueError as e:
		print(f"❌ Security configuration error: {e}")
		print("Run setup_security.py to configure authentication")
		print("🛑 Server startup aborted due to security configuration errors")
		import sys
		sys.exit(1)

	app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
	include_router(app)
	configure_static(app)

	# Start session cleanup task
	@app.on_event("startup")
	async def startup_event():
		from services.session_manager import cleanup_idle_sessions
		asyncio.create_task(cleanup_idle_sessions(idle_timeout=3600))
		print("✅ Session cleanup task started (1 hour idle timeout)")

	return app 


app = start_application()

if __name__ == "__main__":
    import uvicorn
    import subprocess
    import os

    # Determine if running in Cloud Run
    is_cloud_run = os.environ.get("K_SERVICE") is not None

    if is_cloud_run:
        # In Cloud Run, bind to all interfaces
        print("🌐 Running in Cloud Run - binding to 0.0.0.0:8080")
        host = "0.0.0.0"
    else:
        # Local development - bind to all interfaces for local network testing
        print("🌐 Local development - binding to 0.0.0.0:8080")
        print("📱 Access from phone via: http://<your-mac-ip>:8080/dev")
        host = "0.0.0.0"

    uvicorn.run(app, host=host, port=8080)
