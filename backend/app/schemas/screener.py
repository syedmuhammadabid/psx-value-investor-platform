"""Stock screener request/response schemas."""

from __future__ import annotations

from decimal import Decimal

from pydantic import BaseModel


class ScreenerRow(BaseModel):
    """A company that passed the screen, with the metrics used to filter it.

    Percentage-style metrics (ROE, ROIC, dividend yield, revenue growth) are
    expressed as percentages (e.g. 23.4 == 23.4%). Multiples (P/E, D/E) are
    plain numbers.
    """

    symbol: str
    name: str
    sector: str | None = None
    market_cap: Decimal | None = None
    current_price: Decimal | None = None
    roe: float | None = None
    roic: float | None = None
    pe: float | None = None
    dividend_yield: float | None = None
    debt_to_equity: float | None = None
    revenue_growth: float | None = None
    free_cash_flow: float | None = None


class ScreenerResult(BaseModel):
    """Screener results, ordered by market cap (largest first)."""

    count: int
    items: list[ScreenerRow]
