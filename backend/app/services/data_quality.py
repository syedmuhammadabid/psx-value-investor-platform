"""Data-quality service — surfaces freshness and provenance to users."""

from __future__ import annotations

from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.financial_statement import PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.repositories import ingestion as ingestion_repo
from app.schemas.data_quality import DataQualityReport, DataSourceInfo

_LOOKBACK = 100


def _aware(value: datetime) -> datetime:
    return value if value.tzinfo is not None else value.replace(tzinfo=UTC)


def _source_info(source: DataSource) -> DataSourceInfo:
    statement = source.financial_statement
    return DataSourceInfo(
        period_type=statement.period_type,
        fiscal_year=statement.fiscal_year,
        fiscal_period=statement.fiscal_period,
        source_type=source.source_type,
        source_url=source.source_url,
        source_page=source.source_page,
        extracted_at=_aware(source.extracted_at),
        checksum=source.checksum,
    )


def get_data_quality(db: Session, symbol: str) -> DataQualityReport:
    """Return freshness and provenance for a company (404 if it is missing)."""
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    annual = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.ANNUAL, limit=_LOOKBACK
    )
    quarterly = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.QUARTERLY, limit=_LOOKBACK
    )
    statements = annual + quarterly
    sources = ingestion_repo.list_data_sources(db, company.id)

    last_updated = max(_aware(s.updated_at) for s in statements) if statements else None
    latest_fiscal_year = max((s.fiscal_year for s in annual), default=None)
    staleness_days = (datetime.now(UTC) - last_updated).days if last_updated is not None else None

    return DataQualityReport(
        symbol=company.symbol,
        last_updated=last_updated,
        latest_fiscal_year=latest_fiscal_year,
        annual_periods=len(annual),
        quarterly_periods=len(quarterly),
        staleness_days=staleness_days,
        sources=[_source_info(source) for source in sources],
    )
