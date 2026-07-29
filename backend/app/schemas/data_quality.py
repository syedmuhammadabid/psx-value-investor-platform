"""Data-quality and provenance schemas (user-facing freshness reporting)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from app.models.financial_statement import PeriodType


class DataSourceInfo(BaseModel):
    """Provenance for one ingested statement."""

    period_type: PeriodType
    fiscal_year: int
    fiscal_period: str
    source_type: str
    source_url: str | None = None
    source_page: int | None = None
    extracted_at: datetime
    checksum: str


class DataQualityReport(BaseModel):
    """Freshness and provenance summary for a company's financial data."""

    symbol: str
    currency: str = "PKR"
    last_updated: datetime | None = None
    latest_fiscal_year: int | None = None
    annual_periods: int = 0
    quarterly_periods: int = 0
    staleness_days: int | None = None
    sources: list[DataSourceInfo]
