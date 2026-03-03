from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_username(self, username: str) -> User | None:
        return self.db.scalar(select(User).where(User.username == username))

    def get_by_api_token(self, token: str) -> User | None:
        return self.db.scalar(select(User).where(User.api_token == token))

    def create(self, username: str, password_hash: str, api_token: str) -> User:
        user = User(username=username, password_hash=password_hash, api_token=api_token)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user
