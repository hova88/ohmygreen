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

from .database import SessionLocal
from .models import Post, User
from .schemas import AuthResponse, LoginPayload, PostCreate, PostOut
from .security import hash_password, new_api_token, verify_password

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
    secret_key=os.getenv("OHMYGREEN_SESSION_SECRET", "dev-secret-change-in-production"),
    same_site="lax",
    https_only=False,
)

BASE_DIR = Path(__file__).resolve().parent.parent
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

    posts = db.scalars(select(Post).where(Post.owner_id == user.id).order_by(Post.created_at.desc())).all()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "posts": posts})


@app.post("/session")
def login_or_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    normalized_username = username.strip().lower()
    normalized_password = password.strip()
    if len(normalized_username) < 2 or len(normalized_password) < 6:
        raise HTTPException(status_code=400, detail="Username/password is invalid")

    user = db.scalar(select(User).where(User.username == normalized_username))
    if user is None:
        user = User(
            username=normalized_username,
            password_hash=hash_password(normalized_password),
            api_token=new_api_token(),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not verify_password(normalized_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@app.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@app.post("/posts")
def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    user = current_user_from_session(request, db)

    post = Post(owner_id=user.id, title=title.strip(), content=content.strip())
    db.add(post)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/auth/login", response_model=AuthResponse)
def api_login(payload: LoginPayload, db: Session = Depends(get_db)):
    normalized_username = payload.username.strip().lower()
    normalized_password = payload.password.strip()

    user = db.scalar(select(User).where(User.username == normalized_username))
    if user is None or not verify_password(normalized_password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    return AuthResponse(username=user.username, token=user.api_token)


@app.get("/api/posts", response_model=list[PostOut])
def api_list_posts(request: Request, db: Session = Depends(get_db)):
    user = current_user_from_bearer(request, db)
    posts = db.scalars(select(Post).where(Post.owner_id == user.id).order_by(Post.created_at.desc())).all()
    return posts


@app.post("/api/posts", response_model=PostOut)
def api_create_post(payload: PostCreate, request: Request, db: Session = Depends(get_db)):
    user = current_user_from_bearer(request, db)

    post = Post(owner_id=user.id, title=payload.title.strip(), content=payload.content.strip())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post
