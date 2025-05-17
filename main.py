from fastapi import FastAPI
from core.config import settings
from fastapi.staticfiles import StaticFiles
from apis.route_general import general_router
from apis.route_education import education_router
from apis.route_hobbies import hobby_router
from apis.route_other import other_router
from apis.route_projects import project_router


def include_router(app):
      app.include_router(general_router)
      app.include_router(education_router)
      app.include_router(hobby_router)
      app.include_router(other_router)
      app.include_router(project_router)

 
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
    uvicorn.run(app, host="localhost", port=8080)