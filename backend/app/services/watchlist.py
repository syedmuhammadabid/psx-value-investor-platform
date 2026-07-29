"""Watchlist service — user-scoped company tracking with light enrichment."""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.models.watchlist import WatchlistItem
from app.repositories import company as company_repo
from app.repositories import watchlist as watchlist_repo
from app.schemas.watchlist import WatchlistItemCreate, WatchlistItemOut
from app.services import valuation as valuation_service


def _to_out(db: Session, item: WatchlistItem) -> WatchlistItemOut:
    """Build an enriched watchlist entry (best-effort valuation)."""
    company = company_repo.get_by_symbol(db, item.symbol)
    out = WatchlistItemOut(
        symbol=item.symbol,
        name=company.name if company is not None else None,
        sector=company.sector.name if company is not None and company.sector else None,
        added_at=item.created_at,
    )
    if company is not None:
        valuation = valuation_service.get_valuation(db, company.symbol)
        out.current_price = valuation.current_price
        out.intrinsic_value = valuation.intrinsic_value
        out.discount = valuation.discount
        out.recommendation = valuation.recommendation.value
    return out


def list_watchlist(db: Session, user: User) -> list[WatchlistItemOut]:
    """Return the user's enriched watchlist."""
    return [_to_out(db, item) for item in watchlist_repo.list_for_user(db, user.id)]


def add_to_watchlist(db: Session, user: User, payload: WatchlistItemCreate) -> WatchlistItemOut:
    """Add a company to the user's watchlist (404 if unknown, 409 if duplicate)."""
    company = company_repo.get_by_symbol(db, payload.symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{payload.symbol}' not found.",
        )
    if watchlist_repo.get(db, user.id, company.symbol) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"'{company.symbol}' is already on your watchlist.",
        )
    item = watchlist_repo.add(db, user.id, company.symbol)
    db.commit()
    db.refresh(item)
    return _to_out(db, item)


def remove_from_watchlist(db: Session, user: User, symbol: str) -> None:
    """Remove a company from the user's watchlist (404 if not present)."""
    item = watchlist_repo.get(db, user.id, symbol)
    if item is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{symbol}' is not on your watchlist.",
        )
    watchlist_repo.delete(db, item)
    db.commit()
