from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Post


class PostRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_by_owner(self, owner_id: int) -> list[Post]:
        return self.db.scalars(
            select(Post).where(Post.owner_id == owner_id).order_by(Post.created_at.desc())
        ).all()

    def create(self, owner_id: int, title: str, content: str) -> Post:
        post = Post(owner_id=owner_id, title=title, content=content)
        self.db.add(post)
        self.db.commit()
        self.db.refresh(post)
        return post
