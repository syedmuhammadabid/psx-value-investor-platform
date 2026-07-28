"""Company service — orchestrates repository access and schema mapping."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.repositories import company as repo
from app.repositories.company import CompanySort
from app.schemas.company import CompanyDetail, CompanySummary
from app.schemas.pagination import Page


def list_companies(
    db: Session,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    sector: str | None = None,
    sort: CompanySort = CompanySort.MARKET_CAP,
) -> Page[CompanySummary]:
    companies, total = repo.list_companies(
        db, limit=limit, offset=offset, search=search, sector=sector, sort=sort
    )
    return Page(
        items=[CompanySummary.from_model(c) for c in companies],
        total=total,
        limit=limit,
        offset=offset,
    )


def get_company(db: Session, symbol: str) -> CompanyDetail:
    company = repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )
    return CompanyDetail.from_model(company)


def search_companies(db: Session, query: str, *, limit: int = 10) -> list[CompanySummary]:
    companies = repo.search_companies(db, query, limit=limit)
    return [CompanySummary.from_model(c) for c in companies]
