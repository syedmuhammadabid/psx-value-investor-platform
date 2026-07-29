"""Tests for the price-sync service."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.ingestion_job import IngestionJob, JobStatus
from app.scraper.prices import PriceSnapshotRow
from app.services import price_sync

_AS_OF = datetime(2026, 7, 28, 10, 36, 3, tzinfo=UTC)


def _row(symbol: str, price: str) -> PriceSnapshotRow:
    return PriceSnapshotRow(symbol=symbol, price=Decimal(price), as_of=_AS_OF)


def _price(db: Session, symbol: str) -> Decimal | None:
    company = db.execute(select(Company).where(Company.symbol == symbol)).scalar_one()
    return company.current_price


def test_updates_matching_company_prices(
    db_session: Session, seed_companies: list[Company]
) -> None:
    rows = [_row("MARI", "650.85"), _row("UBL", "473.33"), _row("NOTOURS", "99.99")]

    result = price_sync.sync_prices(db_session, rows, source="snapshot://test")

    assert _price(db_session, "MARI") == Decimal("650.85")
    assert _price(db_session, "UBL") == Decimal("473.33")
    assert result.matched == 2
    assert result.updated == 2


def test_matches_symbol_case_insensitively(
    db_session: Session, seed_companies: list[Company]
) -> None:
    result = price_sync.sync_prices(db_session, [_row("mari", "650.85")], source="s")

    assert result.updated == 1
    assert _price(db_session, "MARI") == Decimal("650.85")


def test_is_idempotent(db_session: Session, seed_companies: list[Company]) -> None:
    rows = [_row("MARI", "650.85")]
    price_sync.sync_prices(db_session, rows, source="s")

    result = price_sync.sync_prices(db_session, rows, source="s")

    assert result.updated == 0
    assert result.unchanged == 1


def test_reports_unmatched_tracked_companies(
    db_session: Session, seed_companies: list[Company]
) -> None:
    # Snapshot only carries MARI; UBL, SYS and OLDCO are tracked but absent.
    result = price_sync.sync_prices(db_session, [_row("MARI", "650.85")], source="s")

    assert result.status is JobStatus.PARTIAL
    assert set(result.unmatched_symbols) == {"UBL", "SYS", "OLDCO"}


def test_succeeds_when_every_company_matched(
    db_session: Session, seed_companies: list[Company]
) -> None:
    rows = [
        _row("MARI", "650.85"),
        _row("UBL", "473.33"),
        _row("SYS", "135.01"),
        _row("OLDCO", "1.00"),
    ]

    result = price_sync.sync_prices(db_session, rows, source="s")

    assert result.status is JobStatus.SUCCEEDED
    assert result.unmatched_symbols == []


def test_records_an_audit_job(db_session: Session, seed_companies: list[Company]) -> None:
    price_sync.sync_prices(db_session, [_row("MARI", "650.85")], source="snapshot://audit")

    job = db_session.execute(select(IngestionJob)).scalar_one()
    assert job.source == "snapshot://audit"
    assert job.finished_at is not None
    assert job.records_updated == 1
    assert job.records_skipped == 3
