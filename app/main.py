from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import api_router, configure_templates, web_router
from app.core import BASE_DIR, SESSION_SECRET
from app.database import Base, engine

app = FastAPI(title="OhMyGreen")
app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
configure_templates(templates)

app.include_router(web_router)
app.include_router(api_router)


@app.on_event("startup")
def startup() -> None:
    Base.metadata.create_all(bind=engine)


@app.on_event("shutdown")
def shutdown() -> None:
    return None
