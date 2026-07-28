"""Search endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.company import CompanySummary
from app.services import company as service

router = APIRouter(tags=["search"])


@router.get("/search", response_model=list[CompanySummary])
def search(
    db: Annotated[Session, Depends(get_db)],
    q: Annotated[str, Query(min_length=1, description="Symbol or company name")],
    limit: Annotated[int, Query(ge=1, le=25)] = 10,
) -> list[CompanySummary]:
    """Typeahead-style search across PSX companies."""
    return service.search_companies(db, q, limit=limit)
