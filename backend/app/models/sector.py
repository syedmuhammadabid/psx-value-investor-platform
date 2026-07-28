"""Sector / industry taxonomy model."""

from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.company import Company


class Sector(UUIDMixin, TimestampMixin, Base):
    """A normalized PSX sector (e.g. Fertilizer, Commercial Banks)."""

    __tablename__ = "sectors"

    name: Mapped[str] = mapped_column(String(120), unique=True, index=True)

    companies: Mapped[list[Company]] = relationship(
        back_populates="sector",
        cascade="save-update",
    )
