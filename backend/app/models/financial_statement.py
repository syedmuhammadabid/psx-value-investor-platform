"""Financial statement model — one reporting period per row.

A single wide row captures the headline line items of all three statements
(income statement, balance sheet, cash flow) for a company for a given period.
This structure keeps period-over-period queries simple and feeds the ratio
engine (Phase 5) directly.
"""

from __future__ import annotations

import enum
import uuid
from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import (
    Date,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy import (
    Enum as SAEnum,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company

# Monetary line items are large (PKR), stored with two decimals.
_Money = Numeric(24, 2)


class PeriodType(enum.StrEnum):
    """Reporting cadence of a financial statement."""

    ANNUAL = "annual"
    QUARTERLY = "quarterly"


class FinancialStatement(UUIDMixin, TimestampMixin, Base):
    """Headline financials for one company for one reporting period."""

    __tablename__ = "financial_statements"
    __table_args__ = (
        UniqueConstraint(
            "company_id",
            "period_type",
            "fiscal_year",
            "fiscal_period",
            name="uq_financials_company_period",
        ),
    )

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    period_type: Mapped[PeriodType] = mapped_column(
        SAEnum(
            PeriodType,
            name="period_type",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        index=True,
    )
    fiscal_year: Mapped[int] = mapped_column(Integer, index=True)
    # "FY" for annual; "Q1".."Q4" for quarterly.
    fiscal_period: Mapped[str] = mapped_column(String(8))
    period_end: Mapped[date] = mapped_column(Date, index=True)
    currency: Mapped[str] = mapped_column(String(3), default="PKR")

    # --- Income statement ---
    revenue: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    cost_of_revenue: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    gross_profit: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    operating_expenses: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    operating_income: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    interest_expense: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    pretax_income: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    tax_expense: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    net_income: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    eps_basic: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    shares_outstanding: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)

    # --- Balance sheet ---
    cash_and_equivalents: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    inventory: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    current_assets: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    total_assets: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    current_liabilities: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    total_debt: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    total_liabilities: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    total_equity: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)

    # --- Cash flow ---
    operating_cash_flow: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    capital_expenditure: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    investing_cash_flow: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    financing_cash_flow: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)
    dividends_paid: Mapped[Decimal | None] = mapped_column(_Money, nullable=True)

    company: Mapped[Company] = relationship(back_populates="financials")
