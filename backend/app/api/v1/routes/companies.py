"""Company endpoints."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.financial_statement import PeriodType
from app.repositories.company import CompanySort
from app.schemas.alerts import AlertReport
from app.schemas.assistant import AssistantAnswer, AssistantRequest
from app.schemas.company import CompanyDetail, CompanySummary
from app.schemas.data_quality import DataQualityReport
from app.schemas.financials import FinancialStatements
from app.schemas.history import CompanyHistory
from app.schemas.pagination import Page
from app.schemas.ratios import FinancialRatios
from app.schemas.recommendation import RecommendationReport
from app.schemas.scores import CompanyScores
from app.schemas.valuation import Valuation
from app.schemas.zones import BuySellZones
from app.services import alerts as alerts_service
from app.services import assistant as assistant_service
from app.services import company as service
from app.services import data_quality as data_quality_service
from app.services import financials as financials_service
from app.services import history as history_service
from app.services import ratios as ratios_service
from app.services import recommendation as recommendation_service
from app.services import scores as scores_service
from app.services import valuation as valuation_service
from app.services import zones as zones_service

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


@router.get("/{symbol}/valuation", response_model=Valuation)
def get_valuation(symbol: str, db: Annotated[Session, Depends(get_db)]) -> Valuation:
    """Return a blended intrinsic value and recommendation for a company."""
    return valuation_service.get_valuation(db, symbol)


@router.get("/{symbol}/zones", response_model=BuySellZones)
def get_zones(symbol: str, db: Annotated[Session, Depends(get_db)]) -> BuySellZones:
    """Return buy/sell price bands derived from the intrinsic value."""
    return zones_service.get_zones(db, symbol)


@router.get("/{symbol}/recommendation", response_model=RecommendationReport)
def get_recommendation(
    symbol: str, db: Annotated[Session, Depends(get_db)]
) -> RecommendationReport:
    """Return the BUY/HOLD/SELL call with the explainable reasons behind it."""
    return recommendation_service.get_recommendation(db, symbol)


@router.get("/{symbol}/alerts", response_model=AlertReport)
def get_alerts(symbol: str, db: Annotated[Session, Depends(get_db)]) -> AlertReport:
    """Return the alert conditions currently active for a company."""
    return alerts_service.get_alerts(db, symbol)


@router.get("/{symbol}/scores", response_model=CompanyScores)
def get_scores(symbol: str, db: Annotated[Session, Depends(get_db)]) -> CompanyScores:
    """Return the investment scorecard (health, Buffett, Graham, Piotroski, etc.)."""
    return scores_service.get_scores(db, symbol)


@router.get("/{symbol}/data-quality", response_model=DataQualityReport)
def get_data_quality(symbol: str, db: Annotated[Session, Depends(get_db)]) -> DataQualityReport:
    """Return data freshness and provenance so users can gauge trust."""
    return data_quality_service.get_data_quality(db, symbol)


@router.post("/{symbol}/assistant", response_model=AssistantAnswer)
def ask_assistant(
    symbol: str,
    request: AssistantRequest,
    db: Annotated[Session, Depends(get_db)],
) -> AssistantAnswer:
    """Answer a natural-language question about a company from its computed data."""
    return assistant_service.ask(db, symbol, request.question)
