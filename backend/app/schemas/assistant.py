"""AI assistant request/response schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field

from app.schemas.valuation import Recommendation

DEFAULT_DISCLAIMER = (
    "This is an automated, informational answer generated from reported "
    "financials and our valuation models. It is not financial advice."
)


class AssistantRequest(BaseModel):
    """A natural-language question about a company."""

    question: str = Field(min_length=1, max_length=500)


class AssistantAnswer(BaseModel):
    """A deterministic answer composed from the company's computed data."""

    symbol: str
    question: str
    intent: str
    answer: str
    highlights: list[str]
    recommendation: Recommendation
    disclaimer: str = DEFAULT_DISCLAIMER
