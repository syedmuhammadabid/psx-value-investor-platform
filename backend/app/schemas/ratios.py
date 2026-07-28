"""Financial-ratio response schemas.

Percentage-style figures (margins, returns, growth, FCF yield) are expressed as
percentages (e.g. ``23.45`` == 23.45%), matching the convention used for
``dividend_yield``. Multiples (P/E, P/B, ratios) are plain numbers.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class ProfitabilityRatios(BaseModel):
    gross_margin: float | None = None
    operating_margin: float | None = None
    net_margin: float | None = None
    roe: float | None = None
    roa: float | None = None
    roic: float | None = None


class ValuationRatios(BaseModel):
    pe: float | None = None
    pb: float | None = None
    peg: float | None = None
    ev_ebitda: float | None = None
    price_to_sales: float | None = None
    dividend_yield: float | None = None


class DebtRatios(BaseModel):
    debt_to_equity: float | None = None
    interest_coverage: float | None = None


class LiquidityRatios(BaseModel):
    current_ratio: float | None = None
    quick_ratio: float | None = None


class CashFlowRatios(BaseModel):
    operating_cash_flow: float | None = None
    free_cash_flow: float | None = None
    fcf_yield: float | None = None


class GrowthRatios(BaseModel):
    revenue_cagr: float | None = None
    eps_cagr: float | None = None
    dividend_cagr: float | None = None
    # Number of annual intervals the CAGR figures span.
    years: int = 0


class FinancialRatios(BaseModel):
    """Headline ratios computed from the latest annual period plus growth trends."""

    symbol: str
    fiscal_year: int | None = None
    fiscal_period: str | None = None
    period_end: date | None = None
    profitability: ProfitabilityRatios
    valuation: ValuationRatios
    debt: DebtRatios
    liquidity: LiquidityRatios
    cash_flow: CashFlowRatios
    growth: GrowthRatios
