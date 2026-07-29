"""Per-user alert subscriptions (which companies a user wants signals for)."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class AlertSubscription(UUIDMixin, TimestampMixin, Base):
    """A user's subscription to alert signals for a company."""

    __tablename__ = "alert_subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_alert_sub_user_symbol"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
