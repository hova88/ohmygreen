from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from backend.app.api.schemas import PostCreate, PostRead
from backend.app.db.session import get_db
from backend.app.services.post_service import PostService

router = APIRouter(prefix="/api/v1", tags=["posts"])


@router.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/posts", response_model=list[PostRead])
def list_posts(db: Session = Depends(get_db)) -> list[PostRead]:
    return PostService(db).list_posts()


@router.post("/posts", response_model=PostRead, status_code=status.HTTP_201_CREATED)
def create_post(payload: PostCreate, db: Session = Depends(get_db)) -> PostRead:
    return PostService(db).create_post(payload)
