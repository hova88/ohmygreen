from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import SessionLocal
from app.domain import InvalidSessionError, NotAuthenticatedError
from app.infra.repositories import PostRepository, UserRepository
from app.models import User
from app.services import AuthService, PostService


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(UserRepository(db))


def get_post_service(db: Session = Depends(get_db)) -> PostService:
    return PostService(PostRepository(db))


def get_current_user_from_session(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    user_id = request.session.get("user_id")
    try:
        return auth_service.get_user_from_session(user_id)
    except NotAuthenticatedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
    except InvalidSessionError as exc:
        request.session.clear()
        raise HTTPException(status_code=401, detail=str(exc)) from exc


def get_current_user_from_bearer(
    request: Request,
    auth_service: AuthService = Depends(get_auth_service),
) -> User:
    authorization = request.headers.get("Authorization")
    try:
        return auth_service.get_user_from_bearer(authorization)
    except NotAuthenticatedError as exc:
        raise HTTPException(status_code=401, detail=str(exc)) from exc
