import hashlib
import hmac
import secrets


def hash_password(password: str, salt: str | None = None) -> str:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 120_000)
    return f"{salt}${digest.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    try:
        salt, old_digest = hashed.split("$", 1)
    except ValueError:
        return False
    fresh = hash_password(password, salt).split("$", 1)[1]
    return hmac.compare_digest(fresh, old_digest)


def new_api_token() -> str:
    return secrets.token_urlsafe(32)
