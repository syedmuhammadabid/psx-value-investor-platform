"""Health and readiness probes."""

from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.core.config import settings

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    """Liveness/readiness payload."""

    status: str
    environment: str
    version: str


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Return service liveness information."""
    return HealthResponse(
        status="ok",
        environment=settings.environment,
        version=settings.version,
    )
