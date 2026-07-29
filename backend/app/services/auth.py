"""Authentication service — registration and login."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User
from app.repositories import user as user_repo
from app.schemas.auth import Token, UserCreate, UserLogin


def register(db: Session, payload: UserCreate) -> User:
    """Create a new user (409 if the email is already registered)."""
    if user_repo.get_by_email(db, payload.email) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists.",
        )
    return user_repo.create(
        db,
        email=payload.email,
        password_hash=hash_password(payload.password),
        full_name=payload.full_name,
    )


def authenticate(db: Session, payload: UserLogin) -> User:
    """Verify credentials and return the user (401 on failure)."""
    user = user_repo.get_by_email(db, payload.email)
    if user is None or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password.",
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This account is inactive.",
        )
    return user


def issue_token(user: User) -> Token:
    """Mint an access token for a user."""
    return Token(access_token=create_access_token(str(user.id)))
