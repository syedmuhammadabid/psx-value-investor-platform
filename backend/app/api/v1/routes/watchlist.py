"""Watchlist endpoints (authenticated, user-scoped)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.schemas.watchlist import WatchlistItemCreate, WatchlistItemOut
from app.services import watchlist as service

router = APIRouter(prefix="/watchlist", tags=["watchlist"])


@router.get("", response_model=list[WatchlistItemOut])
def list_watchlist(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[WatchlistItemOut]:
    """Return the current user's watchlist."""
    return service.list_watchlist(db, current_user)


@router.post("", response_model=WatchlistItemOut, status_code=status.HTTP_201_CREATED)
def add_to_watchlist(
    payload: WatchlistItemCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> WatchlistItemOut:
    """Add a company to the current user's watchlist."""
    return service.add_to_watchlist(db, current_user, payload)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def remove_from_watchlist(
    symbol: str, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> None:
    """Remove a company from the current user's watchlist."""
    service.remove_from_watchlist(db, current_user, symbol)
