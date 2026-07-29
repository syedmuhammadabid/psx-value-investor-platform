"""Data-access layer for persisted portfolio positions."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.portfolio_position import PortfolioPosition


def list_for_user(db: Session, user_id: uuid.UUID) -> list[PortfolioPosition]:
    """Return a user's positions, newest first."""
    stmt = (
        select(PortfolioPosition)
        .where(PortfolioPosition.user_id == user_id)
        .order_by(PortfolioPosition.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get(db: Session, user_id: uuid.UUID, symbol: str) -> PortfolioPosition | None:
    """Fetch a single position for a user by symbol (case-insensitive)."""
    stmt = select(PortfolioPosition).where(
        PortfolioPosition.user_id == user_id,
        func.upper(PortfolioPosition.symbol) == symbol.upper(),
    )
    return db.execute(stmt).scalars().one_or_none()


def upsert(
    db: Session,
    user_id: uuid.UUID,
    *,
    symbol: str,
    quantity: Decimal,
    average_cost: Decimal,
) -> PortfolioPosition:
    """Create a position or update an existing one for the same symbol."""
    position = get(db, user_id, symbol)
    if position is None:
        position = PortfolioPosition(
            user_id=user_id,
            symbol=symbol.upper(),
            quantity=quantity,
            average_cost=average_cost,
        )
        db.add(position)
    else:
        position.quantity = quantity
        position.average_cost = average_cost
    db.flush()
    return position


def delete(db: Session, position: PortfolioPosition) -> None:
    """Remove a position."""
    db.delete(position)
    db.flush()
