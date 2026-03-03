import os
from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware

from .api.deps import bearer_auth, get_db, session_auth
from .api.errors import register_error_handlers
from .database import Base, engine
from .models import Post, User
from .schemas import AuthResponse, LoginPayload, PostCreate, PostOut
from .security import hash_password, new_api_token, verify_password

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OhMyGreen")
app.add_middleware(
    SessionMiddleware,
    secret_key=os.getenv("OHMYGREEN_SESSION_SECRET", "dev-secret-change-in-production"),
    same_site="lax",
    https_only=False,
)

BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

register_error_handlers(app)


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
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
    user: User = Depends(session_auth),
):
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
def api_list_posts(db: Session = Depends(get_db), user: User = Depends(bearer_auth)):
    posts = db.scalars(select(Post).where(Post.owner_id == user.id).order_by(Post.created_at.desc())).all()
    return posts


@app.post("/api/posts", response_model=PostOut)
def api_create_post(payload: PostCreate, db: Session = Depends(get_db), user: User = Depends(bearer_auth)):
    post = Post(owner_id=user.id, title=payload.title.strip(), content=payload.content.strip())
    db.add(post)
    db.commit()
    db.refresh(post)
    return post
