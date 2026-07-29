"""Data-access layer for financial statements."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.financial_statement import FinancialStatement, PeriodType


def list_financials(
    db: Session,
    company_id: uuid.UUID,
    *,
    period_type: PeriodType,
    limit: int = 10,
) -> list[FinancialStatement]:
    """Return a company's statements for a cadence, newest period first."""
    stmt = (
        select(FinancialStatement)
        .where(
            FinancialStatement.company_id == company_id,
            FinancialStatement.period_type == period_type,
        )
        .order_by(FinancialStatement.period_end.desc())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().all())


def get_by_natural_key(
    db: Session,
    company_id: uuid.UUID,
    *,
    period_type: PeriodType,
    fiscal_year: int,
    fiscal_period: str,
) -> FinancialStatement | None:
    """Return a statement by its natural key, or ``None`` (for idempotent upsert)."""
    stmt = select(FinancialStatement).where(
        FinancialStatement.company_id == company_id,
        FinancialStatement.period_type == period_type,
        FinancialStatement.fiscal_year == fiscal_year,
        FinancialStatement.fiscal_period == fiscal_period,
    )
    return db.execute(stmt).scalar_one_or_none()
