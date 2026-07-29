"""Data-access layer for alert subscriptions."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.alert_subscription import AlertSubscription


def list_for_user(db: Session, user_id: uuid.UUID) -> list[AlertSubscription]:
    """Return a user's subscriptions, newest first."""
    stmt = (
        select(AlertSubscription)
        .where(AlertSubscription.user_id == user_id)
        .order_by(AlertSubscription.created_at.desc())
    )
    return list(db.execute(stmt).scalars().all())


def get(db: Session, user_id: uuid.UUID, symbol: str) -> AlertSubscription | None:
    """Fetch a single subscription for a user by symbol (case-insensitive)."""
    stmt = select(AlertSubscription).where(
        AlertSubscription.user_id == user_id,
        func.upper(AlertSubscription.symbol) == symbol.upper(),
    )
    return db.execute(stmt).scalars().one_or_none()


def add(db: Session, user_id: uuid.UUID, symbol: str) -> AlertSubscription:
    """Create a subscription."""
    subscription = AlertSubscription(user_id=user_id, symbol=symbol.upper())
    db.add(subscription)
    db.flush()
    return subscription


def delete(db: Session, subscription: AlertSubscription) -> None:
    """Remove a subscription."""
    db.delete(subscription)
    db.flush()
