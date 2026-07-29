"""Per-user persisted portfolio positions."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class PortfolioPosition(UUIDMixin, TimestampMixin, Base):
    """A holding a user owns (one row per symbol; updates are upserts)."""

    __tablename__ = "portfolio_positions"
    __table_args__ = (UniqueConstraint("user_id", "symbol", name="uq_portfolio_user_symbol"),)

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    symbol: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
    average_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), nullable=False)
