"""Portfolio analysis endpoint (stateless) and persisted portfolio (authenticated)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import CurrentUser
from app.core.database import get_db
from app.schemas.portfolio import PortfolioAnalysis, PortfolioRequest, PositionUpsert
from app.services import portfolio as service
from app.services import user_portfolio as persisted_service

router = APIRouter(tags=["portfolio"])


@router.post("/portfolio/analyze", response_model=PortfolioAnalysis)
def analyze_portfolio(
    request: PortfolioRequest, db: Annotated[Session, Depends(get_db)]
) -> PortfolioAnalysis:
    """Compute gain/loss, margin of safety, expected CAGR and a health score."""
    return service.analyze_portfolio(db, request)


@router.get("/portfolio", response_model=PortfolioAnalysis)
def get_portfolio(
    current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PortfolioAnalysis:
    """Return the authenticated user's persisted portfolio analysis."""
    return persisted_service.get_portfolio(db, current_user)


@router.post("/portfolio", response_model=PortfolioAnalysis, status_code=status.HTTP_201_CREATED)
def upsert_position(
    payload: PositionUpsert,
    current_user: CurrentUser,
    db: Annotated[Session, Depends(get_db)],
) -> PortfolioAnalysis:
    """Add or update a position in the authenticated user's portfolio."""
    return persisted_service.upsert_position(db, current_user, payload)


@router.delete("/portfolio/{symbol}", response_model=PortfolioAnalysis)
def remove_position(
    symbol: str, current_user: CurrentUser, db: Annotated[Session, Depends(get_db)]
) -> PortfolioAnalysis:
    """Remove a position from the authenticated user's portfolio."""
    return persisted_service.remove_position(db, current_user, symbol)
