from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .database import Base, SessionLocal, engine
from .models import Post, User
from .schemas import AuthResponse, LoginPayload, PostCreate, PostOut
from .security import hash_password, new_api_token, verify_password

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OhMyGreen - AI + Bearblog + CLI")
app.add_middleware(SessionMiddleware, secret_key="ohmygreen-dev-secret-change-me", same_site="lax")

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def require_user(request: Request, db: Session) -> User:
    user_id = request.session.get("user_id")
    if not user_id:
        raise HTTPException(status_code=401, detail="not authenticated")
    user = db.get(User, user_id)
    if user is None:
        request.session.clear()
        raise HTTPException(status_code=401, detail="session invalid")
    return user


def bearer_token(request: Request) -> str:
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="missing bearer token")
    return auth.removeprefix("Bearer ").strip()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db)):
    user_id = request.session.get("user_id")
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})

    user = db.get(User, user_id)
    if not user:
        request.session.clear()
        return templates.TemplateResponse("login.html", {"request": request, "error": "Session expired."})

    posts = db.scalars(select(Post).where(Post.owner_id == user.id).order_by(Post.created_at.desc())).all()
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "posts": posts})


@app.post("/session")
def login_or_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db),
):
    username = username.strip().lower()
    if len(username) < 2 or len(password) < 6:
        raise HTTPException(status_code=400, detail="username/password invalid")

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        user = User(username=username, password_hash=hash_password(password), api_token=new_api_token())
        db.add(user)
        db.commit()
        db.refresh(user)
    elif not verify_password(password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")

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
    user = require_user(request, db)
    post = Post(owner_id=user.id, title=title.strip(), content=content.strip())
    db.add(post)
    db.commit()
    return RedirectResponse(url="/", status_code=303)


@app.post("/api/auth/login", response_model=AuthResponse)
def api_login(payload: LoginPayload, db: Session = Depends(get_db)):
    username = payload.username.strip().lower()
    user = db.scalar(select(User).where(User.username == username))
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="invalid credentials")
    return AuthResponse(username=user.username, token=user.api_token)


@app.get("/api/posts", response_model=list[PostOut])
def api_list_posts(request: Request, db: Session = Depends(get_db)):
    token = bearer_token(request)
    user = db.scalar(select(User).where(User.api_token == token))
    if user is None:
        raise HTTPException(status_code=401, detail="invalid token")
    posts = db.scalars(select(Post).where(Post.owner_id == user.id).order_by(Post.created_at.desc())).all()
    return posts


@app.post("/api/posts", response_model=PostOut)
def api_create_post(payload: PostCreate, request: Request, db: Session = Depends(get_db)):
    token = bearer_token(request)
    user = db.scalar(select(User).where(User.api_token == token))
    if user is None:
        raise HTTPException(status_code=401, detail="invalid token")

    post = Post(owner_id=user.id, title=payload.title.strip(), content=payload.content.strip())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post
