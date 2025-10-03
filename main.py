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

	app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
	include_router(app)
	configure_static(app)
	return app 


app = start_application()

if __name__ == "__main__":
    import uvicorn
    import subprocess

    # Get Tailscale IP
    try:
        result = subprocess.run(["tailscale", "ip", "-4"], capture_output=True, text=True)
        tailscale_ip = result.stdout.strip()
        if tailscale_ip:
            print(f"✅ Binding to Tailscale interface: {tailscale_ip}:8080")
            print(f"🌐 Access via Cloud Run proxy only")
            host = tailscale_ip
        else:
            print("⚠️  Tailscale not detected, binding to localhost only")
            host = "127.0.0.1"
    except Exception as e:
        print(f"⚠️  Could not detect Tailscale ({e}), binding to localhost only")
        host = "127.0.0.1"

    uvicorn.run(app, host=host, port=8080)
