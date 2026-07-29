"""Tests for the ingestion service (write path of the data pipeline)."""

from __future__ import annotations

from datetime import date
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.data_source import DataSource
from app.models.financial_statement import FinancialStatement
from app.schemas.ingestion import RawFinancialRecord, RecordStatus
from app.services import ingestion as ingestion_service


def _record(**overrides: Any) -> RawFinancialRecord:
    base: dict[str, Any] = {
        "symbol": "MARI",
        "period_type": "annual",
        "fiscal_year": 2023,
        "fiscal_period": "FY",
        "period_end": date(2023, 12, 31),
        "currency": "PKR",
        "scale": "units",
        "source_url": "https://example.com/mari-2023.pdf",
        "source_page": 42,
        "revenue": 1000,
        "cost_of_revenue": 600,
        "gross_profit": 400,
        "operating_expenses": 100,
        "operating_income": 300,
        "pretax_income": 250,
        "tax_expense": 50,
        "net_income": 200,
        "eps_basic": 2.0,
        "shares_outstanding": 100,
        "current_assets": 500,
        "total_assets": 2000,
        "current_liabilities": 400,
        "total_liabilities": 1200,
        "total_equity": 800,
        "dividends_paid": 50,
    }
    base.update(overrides)
    return RawFinancialRecord.model_validate(base)


def test_ingest_creates_statement_and_provenance(
    db_session: Session, seed_companies: list[Company]
) -> None:
    report = ingestion_service.ingest(db_session, "test", [_record()])

    assert report.ingested == 1
    assert report.outcomes[0].status is RecordStatus.INGESTED
    statements = db_session.execute(select(FinancialStatement)).scalars().all()
    assert len(statements) == 1
    assert statements[0].revenue == 1000
    sources = db_session.execute(select(DataSource)).scalars().all()
    assert len(sources) == 1
    assert sources[0].source_page == 42


def test_ingest_scales_amounts(db_session: Session, seed_companies: list[Company]) -> None:
    ingestion_service.ingest(db_session, "test", [_record(scale="millions")])

    statement = db_session.execute(select(FinancialStatement)).scalar_one()
    assert statement.revenue == 1_000_000_000


def test_ingest_is_idempotent(db_session: Session, seed_companies: list[Company]) -> None:
    ingestion_service.ingest(db_session, "test", [_record()])
    report = ingestion_service.ingest(db_session, "test", [_record()])

    assert report.skipped == 1
    assert report.ingested == 0
    assert report.outcomes[0].status is RecordStatus.SKIPPED
    # No duplicate statement and no extra provenance row on a no-op run.
    assert db_session.execute(select(func.count()).select_from(FinancialStatement)).scalar() == 1
    assert db_session.execute(select(func.count()).select_from(DataSource)).scalar() == 1


def test_ingest_updates_changed_record(db_session: Session, seed_companies: list[Company]) -> None:
    ingestion_service.ingest(db_session, "test", [_record()])
    report = ingestion_service.ingest(db_session, "test", [_record(dividends_paid=75)])

    assert report.updated == 1
    assert report.outcomes[0].status is RecordStatus.UPDATED
    statement = db_session.execute(select(FinancialStatement)).scalar_one()
    assert statement.dividends_paid == 75
    assert db_session.execute(select(func.count()).select_from(DataSource)).scalar() == 2


def test_unknown_symbol_rejected(db_session: Session, seed_companies: list[Company]) -> None:
    report = ingestion_service.ingest(db_session, "test", [_record(symbol="NOPE")])

    assert report.rejected == 1
    assert report.status == "failed"
    assert report.outcomes[0].status is RecordStatus.REJECTED
    assert report.outcomes[0].issues[0].code == "unknown_company"
    assert db_session.execute(select(func.count()).select_from(FinancialStatement)).scalar() == 0


def test_accounting_anomaly_rejected(db_session: Session, seed_companies: list[Company]) -> None:
    report = ingestion_service.ingest(db_session, "test", [_record(total_equity=500)])

    assert report.rejected == 1
    codes = {issue.code for issue in report.outcomes[0].issues}
    assert "accounting_equation" in codes
    # Rejected records are never written.
    assert db_session.execute(select(func.count()).select_from(FinancialStatement)).scalar() == 0


def test_warning_flags_but_ingests(db_session: Session, seed_companies: list[Company]) -> None:
    report = ingestion_service.ingest(db_session, "test", [_record(gross_profit=999)])

    assert report.ingested == 1
    assert report.flagged == 1
    codes = {issue.code for issue in report.outcomes[0].issues}
    assert "gross_profit_mismatch" in codes
    assert db_session.execute(select(func.count()).select_from(FinancialStatement)).scalar() == 1


def test_partial_status_with_mixed_outcomes(
    db_session: Session, seed_companies: list[Company]
) -> None:
    report = ingestion_service.ingest(db_session, "test", [_record(), _record(symbol="NOPE")])

    assert report.status == "partial"
    assert report.ingested == 1
    assert report.rejected == 1
