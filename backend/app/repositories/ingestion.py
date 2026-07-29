"""Data-access layer for ingestion jobs and data-source provenance."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.data_source import DataSource
from app.models.ingestion_job import IngestionJob


def add_job(db: Session, job: IngestionJob) -> IngestionJob:
    """Persist a new ingestion job and assign its primary key."""
    db.add(job)
    db.flush()
    return job


def add_data_source(db: Session, source: DataSource) -> DataSource:
    """Append a provenance record for an ingested statement."""
    db.add(source)
    db.flush()
    return source


def latest_checksum(db: Session, financial_statement_id: uuid.UUID) -> str | None:
    """Return the most recent provenance checksum for a statement, if any."""
    stmt = (
        select(DataSource.checksum)
        .where(DataSource.financial_statement_id == financial_statement_id)
        .order_by(DataSource.extracted_at.desc())
        .limit(1)
    )
    return db.execute(stmt).scalar_one_or_none()


def list_data_sources(db: Session, company_id: uuid.UUID) -> list[DataSource]:
    """Return a company's provenance records, most recently extracted first."""
    stmt = (
        select(DataSource)
        .where(DataSource.company_id == company_id)
        .order_by(DataSource.extracted_at.desc())
    )
    return list(db.execute(stmt).scalars().all())
