from fastapi import APIRouter, Depends, HTTPException

from app.api.deps import get_auth_service, get_current_user_from_bearer, get_post_service
from app.domain import InvalidCredentialsError
from app.models import User
from app.schemas import AuthResponse, LoginPayload, PostCreate, PostOut
from app.services import AuthService, PostService

router = APIRouter(prefix="/api")


@router.post("/auth/login", response_model=AuthResponse)
def api_login(payload: LoginPayload, auth_service: AuthService = Depends(get_auth_service)):
    try:
        user = auth_service.login_api(payload.username, payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc

    return AuthResponse(username=user.username, token=user.api_token)


@router.get("/posts", response_model=list[PostOut])
def api_list_posts(
    current_user: User = Depends(get_current_user_from_bearer),
    post_service: PostService = Depends(get_post_service),
):
    return post_service.list_posts(current_user.id)


@router.post("/posts", response_model=PostOut)
def api_create_post(
    payload: PostCreate,
    current_user: User = Depends(get_current_user_from_bearer),
    post_service: PostService = Depends(get_post_service),
):
    return post_service.create_post(owner_id=current_user.id, title=payload.title, content=payload.content)
