"""Buy & sell zone response schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ZoneName(StrEnum):
    """The five price bands, cheapest to most expensive."""

    STRONG_BUY = "STRONG_BUY"
    BUY = "BUY"
    HOLD = "HOLD"
    SELL = "SELL"
    STRONG_SELL = "STRONG_SELL"


class PriceZone(BaseModel):
    """A single price band with its (optional) bounds in PKR."""

    name: ZoneName
    label: str
    lower: float | None = None
    upper: float | None = None
    is_current: bool = False


class BuySellZones(BaseModel):
    """Price bands derived from a company's intrinsic value."""

    symbol: str
    currency: str = "PKR"
    intrinsic_value: float | None = None
    current_price: float | None = None
    current_zone: ZoneName | None = None
    zones: list[PriceZone]
