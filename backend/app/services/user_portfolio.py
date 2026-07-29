"""Persisted portfolio service — user-scoped positions analysed via the shared engine."""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.user import User
from app.repositories import company as company_repo
from app.repositories import portfolio_position as position_repo
from app.schemas.portfolio import (
    PortfolioAnalysis,
    PortfolioHolding,
    PortfolioRequest,
    PortfolioSummary,
    PositionUpsert,
)
from app.services import portfolio as portfolio_service

_EMPTY_SUMMARY = PortfolioSummary(holdings_count=0, total_cost=0.0)


def get_portfolio(db: Session, user: User) -> PortfolioAnalysis:
    """Analyse the user's persisted positions (empty analysis if none)."""
    positions = position_repo.list_for_user(db, user.id)
    if not positions:
        return PortfolioAnalysis(summary=_EMPTY_SUMMARY, holdings=[])
    request = PortfolioRequest(
        holdings=[
            PortfolioHolding(
                symbol=p.symbol,
                quantity=float(p.quantity),
                average_cost=float(p.average_cost),
            )
            for p in positions
        ]
    )
    return portfolio_service.analyze_portfolio(db, request)


def upsert_position(db: Session, user: User, payload: PositionUpsert) -> PortfolioAnalysis:
    """Add or update a position, then return the refreshed analysis."""
    company = company_repo.get_by_symbol(db, payload.symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{payload.symbol}' not found.",
        )
    position_repo.upsert(
        db,
        user.id,
        symbol=company.symbol,
        quantity=Decimal(str(payload.quantity)),
        average_cost=Decimal(str(payload.average_cost)),
    )
    db.commit()
    return get_portfolio(db, user)


def remove_position(db: Session, user: User, symbol: str) -> PortfolioAnalysis:
    """Remove a position, then return the refreshed analysis (404 if absent)."""
    position = position_repo.get(db, user.id, symbol)
    if position is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"'{symbol}' is not in your portfolio.",
        )
    position_repo.delete(db, position)
    db.commit()
    return get_portfolio(db, user)
