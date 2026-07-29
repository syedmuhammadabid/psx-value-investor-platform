"""Alert subscription service — user-scoped, enriched with live signals."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.alert_subscription import AlertSubscription
from app.models.user import User
from app.repositories import alert_subscription as subscription_repo
from app.repositories import company as company_repo
from app.schemas.alert_subscription import AlertSubscriptionCreate, AlertSubscriptionOut
from app.services import alerts as alerts_service


def _to_out(db: Session, subscription: AlertSubscription) -> AlertSubscriptionOut:
    """Build a subscription enriched with the company's active alert signals."""
    company = company_repo.get_by_symbol(db, subscription.symbol)
    report = alerts_service.get_alerts(db, subscription.symbol)
    return AlertSubscriptionOut(
        symbol=subscription.symbol,
        name=company.name if company is not None else None,
        subscribed_at=subscription.created_at,
        alerts=report.alerts,
    )


def list_subscriptions(db: Session, user: User) -> list[AlertSubscriptionOut]:
    """Return the user's enriched alert subscriptions."""
    return [_to_out(db, sub) for sub in subscription_repo.list_for_user(db, user.id)]


def subscribe(db: Session, user: User, payload: AlertSubscriptionCreate) -> AlertSubscriptionOut:
    """Subscribe to a company's alerts (404 if unknown, 409 if duplicate)."""
    company = company_repo.get_by_symbol(db, payload.symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{payload.symbol}' not found.",
        )
    if subscription_repo.get(db, user.id, company.symbol) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"You are already subscribed to '{company.symbol}'.",
        )
    subscription = subscription_repo.add(db, user.id, company.symbol)
    db.commit()
    db.refresh(subscription)
    return _to_out(db, subscription)


def unsubscribe(db: Session, user: User, symbol: str) -> None:
    """Remove a subscription (404 if not present)."""
    subscription = subscription_repo.get(db, user.id, symbol)
    if subscription is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"You are not subscribed to '{symbol}'.",
        )
    subscription_repo.delete(db, subscription)
    db.commit()
