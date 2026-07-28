"""Stock screener endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.screener import ScreenerResult
from app.services import screener as service

router = APIRouter(tags=["screener"])


@router.get("/screener", response_model=ScreenerResult)
def screener(  # noqa: PLR0917
    db: Annotated[Session, Depends(get_db)],
    min_roe: Annotated[float | None, Query(description="Minimum ROE (%)")] = None,
    min_roic: Annotated[float | None, Query(description="Minimum ROIC (%)")] = None,
    max_pe: Annotated[float | None, Query(description="Maximum P/E")] = None,
    min_dividend_yield: Annotated[
        float | None, Query(description="Minimum dividend yield (%)")
    ] = None,
    max_debt_to_equity: Annotated[float | None, Query(description="Maximum debt/equity")] = None,
    min_revenue_growth: Annotated[
        float | None, Query(description="Minimum revenue CAGR (%)")
    ] = None,
    positive_fcf: Annotated[bool, Query(description="Require positive free cash flow")] = False,
    sector: Annotated[str | None, Query(description="Filter by sector name")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
) -> ScreenerResult:
    """Filter PSX companies by value-investing rules (all filters optional)."""
    return service.run_screener(
        db,
        min_roe=min_roe,
        min_roic=min_roic,
        max_pe=max_pe,
        min_dividend_yield=min_dividend_yield,
        max_debt_to_equity=max_debt_to_equity,
        min_revenue_growth=min_revenue_growth,
        positive_fcf=positive_fcf,
        sector=sector,
        limit=limit,
    )
