"""Tests for the company valuation endpoint."""

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


def test_valuation_returns_blended_intrinsic_value(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    mari = seed_companies[0]  # MARI, current price 620.50
    _add_annual(db_session, mari, fiscal_year=2024, period_end=date(2024, 6, 30), values=_LATEST)
    _add_annual(db_session, mari, fiscal_year=2023, period_end=date(2023, 6, 30), values=_PRIOR)
    db_session.commit()

    response = client.get("/api/v1/companies/MARI/valuation")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    assert body["currency"] == "PKR"
    assert body["current_price"] == 620.5
    assert body["intrinsic_value"] is not None and body["intrinsic_value"] > 0
    assert body["recommendation"] in {"BUY", "HOLD", "SELL"}

    # Discount is measured against intrinsic value.
    expected_discount = (body["intrinsic_value"] - 620.5) / body["intrinsic_value"] * 100
    assert body["discount"] == expected_discount

    # All seven models are reported; the core ones apply for this profile.
    assert len(body["models"]) == 7
    applied = {m["name"]: m["applied"] for m in body["models"]}
    assert applied["Discounted Cash Flow"] is True
    assert applied["Graham Intrinsic Value"] is True
    assert applied["Dividend Discount Model"] is True

    assumptions = body["assumptions"]
    assert assumptions["discount_rate"] == 0.15
    assert assumptions["terminal_growth"] == 0.04
    assert assumptions["projection_years"] == 5


def test_valuation_empty_when_no_financials(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.get("/api/v1/companies/SYS/valuation")
    assert response.status_code == 200
    body = response.json()

    assert body["intrinsic_value"] is None
    assert body["discount"] is None
    assert body["recommendation"] == "HOLD"
    assert body["current_price"] == 985.0
    assert len(body["models"]) == 7
    assert all(m["applied"] is False for m in body["models"])


def test_valuation_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/valuation")
    assert response.status_code == 404
