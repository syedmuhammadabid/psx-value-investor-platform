"""Ratio engine service — assembles headline ratios for a company.

Point-in-time ratios (profitability, valuation, debt, liquidity, cash flow) use
the latest annual statement together with current market data. Growth figures
use the full available annual series.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.calculations import ratios as calc
from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.schemas.ratios import (
    CashFlowRatios,
    DebtRatios,
    FinancialRatios,
    GrowthRatios,
    LiquidityRatios,
    ProfitabilityRatios,
    ValuationRatios,
)

# How many annual periods to pull for growth (CAGR) calculations.
_GROWTH_WINDOW = 10
# Minimum annual periods required to compute a growth rate.
_MIN_GROWTH_PERIODS = 2


def _f(value: Decimal | None) -> float | None:
    """Coerce an optional Decimal to a float."""
    return float(value) if value is not None else None


def _pct(fraction: float | None) -> float | None:
    """Express a fraction (0.23) as a percentage (23.0)."""
    return fraction * 100.0 if fraction is not None else None


def get_ratios(db: Session, symbol: str) -> FinancialRatios:
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    # Newest first; index 0 is the latest annual period.
    annual = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.ANNUAL, limit=_GROWTH_WINDOW
    )
    if not annual:
        return FinancialRatios(
            symbol=company.symbol,
            profitability=ProfitabilityRatios(),
            valuation=ValuationRatios(dividend_yield=_f(company.dividend_yield)),
            debt=DebtRatios(),
            liquidity=LiquidityRatios(),
            cash_flow=CashFlowRatios(),
            growth=GrowthRatios(),
        )

    latest = annual[0]
    growth = _growth(annual)
    return FinancialRatios(
        symbol=company.symbol,
        fiscal_year=latest.fiscal_year,
        fiscal_period=latest.fiscal_period,
        period_end=latest.period_end,
        profitability=_profitability(latest),
        valuation=_valuation(company, latest, growth.eps_cagr),
        debt=_debt(latest),
        liquidity=_liquidity(latest),
        cash_flow=_cash_flow(company, latest),
        growth=growth,
    )


def _profitability(s: FinancialStatement) -> ProfitabilityRatios:
    return ProfitabilityRatios(
        gross_margin=_pct(calc.gross_margin(_f(s.gross_profit), _f(s.revenue))),
        operating_margin=_pct(calc.operating_margin(_f(s.operating_income), _f(s.revenue))),
        net_margin=_pct(calc.net_margin(_f(s.net_income), _f(s.revenue))),
        roe=_pct(calc.return_on_equity(_f(s.net_income), _f(s.total_equity))),
        roa=_pct(calc.return_on_assets(_f(s.net_income), _f(s.total_assets))),
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
    )


def _valuation(
    company: Company, s: FinancialStatement, eps_growth_pct: float | None
) -> ValuationRatios:
    market_cap = _f(company.market_cap)
    pe = calc.price_to_earnings(market_cap, _f(s.net_income))
    ev = calc.enterprise_value(market_cap, _f(s.total_debt), _f(s.cash_and_equivalents))
    ebitda = calc.ebitda(_f(s.operating_income), _f(s.operating_cash_flow), _f(s.net_income))
    # PEG needs EPS growth as a fraction; the growth engine reports a percentage.
    eps_growth = eps_growth_pct / 100.0 if eps_growth_pct is not None else None
    return ValuationRatios(
        pe=pe,
        pb=calc.price_to_book(market_cap, _f(s.total_equity)),
        peg=calc.peg_ratio(pe, eps_growth),
        ev_ebitda=calc.ev_to_ebitda(ev, ebitda),
        price_to_sales=calc.price_to_sales(market_cap, _f(s.revenue)),
        dividend_yield=_f(company.dividend_yield),
    )


def _debt(s: FinancialStatement) -> DebtRatios:
    return DebtRatios(
        debt_to_equity=calc.debt_to_equity(_f(s.total_debt), _f(s.total_equity)),
        interest_coverage=calc.interest_coverage(_f(s.operating_income), _f(s.interest_expense)),
    )


def _liquidity(s: FinancialStatement) -> LiquidityRatios:
    return LiquidityRatios(
        current_ratio=calc.current_ratio(_f(s.current_assets), _f(s.current_liabilities)),
        quick_ratio=calc.quick_ratio(
            _f(s.current_assets), _f(s.inventory), _f(s.current_liabilities)
        ),
    )


def _cash_flow(company: Company, s: FinancialStatement) -> CashFlowRatios:
    fcf = calc.free_cash_flow(_f(s.operating_cash_flow), _f(s.capital_expenditure))
    return CashFlowRatios(
        operating_cash_flow=_f(s.operating_cash_flow),
        free_cash_flow=fcf,
        fcf_yield=_pct(calc.fcf_yield(fcf, _f(company.market_cap))),
    )


def _growth(annual: list[FinancialStatement]) -> GrowthRatios:
    """Compute CAGRs across the annual series (oldest to newest)."""
    if len(annual) < _MIN_GROWTH_PERIODS:
        return GrowthRatios()

    series = list(reversed(annual))  # oldest -> newest
    years = len(series) - 1
    earliest, latest = series[0], series[-1]

    def _dividends(s: FinancialStatement) -> float | None:
        # Dividends paid are stored as a negative outflow; growth uses magnitude.
        value = _f(s.dividends_paid)
        return abs(value) if value is not None else None

    return GrowthRatios(
        revenue_cagr=_pct(calc.cagr(_f(earliest.revenue), _f(latest.revenue), years)),
        eps_cagr=_pct(calc.cagr(_f(earliest.eps_basic), _f(latest.eps_basic), years)),
        dividend_cagr=_pct(calc.cagr(_dividends(earliest), _dividends(latest), years)),
        years=years,
    )
