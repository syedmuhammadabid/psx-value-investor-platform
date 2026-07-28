"""Financials service — resolves a company then maps its statements."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.financial_statement import PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as repo
from app.schemas.financials import FinancialPeriod, FinancialStatements


def get_financials(
    db: Session,
    symbol: str,
    *,
    period_type: PeriodType,
    limit: int = 10,
) -> FinancialStatements:
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    statements = repo.list_financials(db, company.id, period_type=period_type, limit=limit)
    return FinancialStatements(
        symbol=company.symbol,
        period_type=period_type,
        periods=[FinancialPeriod.from_model(s) for s in statements],
    )
