"""Company request/response schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, Field

if TYPE_CHECKING:
    from app.models.company import Company


class CompanySummary(BaseModel):
    """Compact company representation for lists and search results."""

    model_config = ConfigDict(from_attributes=True)

    symbol: str
    name: str
    sector: str | None = None
    industry: str | None = None
    market_cap: Decimal | None = None
    current_price: Decimal | None = None

    @classmethod
    def from_model(cls, company: Company) -> CompanySummary:
        return cls(
            symbol=company.symbol,
            name=company.name,
            sector=company.sector.name if company.sector else None,
            industry=company.industry,
            market_cap=company.market_cap,
            current_price=company.current_price,
        )


class CompanyDetail(CompanySummary):
    """Full company profile (Phase 3)."""

    fifty_two_week_high: Decimal | None = Field(default=None)
    fifty_two_week_low: Decimal | None = Field(default=None)
    dividend_yield: Decimal | None = Field(default=None)
    website: str | None = None
    fiscal_year_end: str | None = None
    listing_date: date | None = None
    description: str | None = None

    @classmethod
    def from_model(cls, company: Company) -> CompanyDetail:
        return cls(
            symbol=company.symbol,
            name=company.name,
            sector=company.sector.name if company.sector else None,
            industry=company.industry,
            market_cap=company.market_cap,
            current_price=company.current_price,
            fifty_two_week_high=company.fifty_two_week_high,
            fifty_two_week_low=company.fifty_two_week_low,
            dividend_yield=company.dividend_yield,
            website=company.website,
            fiscal_year_end=company.fiscal_year_end,
            listing_date=company.listing_date,
            description=company.description,
        )
