"""History service — builds chart-ready annual metric series.

Reuses the pure ratio calculations so trend metrics stay consistent with the
ratio engine. Per-share figures (EPS is stored directly; BVPS and DPS are
derived) let the frontend chart long-term trends.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.calculations import ratios as calc
from app.models.financial_statement import FinancialStatement, PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.schemas.history import CompanyHistory, MetricPoint

# How many annual periods to chart.
_HISTORY_WINDOW = 10


def _f(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _pct(fraction: float | None) -> float | None:
    return fraction * 100.0 if fraction is not None else None


def get_history(db: Session, symbol: str, *, limit: int = _HISTORY_WINDOW) -> CompanyHistory:
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    annual = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.ANNUAL, limit=limit
    )
    # Charts read left-to-right in time, so return oldest period first.
    points = [_point(s) for s in reversed(annual)]
    return CompanyHistory(symbol=company.symbol, points=points)


def _point(s: FinancialStatement) -> MetricPoint:
    shares = _f(s.shares_outstanding)
    dividends = _f(s.dividends_paid)
    # Dividends paid are stored as a negative outflow; per share uses magnitude.
    dividend_total = abs(dividends) if dividends is not None else None
    return MetricPoint(
        fiscal_year=s.fiscal_year,
        period_end=s.period_end,
        revenue=_f(s.revenue),
        net_income=_f(s.net_income),
        eps=_f(s.eps_basic),
        roe=_pct(calc.return_on_equity(_f(s.net_income), _f(s.total_equity))),
        roic=_pct(
            calc.return_on_invested_capital(
                _f(s.operating_income),
                _f(s.tax_expense),
                _f(s.pretax_income),
                _f(s.total_debt),
                _f(s.total_equity),
                _f(s.cash_and_equivalents),
            )
        ),
        dividend_per_share=calc.safe_div(dividend_total, shares),
        book_value_per_share=calc.safe_div(_f(s.total_equity), shares),
        free_cash_flow=calc.free_cash_flow(_f(s.operating_cash_flow), _f(s.capital_expenditure)),
    )
