"""Tests for the company alerts endpoint."""

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


# Prior year: lower ROIC, less debt, lower EPS, smaller dividend.
_PRIOR = {
    "revenue": "300000000000",
    "operating_income": "200000000000",
    "net_income": "150000000000",
    "eps_basic": "20",
    "total_equity": "500000000000",
    "total_debt": "100000000000",
    "cash_and_equivalents": "20000000000",
    "shares_outstanding": "5000000000",
    "operating_cash_flow": "180000000000",
    "capital_expenditure": "-30000000000",
    "dividends_paid": "-25000000000",
}

# Latest year: higher ROIC, more debt, higher EPS, bigger dividend.
_LATEST = {
    "revenue": "420000000000",
    "operating_income": "300000000000",
    "net_income": "210000000000",
    "eps_basic": "28",
    "total_equity": "560000000000",
    "total_debt": "180000000000",
    "cash_and_equivalents": "20000000000",
    "shares_outstanding": "5000000000",
    "operating_cash_flow": "260000000000",
    "capital_expenditure": "-40000000000",
    "dividends_paid": "-40000000000",
}


def _seed_mari(db: Session, mari: Company) -> None:
    _add_annual(db, mari, fiscal_year=2024, period_end=date(2024, 6, 30), values=_LATEST)
    _add_annual(db, mari, fiscal_year=2023, period_end=date(2023, 6, 30), values=_PRIOR)
    db.commit()


def test_alerts_report_trend_signals(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    mari = seed_companies[0]  # MARI
    _seed_mari(db_session, mari)

    response = client.get("/api/v1/companies/MARI/alerts")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    assert body["currency"] == "PKR"

    types = {alert["type"] for alert in body["alerts"]}
    assert {
        "roic_improved",
        "debt_increased",
        "earnings_growth",
        "dividend_increased",
    } <= types

    for alert in body["alerts"]:
        assert alert["title"] and alert["detail"]
        assert alert["sentiment"] in {"positive", "negative", "neutral"}


def test_alerts_empty_when_no_financials(client: TestClient, seed_companies: list[Company]) -> None:
    response = client.get("/api/v1/companies/SYS/alerts")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "SYS"
    assert body["alerts"] == []


def test_alerts_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/alerts")
    assert response.status_code == 404
