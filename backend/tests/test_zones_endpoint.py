"""Tests for the buy & sell zones endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType


def _add_annual(
    db: Session,
    company: Company,
    *,
    fiscal_year: int,
    period_end: date,
    values: dict[str, str],
) -> None:
    db.add(
        FinancialStatement(
            company=company,
            period_type=PeriodType.ANNUAL,
            fiscal_year=fiscal_year,
            fiscal_period="FY",
            period_end=period_end,
            currency="PKR",
            **{key: Decimal(value) for key, value in values.items()},
        )
    )


_PRIOR = {
    "revenue": "400000000000",
    "operating_income": "320000000000",
    "net_income": "250000000000",
    "eps_basic": "30",
    "total_equity": "700000000000",
    "total_debt": "180000000000",
    "cash_and_equivalents": "40000000000",
    "shares_outstanding": "7500000000",
    "operating_cash_flow": "300000000000",
    "capital_expenditure": "-50000000000",
    "dividends_paid": "-45000000000",
}

_LATEST = {
    "revenue": "520000000000",
    "operating_income": "400000000000",
    "net_income": "300000000000",
    "eps_basic": "40",
    "total_equity": "800000000000",
    "total_debt": "200000000000",
    "cash_and_equivalents": "50000000000",
    "shares_outstanding": "7500000000",
    "operating_cash_flow": "350000000000",
    "capital_expenditure": "-60000000000",
    "dividends_paid": "-56000000000",
}


def test_zones_returns_five_ordered_bands(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    mari = seed_companies[0]  # MARI, current price 620.50
    _add_annual(db_session, mari, fiscal_year=2024, period_end=date(2024, 6, 30), values=_LATEST)
    _add_annual(db_session, mari, fiscal_year=2023, period_end=date(2023, 6, 30), values=_PRIOR)
    db_session.commit()

    response = client.get("/api/v1/companies/MARI/zones")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    assert body["currency"] == "PKR"
    assert body["current_price"] == 620.5
    assert body["intrinsic_value"] is not None and body["intrinsic_value"] > 0

    names = [zone["name"] for zone in body["zones"]]
    assert names == ["STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL"]

    # First band unbounded below, last unbounded above; bounds are contiguous.
    zones = body["zones"]
    assert zones[0]["lower"] is None
    assert zones[-1]["upper"] is None
    for lower_band, upper_band in zip(zones, zones[1:], strict=False):
        assert lower_band["upper"] == upper_band["lower"]

    # Exactly one band is flagged current, and it matches current_zone.
    current = [zone for zone in zones if zone["is_current"]]
    assert len(current) == 1
    assert current[0]["name"] == body["current_zone"]


def test_zones_empty_when_no_financials(client: TestClient, seed_companies: list[Company]) -> None:
    response = client.get("/api/v1/companies/SYS/zones")
    assert response.status_code == 200
    body = response.json()

    assert body["intrinsic_value"] is None
    assert body["current_zone"] is None
    assert body["current_price"] == 985.0
    assert body["zones"] == []


def test_zones_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/zones")
    assert response.status_code == 404
