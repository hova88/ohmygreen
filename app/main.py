from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.api.routes import api_router, configure_templates, web_router
from app.core import BASE_DIR, SESSION_SECRET
from app.database import Base, engine
import json
import logging
import os
import time
import uuid
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.sessions import SessionMiddleware

from .core.settings import get_settings
from .database import Base, SessionLocal, engine
from .database import SessionLocal
from .models import Post, User
from .schemas import AuthResponse, LoginPayload, PostCreate, PostOut
from .security import hash_password, new_api_token, verify_password

settings = get_settings()

Base.metadata.create_all(bind=engine)
logger = logging.getLogger("ohmygreen")
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(message)s"))
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False


class RequestContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id
        start = time.perf_counter()

        response = await call_next(request)

        duration_ms = int((time.perf_counter() - start) * 1000)
        response.headers["X-Request-ID"] = request_id
        logger.info(
            json.dumps(
                {
                    "event": "request",
                    "request_id": request_id,
                    "method": request.method,
                    "path": request.url.path,
                    "status_code": response.status_code,
                    "duration_ms": duration_ms,
                }
            )
        )
        return response


app = FastAPI(title="OhMyGreen")
app.add_middleware(RequestContextMiddleware)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret,
    same_site="lax",
    https_only=False,
)

app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def error_response(request: Request, status_code: int, error_code: str, message: str):
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
    logger.error(
        json.dumps(
            {
                "event": "error",
                "request_id": request_id,
                "error_code": error_code,
                "status_code": status_code,
                "path": request.url.path,
                "message": message,
            }
        )
    )
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "request_id": request_id,
                "error_code": error_code,
                "message": message,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    error_code = "HTTP_ERROR"
    if exc.status_code == 401:
        error_code = "AUTH_ERROR"
    elif exc.status_code == 404:
        error_code = "NOT_FOUND"
    elif exc.status_code == 400:
        error_code = "BAD_REQUEST"
    return error_response(request, exc.status_code, error_code, str(exc.detail))


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return error_response(request, 422, "VALIDATION_ERROR", "Request validation failed")


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    return error_response(request, 500, "INTERNAL_ERROR", "Internal server error")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def current_user_from_session(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="Not authenticated")

    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="Session invalid")
    return user


def current_user_from_bearer(request: Request, db: Session) -> User:
    authorization = request.headers.get("Authorization", "")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")

    token = authorization.removeprefix("Bearer ").strip()
    user = db.scalar(select(User).where(User.api_token == token))
    if user is None:
        raise HTTPException(status_code=401, detail="Invalid token")
    return user


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})

    user = db.get(User, user_id)
    if not user:
        request.session.clear()
        return templates.TemplateResponse("login.html", {"request": request, "error": "Your session expired."})

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
