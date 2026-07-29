"""Valuation request/response schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class Recommendation(StrEnum):
    """Headline call derived from the discount to intrinsic value."""

    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"


class ValuationModelResult(BaseModel):
    """A single model's per-share estimate and its blend weight."""

    name: str
    value: float | None = None
    weight: float
    applied: bool


class ValuationAssumptions(BaseModel):
    """Key assumptions behind the estimate, surfaced for transparency."""

    discount_rate: float
    terminal_growth: float
    projection_years: int


class Valuation(BaseModel):
    """Blended intrinsic value and recommendation for a company."""

    symbol: str
    currency: str = "PKR"
    intrinsic_value: float | None = None
    current_price: float | None = None
    # Discount to intrinsic value as a percentage (positive == undervalued).
    discount: float | None = None
    recommendation: Recommendation = Recommendation.HOLD
    models: list[ValuationModelResult]
    assumptions: ValuationAssumptions
