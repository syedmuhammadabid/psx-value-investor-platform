"""Chart-ready historical metric series for a company.

Each point bundles the headline trend metrics for one annual period so the
frontend can plot long-term trends (Phase 6) without recomputing ratios.
Percentage-style figures (ROE, ROIC) are expressed as percentages.
"""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel


class MetricPoint(BaseModel):
    fiscal_year: int
    period_end: date
    revenue: float | None = None
    net_income: float | None = None
    eps: float | None = None
    roe: float | None = None
    roic: float | None = None
    dividend_per_share: float | None = None
    book_value_per_share: float | None = None
    free_cash_flow: float | None = None


class CompanyHistory(BaseModel):
    """A company's annual metric series, oldest period first."""

    symbol: str
    points: list[MetricPoint]
