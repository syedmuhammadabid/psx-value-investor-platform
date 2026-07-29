"""Tests for the explainable recommendation endpoint."""

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
    "interest_expense": "8000000000",
    "eps_basic": "30",
    "total_equity": "700000000000",
    "total_debt": "180000000000",
    "current_assets": "300000000000",
    "current_liabilities": "120000000000",
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
    "interest_expense": "9000000000",
    "eps_basic": "40",
    "total_equity": "800000000000",
    "total_debt": "200000000000",
    "current_assets": "360000000000",
    "current_liabilities": "130000000000",
    "cash_and_equivalents": "50000000000",
    "shares_outstanding": "7500000000",
    "operating_cash_flow": "350000000000",
    "capital_expenditure": "-60000000000",
    "dividends_paid": "-56000000000",
}


def test_recommendation_has_call_summary_and_reasons(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    mari = seed_companies[0]  # MARI, current price 620.50
    _add_annual(db_session, mari, fiscal_year=2024, period_end=date(2024, 6, 30), values=_LATEST)
    _add_annual(db_session, mari, fiscal_year=2023, period_end=date(2023, 6, 30), values=_PRIOR)
    db_session.commit()

    response = client.get("/api/v1/companies/MARI/recommendation")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    assert body["recommendation"] in {"BUY", "HOLD", "SELL"}
    assert body["summary"].startswith("MARI")
    assert body["intrinsic_value"] is not None and body["intrinsic_value"] > 0
    assert body["current_price"] == 620.5

    reasons = body["reasons"]
    assert len(reasons) >= 5
    labels = {reason["label"] for reason in reasons}
    assert {"Valuation", "Return on equity", "Return on invested capital"} <= labels
    for reason in reasons:
        assert reason["sentiment"] in {"positive", "negative", "neutral"}
        assert reason["label"] and reason["detail"]


def test_recommendation_empty_when_no_financials(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.get("/api/v1/companies/SYS/recommendation")
    assert response.status_code == 200
    body = response.json()

    assert body["recommendation"] == "HOLD"
    assert body["intrinsic_value"] is None
    assert body["discount"] is None
    assert body["reasons"] == []
    assert "could not be estimated" in body["summary"]


def test_recommendation_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/recommendation")
    assert response.status_code == 404
