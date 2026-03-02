from pathlib import Path

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .database import Base, SessionLocal, engine
from .models import Post, User

Base.metadata.create_all(bind=engine)

app = FastAPI(title="OhMyGreen - AI CLI Blog Demo")
BASE_DIR = Path(__file__).resolve().parent.parent
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get("/", response_class=HTMLResponse)
def home(request: Request, db: Session = Depends(get_db), user: str | None = None):
    if not user:
        return templates.TemplateResponse("login.html", {"request": request})

    account = db.scalar(select(User).where(User.username == user))
    posts = []
    if account:
        posts = db.scalars(select(Post).where(Post.owner_id == account.id).order_by(Post.created_at.desc())).all()

    return templates.TemplateResponse(
        "index.html",
        {
            "request": request,
            "user": user,
            "posts": posts,
        },
    )


@app.post("/session")
def set_session(username: str = Form(...), db: Session = Depends(get_db)):
    username = username.strip()
    if len(username) < 2:
        raise HTTPException(status_code=400, detail="username too short")

    account = db.scalar(select(User).where(User.username == username))
    if account is None:
        account = User(username=username)
        db.add(account)
        db.commit()

    return RedirectResponse(url=f"/?user={username}", status_code=303)


@app.post("/posts")
def create_post(
    user: str = Form(...),
    title: str = Form(...),
    content: str = Form(...),
    db: Session = Depends(get_db),
):
    account = db.scalar(select(User).where(User.username == user))
    if account is None:
        raise HTTPException(status_code=404, detail="user not found")

    post = Post(owner_id=account.id, title=title.strip(), content=content.strip())
    db.add(post)
    db.commit()

    return RedirectResponse(url=f"/?user={user}", status_code=303)
