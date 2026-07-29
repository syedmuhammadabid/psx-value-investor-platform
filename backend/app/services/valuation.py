"""Valuation service — blends multiple models into one intrinsic value.

Gathers per-company inputs (latest financials, market data, sector peers) and
feeds them into the pure valuation models, then combines the results using the
roadmap weights and derives a BUY / HOLD / SELL recommendation.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.calculations import ratios as calc
from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.schemas.valuation import (
    Recommendation,
    Valuation,
    ValuationAssumptions,
    ValuationModelResult,
)
from app.valuation import models

# Annual periods pulled for normalization/growth.
_WINDOW = 10
# Minimum annual periods required to compute a growth rate.
_MIN_GROWTH_PERIODS = 2
# Growth is capped so an outlier year can't inflate every model.
_MAX_GROWTH = 0.15


def _f(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _assumptions() -> ValuationAssumptions:
    return ValuationAssumptions(
        discount_rate=models.DEFAULT_DISCOUNT_RATE,
        terminal_growth=models.DEFAULT_TERMINAL_GROWTH,
        projection_years=models.DEFAULT_PROJECTION_YEARS,
    )


def _result(name: str, weight: float, value: float | None) -> ValuationModelResult:
    return ValuationModelResult(
        name=name,
        value=value,
        weight=weight,
        applied=value is not None and value > 0,
    )


def _empty(symbol: str, price: float | None) -> Valuation:
    """A neutral result when there is not enough data to value the company."""
    results = [
        ValuationModelResult(name=name, value=None, weight=weight, applied=False)
        for name, weight in models.MODEL_WEIGHTS.items()
    ]
    return Valuation(
        symbol=symbol,
        current_price=price,
        models=results,
        assumptions=_assumptions(),
    )


def get_valuation(db: Session, symbol: str) -> Valuation:
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    price = _f(company.current_price)
    annual = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.ANNUAL, limit=_WINDOW
    )
    if not annual:
        return _empty(company.symbol, price)

    values = _model_values(db, company, annual, price)
    components = [(values[name], weight) for name, weight in models.MODEL_WEIGHTS.items()]
    intrinsic = models.weighted_intrinsic_value(components)

    discount: float | None = None
    if intrinsic is not None and price is not None and price > 0:
        discount = (intrinsic - price) / intrinsic * 100.0

    results = [_result(name, weight, values[name]) for name, weight in models.MODEL_WEIGHTS.items()]

    return Valuation(
        symbol=company.symbol,
        intrinsic_value=intrinsic,
        current_price=price,
        discount=discount,
        recommendation=Recommendation(models.classify_recommendation(discount)),
        models=results,
        assumptions=_assumptions(),
    )


def _model_values(
    db: Session,
    company: Company,
    annual: list[FinancialStatement],
    price: float | None,
) -> dict[str, float | None]:
    latest = annual[0]
    shares = _f(latest.shares_outstanding)
    eps = _f(latest.eps_basic)
    net_income = _f(latest.net_income)
    equity = _f(latest.total_equity)

    net_debt = (_f(latest.total_debt) or 0.0) - (_f(latest.cash_and_equivalents) or 0.0)
    fcf = calc.free_cash_flow(_f(latest.operating_cash_flow), _f(latest.capital_expenditure))
    ebitda = calc.ebitda(_f(latest.operating_income), _f(latest.operating_cash_flow), net_income)
    book_value_per_share = calc.safe_div(equity, shares)
    dividend_per_share = calc.safe_div(_dividend_total(latest), shares)
    normalized_eps = _normalized_eps(annual)
    roe = calc.return_on_equity(net_income, equity)
    growth = _revenue_growth(annual)

    current_pe = calc.safe_div(price, eps)
    industry_pe = _industry_pe(db, company) or models.DEFAULT_MARKET_PE

    return {
        "Discounted Cash Flow": models.discounted_cash_flow(fcf, shares, net_debt, growth=growth),
        "Graham Intrinsic Value": models.graham_number(eps, book_value_per_share),
        "Historical P/E": models.historical_pe_value(normalized_eps, current_pe),
        "Industry P/E": models.industry_pe_value(eps, industry_pe),
        "EV/EBITDA": models.ev_ebitda_value(ebitda, models.DEFAULT_EV_EBITDA, net_debt, shares),
        "Residual Income": models.residual_income_value(book_value_per_share, roe, growth=growth),
        "Dividend Discount Model": models.dividend_discount_value(dividend_per_share, growth),
    }


def _dividend_total(s: FinancialStatement) -> float | None:
    value = _f(s.dividends_paid)
    return abs(value) if value is not None else None


def _normalized_eps(annual: list[FinancialStatement]) -> float | None:
    values = [_f(s.eps_basic) for s in annual]
    present = [v for v in values if v is not None]
    if not present:
        return None
    return sum(present) / len(present)


def _revenue_growth(annual: list[FinancialStatement]) -> float | None:
    """Revenue CAGR (a fraction) across the annual series, capped."""
    series = list(reversed(annual))  # oldest -> newest
    if len(series) < _MIN_GROWTH_PERIODS:
        return None
    years = len(series) - 1
    cagr = calc.cagr(_f(series[0].revenue), _f(series[-1].revenue), years)
    if cagr is None:
        return None
    return max(0.0, min(cagr, _MAX_GROWTH))


def _industry_pe(db: Session, company: Company) -> float | None:
    """Average trailing P/E of active sector peers (includes the company)."""
    if company.sector_id is None:
        return None
    stmt = select(Company).where(
        Company.sector_id == company.sector_id,
        Company.is_active.is_(True),
    )
    peers = db.execute(stmt).scalars().unique().all()

    ratios: list[float] = []
    for peer in peers:
        peer_annual = financials_repo.list_financials(
            db, peer.id, period_type=PeriodType.ANNUAL, limit=1
        )
        if not peer_annual:
            continue
        pe = calc.price_to_earnings(_f(peer.market_cap), _f(peer_annual[0].net_income))
        if pe is not None and pe > 0:
            ratios.append(pe)

    if not ratios:
        return None
    return sum(ratios) / len(ratios)
