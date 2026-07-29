"""Portfolio analysis request/response schemas.

The portfolio endpoint is stateless: the client submits its holdings and gets
back computed analytics. Money figures (cost, market value, intrinsic value)
are plain numbers in PKR; margins, returns and CAGR are percentages.
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.valuation import Recommendation


class PortfolioHolding(BaseModel):
    """A single position the user holds."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)
    quantity: float = Field(gt=0, description="Number of shares held.")
    average_cost: float = Field(ge=0, description="Average purchase price per share (PKR).")


class PortfolioRequest(BaseModel):
    """A portfolio submitted for analysis."""

    model_config = ConfigDict(extra="forbid")

    holdings: list[PortfolioHolding] = Field(min_length=1, max_length=100)


class HoldingAnalysis(BaseModel):
    """Computed analytics for a single holding."""

    symbol: str
    name: str | None = None
    quantity: float
    average_cost: float
    current_price: float | None = None
    cost_basis: float
    market_value: float | None = None
    gain_loss: float | None = None
    gain_loss_pct: float | None = None
    intrinsic_value: float | None = None
    intrinsic_total: float | None = None
    margin_of_safety: float | None = None
    expected_cagr: float | None = None
    recommendation: Recommendation | None = None
    weight: float | None = None


class PortfolioSummary(BaseModel):
    """Portfolio-level roll-up across all holdings."""

    holdings_count: int
    total_cost: float
    total_market_value: float | None = None
    total_gain_loss: float | None = None
    total_gain_loss_pct: float | None = None
    total_intrinsic_value: float | None = None
    margin_of_safety: float | None = None
    expected_cagr: float | None = None
    health_score: int | None = None


class PortfolioAnalysis(BaseModel):
    """The full stateless portfolio analysis response."""

    currency: str = "PKR"
    summary: PortfolioSummary
    holdings: list[HoldingAnalysis]


class PositionUpsert(BaseModel):
    """Add or update a persisted portfolio position for the current user."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)
    quantity: float = Field(gt=0, description="Number of shares held.")
    average_cost: float = Field(ge=0, description="Average purchase price per share (PKR).")
