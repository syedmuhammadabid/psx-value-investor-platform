"""Alert subscription request/response schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.alerts import AlertSignal


class AlertSubscriptionCreate(BaseModel):
    """Payload to subscribe to alert signals for a company."""

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)


class AlertSubscriptionOut(BaseModel):
    """A subscription enriched with the signals currently active for the company."""

    symbol: str
    name: str | None = None
    subscribed_at: datetime
    alerts: list[AlertSignal]
