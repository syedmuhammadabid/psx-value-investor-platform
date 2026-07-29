"""Alert response schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class AlertSentiment(StrEnum):
    """Whether a triggered condition is favourable, adverse, or neutral."""

    POSITIVE = "positive"
    NEGATIVE = "negative"
    NEUTRAL = "neutral"


class AlertSignal(BaseModel):
    """A single alert condition that currently holds for a company."""

    type: str
    title: str
    detail: str
    sentiment: AlertSentiment


class AlertReport(BaseModel):
    """The set of alert conditions active for a company right now."""

    symbol: str
    currency: str = "PKR"
    alerts: list[AlertSignal]
