"""Ingestion job model — one row per pipeline run for auditability."""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base
from app.models.base import TimestampMixin, UUIDMixin


class JobStatus(enum.StrEnum):
    """Terminal status of an ingestion run."""

    RUNNING = "running"
    SUCCEEDED = "succeeded"
    PARTIAL = "partial"
    FAILED = "failed"


class IngestionJob(UUIDMixin, TimestampMixin, Base):
    """Run history for a single ingestion invocation."""

    __tablename__ = "ingestion_jobs"

    source: Mapped[str] = mapped_column(String(200))
    status: Mapped[JobStatus] = mapped_column(
        SAEnum(
            JobStatus,
            name="ingestion_job_status",
            values_callable=lambda enum: [member.value for member in enum],
        ),
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    records_processed: Mapped[int] = mapped_column(Integer, default=0)
    records_ingested: Mapped[int] = mapped_column(Integer, default=0)
    records_updated: Mapped[int] = mapped_column(Integer, default=0)
    records_skipped: Mapped[int] = mapped_column(Integer, default=0)
    records_rejected: Mapped[int] = mapped_column(Integer, default=0)
    records_flagged: Mapped[int] = mapped_column(Integer, default=0)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
