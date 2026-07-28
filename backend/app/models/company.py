"""Company model — the core entity of the platform."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.financial_statement import FinancialStatement
    from app.models.sector import Sector


class Company(UUIDMixin, TimestampMixin, Base):
    """A PSX-listed company and its headline profile data."""

    __tablename__ = "companies"

    # Natural key used throughout the public API (e.g. "ENGRO").
    symbol: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255), index=True)

    sector_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("sectors.id", ondelete="SET NULL"), index=True, nullable=True
    )
    industry: Mapped[str | None] = mapped_column(String(160), nullable=True, index=True)

    # Headline market data (PKR).
    market_cap: Mapped[Decimal | None] = mapped_column(Numeric(24, 2), nullable=True)
    current_price: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    fifty_two_week_high: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    fifty_two_week_low: Mapped[Decimal | None] = mapped_column(Numeric(20, 4), nullable=True)
    dividend_yield: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)

    # Profile.
    website: Mapped[str | None] = mapped_column(String(255), nullable=True)
    fiscal_year_end: Mapped[str | None] = mapped_column(String(40), nullable=True)
    listing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    is_active: Mapped[bool] = mapped_column(
        default=True, server_default=text("true"), nullable=False
    )

    sector: Mapped[Sector | None] = relationship(back_populates="companies", lazy="joined")
    financials: Mapped[list[FinancialStatement]] = relationship(
        back_populates="company",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
