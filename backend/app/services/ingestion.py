"""Ingestion service — the write path of the data pipeline.

Turns raw source records into validated, normalized, idempotently-upserted
financial statements, recording provenance and a job audit trail. Error-severity
sanity checks block a record; warnings flag it for review but still ingest it.
Re-ingesting identical data is a no-op (checksum match), so runs are safe to
repeat.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Sequence
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.data_source import DataSource
from app.models.financial_statement import FinancialStatement
from app.models.ingestion_job import IngestionJob, JobStatus
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.repositories import ingestion as ingestion_repo
from app.schemas.ingestion import (
    IngestionReport,
    RawFinancialRecord,
    RecordOutcome,
    RecordStatus,
    ValidationIssueOut,
)
from app.scraper import normalize, validation
from app.scraper.normalize import NormalizationError

# Every numeric column that carries data (used for checksums and upserts).
_FINANCIAL_FIELDS: tuple[str, ...] = tuple(sorted(normalize.MONEY_FIELDS | {"eps_basic"}))


def _to_decimal(value: float | None) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _to_float(value: Decimal | None) -> float | None:
    return None if value is None else float(value)


def _checksum(normalized: dict[str, Decimal | None]) -> str:
    payload = {
        field: (None if value is None else str(value)) for field, value in normalized.items()
    }
    encoded = json.dumps(payload, sort_keys=True).encode()
    return hashlib.sha256(encoded).hexdigest()


def _figures(values: dict[str, float | None]) -> validation.Figures:
    return validation.Figures(**{name: values.get(name) for name in validation.Figures._fields})


def _statement_figures(statement: FinancialStatement) -> validation.Figures:
    return validation.Figures(
        **{name: _to_float(getattr(statement, name)) for name in validation.Figures._fields}
    )


def _issue_out(issue: validation.ValidationIssue) -> ValidationIssueOut:
    return ValidationIssueOut(code=issue.code, message=issue.message, severity=issue.severity)


def _reject(
    record: RawFinancialRecord, fiscal_period: str, issues: list[validation.ValidationIssue]
) -> RecordOutcome:
    return RecordOutcome(
        symbol=record.symbol,
        period_type=record.period_type,
        fiscal_year=record.fiscal_year,
        fiscal_period=fiscal_period,
        status=RecordStatus.REJECTED,
        issues=[_issue_out(issue) for issue in issues],
    )


class _Tally:
    """Mutable counters accumulated across a run."""

    def __init__(self) -> None:
        self.ingested = 0
        self.updated = 0
        self.skipped = 0
        self.rejected = 0
        self.flagged = 0


def ingest(
    db: Session,
    source: str,
    records: Sequence[RawFinancialRecord],
    *,
    source_type: str = "file",
    extracted_at: datetime | None = None,
) -> IngestionReport:
    """Ingest a batch of raw records, returning a per-record report."""
    now = extracted_at or datetime.now(UTC)
    job = ingestion_repo.add_job(
        db,
        IngestionJob(
            source=source,
            status=JobStatus.RUNNING,
            started_at=now,
            records_processed=len(records),
            records_ingested=0,
            records_updated=0,
            records_skipped=0,
            records_rejected=0,
            records_flagged=0,
        ),
    )

    tally = _Tally()
    outcomes = [
        _ingest_record(db, record, job=job, source_type=source_type, now=now, tally=tally)
        for record in records
    ]

    job.status = _job_status(tally, processed=len(records))
    job.finished_at = datetime.now(UTC)
    job.records_ingested = tally.ingested
    job.records_updated = tally.updated
    job.records_skipped = tally.skipped
    job.records_rejected = tally.rejected
    job.records_flagged = tally.flagged
    db.commit()

    return IngestionReport(
        source=source,
        job_id=job.id,
        status=job.status,
        processed=len(records),
        ingested=tally.ingested,
        updated=tally.updated,
        skipped=tally.skipped,
        rejected=tally.rejected,
        flagged=tally.flagged,
        outcomes=outcomes,
    )


def _ingest_record(
    db: Session,
    record: RawFinancialRecord,
    *,
    job: IngestionJob,
    source_type: str,
    now: datetime,
    tally: _Tally,
) -> RecordOutcome:
    company = company_repo.get_by_symbol(db, record.symbol)
    if company is None:
        tally.rejected += 1
        return _reject(
            record,
            record.fiscal_period or "",
            [
                validation.ValidationIssue(
                    "unknown_company",
                    f"No company found for symbol '{record.symbol}'.",
                    validation.Severity.ERROR,
                )
            ],
        )

    try:
        scale = normalize.parse_scale(record.scale)
        fiscal_period = normalize.canonical_fiscal_period(record.period_type, record.fiscal_period)
    except NormalizationError as exc:
        tally.rejected += 1
        return _reject(
            record,
            record.fiscal_period or "",
            [
                validation.ValidationIssue(
                    "normalization_error", str(exc), validation.Severity.ERROR
                )
            ],
        )

    raw = record.model_dump()
    normalized = normalize.normalize_figures(
        {field: _to_decimal(raw[field]) for field in _FINANCIAL_FIELDS}, scale
    )
    issues = _validate(db, company, record, fiscal_period=fiscal_period, normalized=normalized)

    if validation.has_errors(issues):
        tally.rejected += 1
        return _reject(record, fiscal_period, issues)

    status = _upsert(
        db,
        company,
        record,
        job=job,
        fiscal_period=fiscal_period,
        normalized=normalized,
        source_type=source_type,
        now=now,
        tally=tally,
    )
    if any(issue.severity is validation.Severity.WARNING for issue in issues):
        tally.flagged += 1

    return RecordOutcome(
        symbol=record.symbol,
        period_type=record.period_type,
        fiscal_year=record.fiscal_year,
        fiscal_period=fiscal_period,
        status=status,
        issues=[_issue_out(issue) for issue in issues],
    )


def _validate(
    db: Session,
    company: Company,
    record: RawFinancialRecord,
    *,
    fiscal_period: str,
    normalized: dict[str, Decimal | None],
) -> list[validation.ValidationIssue]:
    figures = _figures({field: _to_float(normalized[field]) for field in _FINANCIAL_FIELDS})
    issues = validation.validate(figures)

    prior = financials_repo.get_by_natural_key(
        db,
        company.id,
        period_type=record.period_type,
        fiscal_year=record.fiscal_year - 1,
        fiscal_period=fiscal_period,
    )
    if prior is not None:
        issues.extend(validation.validate_yoy(figures, _statement_figures(prior)))
    return issues


def _upsert(
    db: Session,
    company: Company,
    record: RawFinancialRecord,
    *,
    job: IngestionJob,
    fiscal_period: str,
    normalized: dict[str, Decimal | None],
    source_type: str,
    now: datetime,
    tally: _Tally,
) -> RecordStatus:
    existing = financials_repo.get_by_natural_key(
        db,
        company.id,
        period_type=record.period_type,
        fiscal_year=record.fiscal_year,
        fiscal_period=fiscal_period,
    )
    checksum = _checksum(normalized)

    if existing is None:
        statement = FinancialStatement(
            company_id=company.id,
            period_type=record.period_type,
            fiscal_year=record.fiscal_year,
            fiscal_period=fiscal_period,
        )
        _apply(statement, record, normalized)
        db.add(statement)
        db.flush()
        status = RecordStatus.INGESTED
        tally.ingested += 1
    elif ingestion_repo.latest_checksum(db, existing.id) == checksum:
        tally.skipped += 1
        return RecordStatus.SKIPPED
    else:
        _apply(existing, record, normalized)
        db.flush()
        statement = existing
        status = RecordStatus.UPDATED
        tally.updated += 1

    ingestion_repo.add_data_source(
        db,
        DataSource(
            company_id=company.id,
            financial_statement_id=statement.id,
            job_id=job.id,
            source_type=source_type,
            source_url=record.source_url,
            source_page=record.source_page,
            checksum=checksum,
            extracted_at=now,
        ),
    )
    return status


def _apply(
    statement: FinancialStatement,
    record: RawFinancialRecord,
    normalized: dict[str, Decimal | None],
) -> None:
    statement.period_end = record.period_end
    statement.currency = record.currency
    for field in _FINANCIAL_FIELDS:
        setattr(statement, field, normalized[field])


def _job_status(tally: _Tally, *, processed: int) -> JobStatus:
    written = tally.ingested + tally.updated + tally.skipped
    if tally.rejected == 0:
        return JobStatus.SUCCEEDED
    if written == 0 and processed > 0:
        return JobStatus.FAILED
    return JobStatus.PARTIAL
