"""Tests for the stock screener endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
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


# A high-quality company: strong ROE/ROIC, low debt, growing revenue, positive FCF.
_STRONG_LATEST = {
    "revenue": "520000000000",
    "net_income": "300000000000",
    "operating_income": "400000000000",
    "pretax_income": "350000000000",
    "tax_expense": "100000000000",
    "total_equity": "800000000000",
    "total_debt": "200000000000",
    "cash_and_equivalents": "50000000000",
    "operating_cash_flow": "350000000000",
    "capital_expenditure": "-60000000000",
}
_STRONG_PRIOR = {"revenue": "400000000000"}

# A weak company: low ROE, high debt, shrinking revenue, negative FCF.
_WEAK_LATEST = {
    "revenue": "280000000000",
    "net_income": "50000000000",
    "operating_income": "60000000000",
    "pretax_income": "55000000000",
    "tax_expense": "15000000000",
    "total_equity": "1000000000000",
    "total_debt": "900000000000",
    "cash_and_equivalents": "20000000000",
    "operating_cash_flow": "20000000000",
    "capital_expenditure": "-40000000000",
}
_WEAK_PRIOR = {"revenue": "300000000000"}


@pytest.fixture
def screened_companies(db_session: Session, seed_companies: list[Company]) -> list[Company]:
    mari, ubl, _sys, _old = seed_companies
    _add_annual(
        db_session, mari, fiscal_year=2024, period_end=date(2024, 6, 30), values=_STRONG_LATEST
    )
    _add_annual(
        db_session, mari, fiscal_year=2023, period_end=date(2023, 6, 30), values=_STRONG_PRIOR
    )
    _add_annual(
        db_session, ubl, fiscal_year=2024, period_end=date(2024, 12, 31), values=_WEAK_LATEST
    )
    _add_annual(
        db_session, ubl, fiscal_year=2023, period_end=date(2023, 12, 31), values=_WEAK_PRIOR
    )
    db_session.commit()
    return seed_companies


def test_screener_no_filters_returns_active_companies(
    client: TestClient, screened_companies: list[Company]
) -> None:
    response = client.get("/api/v1/screener")
    assert response.status_code == 200
    body = response.json()

    # Three active companies (the inactive OLDCO is excluded), largest cap first.
    assert body["count"] == 3
    symbols = [row["symbol"] for row in body["items"]]
    assert symbols == ["MARI", "UBL", "SYS"]


def test_screener_min_roe_filters_out_weak_names(
    client: TestClient, screened_companies: list[Company]
) -> None:
    response = client.get("/api/v1/screener", params={"min_roe": 20})
    assert response.status_code == 200
    body = response.json()

    assert body["count"] == 1
    row = body["items"][0]
    assert row["symbol"] == "MARI"
    assert row["roe"] == pytest.approx(300 / 800 * 100)


def test_screener_value_rules_combine_with_and(
    client: TestClient, screened_companies: list[Company]
) -> None:
    response = client.get(
        "/api/v1/screener",
        params={
            "min_roe": 20,
            "min_roic": 15,
            "max_pe": 10,
            "max_debt_to_equity": 0.5,
            "min_revenue_growth": 10,
            "positive_fcf": "true",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert [row["symbol"] for row in body["items"]] == ["MARI"]


def test_screener_positive_fcf_excludes_negative_and_missing(
    client: TestClient, screened_companies: list[Company]
) -> None:
    response = client.get("/api/v1/screener", params={"positive_fcf": "true"})
    assert response.status_code == 200
    # MARI has positive FCF; UBL is negative; SYS has no financials.
    assert [row["symbol"] for row in response.json()["items"]] == ["MARI"]


def test_screener_sector_filter(client: TestClient, screened_companies: list[Company]) -> None:
    response = client.get("/api/v1/screener", params={"sector": "Energy"})
    assert response.status_code == 200
    assert [row["symbol"] for row in response.json()["items"]] == ["MARI"]
