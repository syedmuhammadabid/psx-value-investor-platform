"""Tests for the company history (chart series) endpoint."""

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


_OLDER = {
    "revenue": "1000",
    "operating_income": "250",
    "pretax_income": "200",
    "tax_expense": "60",
    "net_income": "150",
    "eps_basic": "10",
    "total_equity": "600",
    "total_debt": "300",
    "cash_and_equivalents": "100",
    "shares_outstanding": "15",
    "operating_cash_flow": "300",
    "capital_expenditure": "-80",
    "dividends_paid": "-45",
}

_NEWER = {
    "revenue": "1200",
    "operating_income": "300",
    "pretax_income": "240",
    "tax_expense": "72",
    "net_income": "168",
    "eps_basic": "12",
    "total_equity": "700",
    "total_debt": "320",
    "cash_and_equivalents": "120",
    "shares_outstanding": "14",
    "operating_cash_flow": "360",
    "capital_expenditure": "-90",
    "dividends_paid": "-56",
}


def test_history_returns_oldest_first_with_metrics(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    company = seed_companies[0]  # MARI
    _add_annual(db_session, company, fiscal_year=2024, period_end=date(2024, 6, 30), values=_NEWER)
    _add_annual(db_session, company, fiscal_year=2023, period_end=date(2023, 6, 30), values=_OLDER)
    db_session.commit()

    response = client.get("/api/v1/companies/MARI/history")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    years = [p["fiscal_year"] for p in body["points"]]
    assert years == [2023, 2024]  # oldest first

    newer = body["points"][1]
    assert newer["revenue"] == pytest.approx(1200.0)
    assert newer["net_income"] == pytest.approx(168.0)
    assert newer["eps"] == pytest.approx(12.0)
    assert newer["roe"] == pytest.approx(168 / 700 * 100)
    # ROIC: NOPAT = 300 * (1 - 72/240) = 210; capital = 320 + 700 - 120 = 900.
    assert newer["roic"] == pytest.approx(210 / 900 * 100)
    # BVPS = 700 / 14; DPS = 56 / 14; FCF = 360 - 90.
    assert newer["book_value_per_share"] == pytest.approx(50.0)
    assert newer["dividend_per_share"] == pytest.approx(4.0)
    assert newer["free_cash_flow"] == pytest.approx(270.0)


def test_history_empty_when_no_financials(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.get("/api/v1/companies/SYS/history")
    assert response.status_code == 200
    assert response.json()["points"] == []


def test_history_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/history")
    assert response.status_code == 404
