from sqlalchemy import select
from sqlalchemy.orm import Session

from backend.app.api.schemas import PostCreate
from backend.app.domain.models import Post


class PostService:
    def __init__(self, db: Session):
        self.db = db

    def list_posts(self) -> list[Post]:
        return list(self.db.scalars(select(Post).order_by(Post.created_at.desc())))

    def create_post(self, payload: PostCreate) -> Post:
        post = Post(title=payload.title.strip(), body=payload.body.strip())
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post
