"""Data-access layer for companies."""

from __future__ import annotations

from enum import StrEnum
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.sector import Sector


class CompanySort(StrEnum):
    """Supported sort orders for company listings."""

    NAME = "name"
    MARKET_CAP = "market_cap"
    SYMBOL = "symbol"


def list_companies(
    db: Session,
    *,
    limit: int,
    offset: int,
    search: str | None = None,
    sector: str | None = None,
    sort: CompanySort = CompanySort.MARKET_CAP,
) -> tuple[list[Company], int]:
    """Return a page of active companies and the total matching count."""
    stmt = select(Company).where(Company.is_active.is_(True))

    if search:
        pattern = f"%{search.strip()}%"
        stmt = stmt.where(or_(Company.symbol.ilike(pattern), Company.name.ilike(pattern)))
    if sector:
        stmt = stmt.join(Company.sector).where(Sector.name == sector)

    total = db.execute(select(func.count()).select_from(stmt.subquery())).scalar_one()

    order_by: Any = {
        CompanySort.NAME: Company.name.asc(),
        CompanySort.SYMBOL: Company.symbol.asc(),
        CompanySort.MARKET_CAP: Company.market_cap.desc().nullslast(),
    }[sort]

    stmt = stmt.order_by(order_by).limit(limit).offset(offset)
    companies = list(db.execute(stmt).scalars().unique().all())
    return companies, total


def get_by_symbol(db: Session, symbol: str) -> Company | None:
    """Fetch a single company by its (case-insensitive) symbol."""
    stmt = select(Company).where(func.upper(Company.symbol) == symbol.upper())
    return db.execute(stmt).scalars().unique().one_or_none()


def search_companies(db: Session, query: str, *, limit: int = 10) -> list[Company]:
    """Return up to ``limit`` companies matching a symbol/name query."""
    pattern = f"%{query.strip()}%"
    stmt = (
        select(Company)
        .where(Company.is_active.is_(True))
        .where(or_(Company.symbol.ilike(pattern), Company.name.ilike(pattern)))
        .order_by(Company.market_cap.desc().nullslast())
        .limit(limit)
    )
    return list(db.execute(stmt).scalars().unique().all())
