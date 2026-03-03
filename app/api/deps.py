from fastapi import Depends, Request
from sqlalchemy.orm import Session

from app.core.auth import AuthContext, get_current_user
from app.database import SessionLocal
from app.models import User


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def session_auth(request: Request, db: Session = Depends(get_db)) -> User:
    return get_current_user(AuthContext(request=request, scheme="session"), db)


def bearer_auth(request: Request, db: Session = Depends(get_db)) -> User:
    return get_current_user(AuthContext(request=request, scheme="bearer"), db)
