from datetime import UTC, datetime, timedelta

import jwt
from pwdlib import PasswordHash

from app.config import settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def create_access_token(subject: str) -> str:
    secret_key = settings.jwt_secret_key
    if len(secret_key.encode("utf-8")) < 32:
        raise RuntimeError("JWT_SECRET_KEY doit contenir au moins 32 octets.")
    if settings.access_token_expire_minutes <= 0:
        raise RuntimeError("ACCESS_TOKEN_EXPIRE_MINUTES doit être supérieur à zéro.")

    issued_at = datetime.now(UTC)
    expires_at = issued_at + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "iat": issued_at, "exp": expires_at},
        secret_key,
        algorithm=settings.jwt_algorithm,
    )
