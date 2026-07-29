"""Password hashing and JWT helpers (self-contained, no external auth service).

Passwords are hashed with bcrypt; access tokens are signed JWTs (HS256) using the
application ``secret_key``. Kept dependency-light and framework-agnostic so it can
be unit-tested in isolation.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import bcrypt
import jwt

from app.core.config import settings


class TokenError(Exception):
    """Raised when a JWT is missing, malformed, or expired."""


def hash_password(password: str) -> str:
    """Return a bcrypt hash of ``password``."""
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    """Return ``True`` if ``password`` matches the stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode(), password_hash.encode())
    except ValueError:
        return False


def create_access_token(subject: str, *, expires_delta: timedelta | None = None) -> str:
    """Issue a signed JWT whose subject is the user id."""
    expire = datetime.now(UTC) + (
        expires_delta or timedelta(minutes=settings.access_token_expire_minutes)
    )
    payload = {"sub": subject, "exp": expire, "iat": datetime.now(UTC)}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def decode_access_token(token: str) -> str:
    """Return the subject (user id) of a valid JWT, or raise :class:`TokenError`."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
    except jwt.PyJWTError as exc:
        raise TokenError("Invalid or expired token.") from exc
    subject = payload.get("sub")
    if not isinstance(subject, str):
        raise TokenError("Token is missing a subject.")
    return subject
