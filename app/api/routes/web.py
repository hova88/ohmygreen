from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from app.api.deps import get_auth_service, get_current_user_from_session, get_post_service
from app.domain import (
    InvalidCredentialsError,
    InvalidInputError,
    InvalidSessionError,
    NotAuthenticatedError,
)
from app.models import User
from app.services import AuthService, PostService

router = APIRouter()
templates: Jinja2Templates | None = None


def configure_templates(template_engine: Jinja2Templates) -> None:
    global templates
    templates = template_engine


@router.get("/", response_class=HTMLResponse)
def home(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
    post_service: PostService = Depends(get_post_service),
):
    assert templates is not None

    user_id = request.session.get("user_id")
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})

    try:
        user = auth_service.get_user_from_session(user_id)
    except (NotAuthenticatedError, InvalidSessionError):
        request.session.clear()
        return templates.TemplateResponse("login.html", {"request": request, "error": "Your session expired."})

    posts = post_service.list_posts(user.id)
    return templates.TemplateResponse("index.html", {"request": request, "user": user, "posts": posts})


@router.post("/session")
def login_or_register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    auth_service: AuthService = Depends(get_auth_service),
):
    try:
        user = auth_service.login_or_register(username=username, password=password)
    except InvalidInputError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    request.session["user_id"] = user.id
    return RedirectResponse(url="/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)


@router.post("/posts")
def create_post(
    request: Request,
    title: str = Form(...),
    content: str = Form(...),
    user: User = Depends(get_current_user_from_session),
    post_service: PostService = Depends(get_post_service),
):
    post_service.create_post(owner_id=user.id, title=title, content=content)
    return RedirectResponse(url="/", status_code=303)
