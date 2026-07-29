"""Tests for the data-quality endpoint."""

from __future__ import annotations

from datetime import date
from typing import Any

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.company import Company
from app.schemas.ingestion import RawFinancialRecord
from app.services import ingestion as ingestion_service


def _record(**overrides: Any) -> RawFinancialRecord:
    base: dict[str, Any] = {
        "symbol": "MARI",
        "period_type": "annual",
        "fiscal_year": 2023,
        "fiscal_period": "FY",
        "period_end": date(2023, 12, 31),
        "scale": "units",
        "source_url": "https://example.com/mari-2023.pdf",
        "source_page": 42,
        "revenue": 1000,
        "cost_of_revenue": 600,
        "gross_profit": 400,
        "net_income": 200,
        "shares_outstanding": 100,
        "eps_basic": 2.0,
        "total_assets": 2000,
        "total_liabilities": 1200,
        "total_equity": 800,
        "current_assets": 500,
        "current_liabilities": 400,
    }
    base.update(overrides)
    return RawFinancialRecord.model_validate(base)


def test_data_quality_reports_freshness_and_provenance(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    ingestion_service.ingest(db_session, "test", [_record()])

    response = client.get("/api/v1/companies/MARI/data-quality")

    assert response.status_code == 200
    body = response.json()
    assert body["symbol"] == "MARI"
    assert body["annual_periods"] == 1
    assert body["quarterly_periods"] == 0
    assert body["latest_fiscal_year"] == 2023
    assert body["staleness_days"] >= 0
    assert len(body["sources"]) == 1
    assert body["sources"][0]["source_page"] == 42
    assert body["sources"][0]["checksum"]


def test_data_quality_empty_for_company_without_data(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.get("/api/v1/companies/SYS/data-quality")

    assert response.status_code == 200
    body = response.json()
    assert body["annual_periods"] == 0
    assert body["last_updated"] is None
    assert body["staleness_days"] is None
    assert body["sources"] == []


def test_data_quality_unknown_symbol_returns_404(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.get("/api/v1/companies/NOPE/data-quality")

    assert response.status_code == 404
