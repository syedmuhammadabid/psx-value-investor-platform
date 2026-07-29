"""Alert subscription endpoints (authenticated, user-scoped)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.schemas.alert_subscription import AlertSubscriptionCreate, AlertSubscriptionOut
from app.services import alert_subscription as service

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=list[AlertSubscriptionOut])
def list_subscriptions(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> list[AlertSubscriptionOut]:
    """Return the current user's alert subscriptions with live signals."""
    return service.list_subscriptions(db, current_user)


@router.post("", response_model=AlertSubscriptionOut, status_code=status.HTTP_201_CREATED)
def subscribe(
    payload: AlertSubscriptionCreate,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> AlertSubscriptionOut:
    """Subscribe the current user to a company's alert signals."""
    return service.subscribe(db, current_user, payload)


@router.delete("/{symbol}", status_code=status.HTTP_204_NO_CONTENT)
def unsubscribe(
    symbol: str, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> None:
    """Remove the current user's subscription to a company."""
    service.unsubscribe(db, current_user, symbol)
