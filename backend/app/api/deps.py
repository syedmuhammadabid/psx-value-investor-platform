"""Shared FastAPI dependencies for authentication."""

from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import TokenError, decode_access_token
from app.models.user import User
from app.repositories import user as user_repo

_bearer = HTTPBearer(auto_error=False)

_CREDENTIALS_EXCEPTION = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_bearer)],
) -> User:
    """Resolve the authenticated user from a bearer token (401 if invalid)."""
    if credentials is None:
        raise _CREDENTIALS_EXCEPTION
    try:
        subject = decode_access_token(credentials.credentials)
        user_id = uuid.UUID(subject)
    except (TokenError, ValueError) as exc:
        raise _CREDENTIALS_EXCEPTION from exc

    user = user_repo.get_by_id(db, user_id)
    if user is None or not user.is_active:
        raise _CREDENTIALS_EXCEPTION
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
