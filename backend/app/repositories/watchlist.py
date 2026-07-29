"""Data-access layer for user watchlists."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.watchlist import WatchlistItem


def list_for_user(db: Session, user_id: uuid.UUID) -> list[WatchlistItem]:
    """Return a user's watchlist entries, newest first."""
    stmt = (
        select(WatchlistItem)
        .where(WatchlistItem.user_id == user_id)
        .order_by(WatchlistItem.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get(db: Session, user_id: uuid.UUID, symbol: str) -> WatchlistItem | None:
    """Fetch a single watchlist entry for a user by symbol (case-insensitive)."""
    stmt = select(WatchlistItem).where(
        WatchlistItem.user_id == user_id,
        func.upper(WatchlistItem.symbol) == symbol.upper(),
    )
    return db.execute(stmt).scalars().one_or_none()


def add(db: Session, user_id: uuid.UUID, symbol: str) -> WatchlistItem:
    """Create a watchlist entry."""
    item = WatchlistItem(user_id=user_id, symbol=symbol.upper())
    db.add(item)
    db.flush()
    return item


def delete(db: Session, item: WatchlistItem) -> None:
    """Remove a watchlist entry."""
    db.delete(item)
    db.flush()
