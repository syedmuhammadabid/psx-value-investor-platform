"""Explainable recommendation response schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel

from app.schemas.valuation import Recommendation


class Sentiment(StrEnum):
    """Whether a reason supports, opposes, or is neutral toward the call."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class RecommendationReason(BaseModel):
    """A single explainable factor behind the recommendation."""

    label: str
    detail: str
    sentiment: Sentiment


class RecommendationReport(BaseModel):
    """The headline call plus the transparent reasons that justify it."""

    symbol: str
    recommendation: Recommendation
    summary: str
    intrinsic_value: float | None = None
    current_price: float | None = None
    discount: float | None = None
    reasons: list[RecommendationReason]
