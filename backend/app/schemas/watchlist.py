"""Watchlist request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class WatchlistItemCreate(BaseModel):
    """Payload to add a company to the watchlist."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)


class WatchlistItemOut(BaseModel):
    """A watchlist entry enriched with a light company snapshot."""

    symbol: str
    name: str | None = None
    sector: str | None = None
    current_price: float | None = None
    intrinsic_value: float | None = None
    discount: float | None = None
    recommendation: str | None = None
    added_at: datetime
