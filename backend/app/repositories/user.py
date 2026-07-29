"""Data-access layer for users."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.user import User


def get_by_email(db: Session, email: str) -> User | None:
    """Fetch a user by their (case-insensitive) email address."""
    stmt = select(User).where(func.lower(User.email) == email.lower())
    return db.execute(stmt).scalars().one_or_none()


def get_by_id(db: Session, user_id: uuid.UUID) -> User | None:
    """Fetch a user by primary key."""
    return db.get(User, user_id)


def create(db: Session, *, email: str, password_hash: str, full_name: str | None) -> User:
    """Persist a new user."""
    user = User(email=email, password_hash=password_hash, full_name=full_name, is_active=True)
    db.add(user)
    db.flush()
    return user
