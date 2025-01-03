from fastapi import FastAPI
from core.config import settings
from fastapi.staticfiles import StaticFiles
from apis.general_pages.route_homepage import general_pages_router


def include_router(app):
	app.include_router(general_pages_router)
 
def configure_static(app):
    app.mount("/static", StaticFiles(directory="static"), name="static")

def start_application():
	app = FastAPI(title=settings.PROJECT_NAME,version=settings.PROJECT_VERSION)
	include_router(app)
	configure_static(app)
	return app 


app = start_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)