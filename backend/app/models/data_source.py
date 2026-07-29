"""Data source model — append-only provenance for each ingested statement.

Every time a statement is written or updated, a row records where the data came
from (filing URL/page), when it was extracted, a content checksum, and the job
that produced it. Keeping this append-only preserves an audit trail across
restatements.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin

if TYPE_CHECKING:
    from app.models.financial_statement import FinancialStatement


class DataSource(UUIDMixin, TimestampMixin, Base):
    """Provenance record for one ingested financial statement."""

    __tablename__ = "data_sources"

    company_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), index=True
    )
    financial_statement_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("financial_statements.id", ondelete="CASCADE"), index=True
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        ForeignKey("ingestion_jobs.id", ondelete="SET NULL"), nullable=True, index=True
    )
    source_type: Mapped[str] = mapped_column(String(50))
    source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    source_page: Mapped[int | None] = mapped_column(Integer, nullable=True)
    checksum: Mapped[str] = mapped_column(String(64), index=True)
    extracted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    financial_statement: Mapped[FinancialStatement] = relationship()
