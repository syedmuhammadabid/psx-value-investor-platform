"""Company endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.financial_statement import PeriodType
from app.repositories.company import CompanySort
from app.schemas.company import CompanyDetail, CompanySummary
from app.schemas.financials import FinancialStatements
from app.schemas.history import CompanyHistory
from app.schemas.pagination import Page
from app.schemas.ratios import FinancialRatios
from app.services import company as service
from app.services import financials as financials_service
from app.services import history as history_service
from app.services import ratios as ratios_service

router = APIRouter(prefix="/companies", tags=["companies"])


@router.get("", response_model=Page[CompanySummary])
def list_companies(  # noqa: PLR0917
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
    q: Annotated[str | None, Query(description="Search by symbol or name")] = None,
    sector: Annotated[str | None, Query(description="Filter by sector name")] = None,
    sort: CompanySort = CompanySort.MARKET_CAP,
) -> Page[CompanySummary]:
    """List PSX companies with pagination, search, and sector filtering."""
    return service.list_companies(
        db, limit=limit, offset=offset, search=q, sector=sector, sort=sort
    )


@router.get("/{symbol}", response_model=CompanyDetail)
def get_company(symbol: str, db: Annotated[Session, Depends(get_db)]) -> CompanyDetail:
    """Fetch a single company's full profile by symbol."""
    return service.get_company(db, symbol)


@router.get("/{symbol}/financials", response_model=FinancialStatements)
def get_financials(
    symbol: str,
    db: Annotated[Session, Depends(get_db)],
    period: PeriodType = PeriodType.ANNUAL,
    limit: Annotated[int, Query(ge=1, le=40)] = 10,
) -> FinancialStatements:
    """Return income, balance sheet, and cash-flow statements for a company."""
    return financials_service.get_financials(db, symbol, period_type=period, limit=limit)


@router.get("/{symbol}/ratios", response_model=FinancialRatios)
def get_ratios(symbol: str, db: Annotated[Session, Depends(get_db)]) -> FinancialRatios:
    """Return headline financial ratios for a company's latest annual period."""
    return ratios_service.get_ratios(db, symbol)


@router.get("/{symbol}/history", response_model=CompanyHistory)
def get_history(
    symbol: str,
    db: Annotated[Session, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=40)] = 10,
) -> CompanyHistory:
    """Return a chart-ready annual metric series for a company (oldest first)."""
    return history_service.get_history(db, symbol, limit=limit)
