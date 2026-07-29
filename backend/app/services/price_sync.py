"""Price-sync service — refreshes company last-traded prices from the snapshot.

Matches PSX price rows (parsed from the public market-data snapshot) against the
companies in our universe by symbol and updates ``current_price`` in place. The
run is recorded as an :class:`IngestionJob` for auditability and is idempotent:
re-running with the same snapshot leaves prices unchanged. Symbols in the
snapshot that we do not track are ignored; companies we track that are absent
from the snapshot are reported as unmatched.
"""

from __future__ import annotations

import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.ingestion_job import IngestionJob, JobStatus
from app.repositories import ingestion as ingestion_repo
from app.scraper import prices as prices_module
from app.scraper.prices import PriceSnapshotRow


@dataclass(frozen=True, slots=True)
class PriceSyncResult:
    """Summary of a single price-sync run."""

    job_id: uuid.UUID
    status: JobStatus
    snapshot_symbols: int
    matched: int
    updated: int
    unchanged: int
    unmatched_symbols: list[str] = field(default_factory=list)


def sync_prices(
    db: Session,
    rows: Sequence[PriceSnapshotRow],
    *,
    source: str,
    extracted_at: datetime | None = None,
) -> PriceSyncResult:
    """Update ``current_price`` for tracked companies from snapshot rows."""
    now = extracted_at or datetime.now(UTC)
    prices = prices_module.latest_by_symbol(rows)

    job = ingestion_repo.add_job(
        db,
        IngestionJob(
            source=source[:200],
            status=JobStatus.RUNNING,
            started_at=now,
            records_processed=len(prices),
        ),
    )

    companies = list(db.execute(select(Company)).scalars().unique().all())

    matched = 0
    updated = 0
    unchanged = 0
    unmatched: list[str] = []

    for company in companies:
        row = prices.get(company.symbol.upper())
        if row is None:
            unmatched.append(company.symbol)
            continue
        matched += 1
        if company.current_price is not None and company.current_price == row.price:
            unchanged += 1
            continue
        company.current_price = row.price
        updated += 1

    job.status = JobStatus.PARTIAL if unmatched else JobStatus.SUCCEEDED
    job.finished_at = datetime.now(UTC)
    job.records_updated = updated
    job.records_skipped = len(unmatched)
    db.commit()

    return PriceSyncResult(
        job_id=job.id,
        status=job.status,
        snapshot_symbols=len(prices),
        matched=matched,
        updated=updated,
        unchanged=unchanged,
        unmatched_symbols=unmatched,
    )
