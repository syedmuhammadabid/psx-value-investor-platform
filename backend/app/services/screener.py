"""Stock screener service — filters companies by value-investing rules.

Reuses the ratio engine so screener metrics stay consistent with the ratios
shown on each company page. Filters are optional and combined with AND: a
company must satisfy every supplied rule, and a company missing a required
metric is excluded (we never assume a passing value).
"""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.repositories import company as company_repo
from app.schemas.screener import ScreenerResult, ScreenerRow
from app.services import ratios as ratios_service

# Upper bound on companies scanned per screen (the MVP universe is ~100).
_MAX_UNIVERSE = 500


def _fails_min(threshold: float | None, value: float | None) -> bool:
    """A minimum rule fails when the metric is missing or below the threshold."""
    return threshold is not None and (value is None or value < threshold)


def _fails_max(threshold: float | None, value: float | None) -> bool:
    """A maximum rule fails when the metric is missing or above the threshold."""
    return threshold is not None and (value is None or value > threshold)


def run_screener(
    db: Session,
    *,
    min_roe: float | None = None,
    min_roic: float | None = None,
    max_pe: float | None = None,
    min_dividend_yield: float | None = None,
    max_debt_to_equity: float | None = None,
    min_revenue_growth: float | None = None,
    positive_fcf: bool = False,
    sector: str | None = None,
    limit: int = 50,
) -> ScreenerResult:
    # Ordered by market cap (largest first); preserve that order in results.
    companies, _ = company_repo.list_companies(db, limit=_MAX_UNIVERSE, offset=0, sector=sector)

    rows: list[ScreenerRow] = []
    for company in companies:
        ratios = ratios_service.get_ratios(db, company.symbol)
        roe = ratios.profitability.roe
        roic = ratios.profitability.roic
        pe = ratios.valuation.pe
        dividend_yield = ratios.valuation.dividend_yield
        debt_to_equity = ratios.debt.debt_to_equity
        revenue_growth = ratios.growth.revenue_cagr
        free_cash_flow = ratios.cash_flow.free_cash_flow

        if _fails_min(min_roe, roe):
            continue
        if _fails_min(min_roic, roic):
            continue
        if _fails_max(max_pe, pe):
            continue
        if _fails_min(min_dividend_yield, dividend_yield):
            continue
        if _fails_max(max_debt_to_equity, debt_to_equity):
            continue
        if _fails_min(min_revenue_growth, revenue_growth):
            continue
        if positive_fcf and (free_cash_flow is None or free_cash_flow <= 0):
            continue

        rows.append(
            ScreenerRow(
                symbol=company.symbol,
                name=company.name,
                sector=company.sector.name if company.sector else None,
                market_cap=company.market_cap,
                current_price=company.current_price,
                roe=roe,
                roic=roic,
                pe=pe,
                dividend_yield=dividend_yield,
                debt_to_equity=debt_to_equity,
                revenue_growth=revenue_growth,
                free_cash_flow=free_cash_flow,
            )
        )

    return ScreenerResult(count=len(rows), items=rows[:limit])
