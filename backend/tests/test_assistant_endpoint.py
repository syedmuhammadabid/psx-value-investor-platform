"""Tests for the company AI assistant endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType

_ANNUAL = {
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
    "interest_expense": "12000000000",
    "pretax_income": "250000000000",
    "tax_expense": "40000000000",
    "current_assets": "300000000000",
    "current_liabilities": "150000000000",
}


def _seed_mari(db: Session, mari: Company) -> None:
    for fiscal_year, period_end in ((2024, date(2024, 6, 30)), (2023, date(2023, 6, 30))):
        db.add(
            FinancialStatement(
                company=mari,
                period_type=PeriodType.ANNUAL,
                fiscal_year=fiscal_year,
                fiscal_period="FY",
                period_end=period_end,
                currency="PKR",
                **{key: Decimal(value) for key, value in _ANNUAL.items()},
            )
        )
    db.commit()


def test_assistant_answers_buy_question(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    _seed_mari(db_session, seed_companies[0])

    response = client.post(
        "/api/v1/companies/MARI/assistant",
        json={"question": "Should I buy MARI?"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    assert body["question"] == "Should I buy MARI?"
    assert body["intent"] == "verdict"
    assert body["answer"]
    assert body["highlights"]
    assert body["recommendation"] in {"BUY", "HOLD", "SELL"}
    assert "not financial advice" in body["disclaimer"].lower()


def test_assistant_routes_intent(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    _seed_mari(db_session, seed_companies[0])

    response = client.post(
        "/api/v1/companies/MARI/assistant",
        json={"question": "How fast is revenue growing?"},
    )
    assert response.status_code == 200
    assert response.json()["intent"] == "growth"


def test_assistant_handles_company_without_financials(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.post(
        "/api/v1/companies/SYS/assistant",
        json={"question": "Is it undervalued?"},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "SYS"
    assert body["intent"] == "valuation"
    assert "n/a" in body["answer"] or "could not be estimated" in body["answer"]


def test_assistant_rejects_blank_question(
    client: TestClient, seed_companies: list[Company]
) -> None:
    response = client.post(
        "/api/v1/companies/MARI/assistant",
        json={"question": ""},
    )
    assert response.status_code == 422


def test_assistant_unknown_company_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/companies/NOPE/assistant",
        json={"question": "Should I buy?"},
    )
    assert response.status_code == 404
