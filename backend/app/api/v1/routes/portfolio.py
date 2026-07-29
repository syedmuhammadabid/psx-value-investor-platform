"""Portfolio analysis endpoint (stateless)."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.portfolio import PortfolioAnalysis, PortfolioRequest
from app.services import portfolio as service

router = APIRouter(tags=["portfolio"])


@router.post("/portfolio/analyze", response_model=PortfolioAnalysis)
def analyze_portfolio(
    request: PortfolioRequest, db: Annotated[Session, Depends(get_db)]
) -> PortfolioAnalysis:
    """Compute gain/loss, margin of safety, expected CAGR and a health score."""
    return service.analyze_portfolio(db, request)
