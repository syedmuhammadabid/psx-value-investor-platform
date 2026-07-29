"""API v1 router aggregation."""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.routes import (
    alerts,
    auth,
    companies,
    health,
    portfolio,
    screener,
    search,
    watchlist,
)

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(auth.router)
api_router.include_router(companies.router)
api_router.include_router(search.router)
api_router.include_router(screener.router)
api_router.include_router(portfolio.router)
api_router.include_router(watchlist.router)
api_router.include_router(alerts.router)
