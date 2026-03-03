from dataclasses import dataclass

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import User


@dataclass(slots=True)
class AuthContext:
    request: Request
    scheme: str


class DomainError(Exception):
    code = "domain_error"
    message = "Domain error"
    status_code = 400

    def __init__(self, message: str | None = None):
        self.message = message or self.message
        super().__init__(self.message)


class AuthError(DomainError):
    code = "auth_error"
    message = "Authentication failed"
    status_code = 401


class MissingCredentialsError(AuthError):
    code = "missing_credentials"
    message = "Missing credentials"


class InvalidCredentialsError(AuthError):
    code = "invalid_credentials"
    message = "Invalid credentials"


class InvalidSessionError(AuthError):
    code = "invalid_session"
    message = "Session invalid"


def get_current_user(context: AuthContext, db: Session) -> User:
    if context.scheme == "session":
        user_id = context.request.session.get("user_id")
        if not user_id:
            raise MissingCredentialsError("Not authenticated")

        user = db.get(User, user_id)
        if user is None:
            context.request.session.clear()
            raise InvalidSessionError()
        return user

    if context.scheme == "bearer":
        authorization = context.request.headers.get("Authorization", "")
        if not authorization.startswith("Bearer "):
            raise MissingCredentialsError("Missing bearer token")

        token = authorization.removeprefix("Bearer ").strip()
        user = db.scalar(select(User).where(User.api_token == token))
        if user is None:
            raise InvalidCredentialsError("Invalid token")
        return user

    raise AuthError("Unsupported auth scheme")
