"""Authentication endpoints — register, login, and current-user."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.schemas.auth import Token, UserCreate, UserLogin, UserOut
from app.services import auth as service

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Annotated[Session, Depends(get_db)]) -> Token:
    """Create an account and return an access token."""
    user = service.register(db, payload)
    db.commit()
    db.refresh(user)
    return service.issue_token(user)


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Annotated[Session, Depends(get_db)]) -> Token:
    """Verify credentials and return an access token."""
    user = service.authenticate(db, payload)
    return service.issue_token(user)


@router.get("/me", response_model=UserOut)
def me(current_user: CurrentUser) -> UserOut:
    """Return the authenticated user's profile."""
    return UserOut.model_validate(current_user)
