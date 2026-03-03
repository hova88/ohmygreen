from app.domain import (
    InvalidCredentialsError,
    InvalidInputError,
    InvalidSessionError,
    NotAuthenticatedError,
)
from app.infra.repositories import UserRepository
from app.models import User
from app.security import hash_password, new_api_token, verify_password


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    def login_or_register(self, username: str, password: str) -> User:
        normalized_username = username.strip().lower()
        normalized_password = password.strip()

        if len(normalized_username) < 2 or len(normalized_password) < 6:
            raise InvalidInputError("Username/password is invalid")

        user = self.user_repo.get_by_username(normalized_username)
        if user is None:
            return self.user_repo.create(
                username=normalized_username,
                password_hash=hash_password(normalized_password),
                api_token=new_api_token(),
            )

        if not verify_password(normalized_password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")
        return user

    def login_api(self, username: str, password: str) -> User:
        normalized_username = username.strip().lower()
        normalized_password = password.strip()

        user = self.user_repo.get_by_username(normalized_username)
        if user is None or not verify_password(normalized_password, user.password_hash):
            raise InvalidCredentialsError("Invalid credentials")
        return user

    def get_user_from_session(self, user_id: int | None) -> User:
        if not user_id:
            raise NotAuthenticatedError("Not authenticated")

        user = self.user_repo.get_by_id(user_id)
        if user is None:
            raise InvalidSessionError("Session invalid")
        return user

    def get_user_from_bearer(self, authorization: str | None) -> User:
        authorization = authorization or ""
        if not authorization.startswith("Bearer "):
            raise NotAuthenticatedError("Missing bearer token")

        token = authorization.removeprefix("Bearer ").strip()
        user = self.user_repo.get_by_api_token(token)
        if user is None:
            raise NotAuthenticatedError("Invalid token")
        return user
