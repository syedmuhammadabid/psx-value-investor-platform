"""Tests for the financial statements endpoint."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType


def _add_statement(
    db: Session,
    company: Company,
    *,
    period_type: PeriodType,
    fiscal_year: int,
    fiscal_period: str,
    period_end: date,
    revenue: str,
    net_income: str,
    operating_cash_flow: str,
    capital_expenditure: str,
) -> None:
    db.add(
        FinancialStatement(
            company=company,
            period_type=period_type,
            fiscal_year=fiscal_year,
            fiscal_period=fiscal_period,
            period_end=period_end,
            currency="PKR",
            revenue=Decimal(revenue),
            net_income=Decimal(net_income),
            operating_cash_flow=Decimal(operating_cash_flow),
            capital_expenditure=Decimal(capital_expenditure),
        )
    )


def test_financials_returns_annual_newest_first(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    company = seed_companies[0]  # MARI
    _add_statement(
        db_session,
        company,
        period_type=PeriodType.ANNUAL,
        fiscal_year=2023,
        fiscal_period="FY",
        period_end=date(2023, 6, 30),
        revenue="1000",
        net_income="200",
        operating_cash_flow="250",
        capital_expenditure="-60",
    )
    _add_statement(
        db_session,
        company,
        period_type=PeriodType.ANNUAL,
        fiscal_year=2024,
        fiscal_period="FY",
        period_end=date(2024, 6, 30),
        revenue="1200",
        net_income="260",
        operating_cash_flow="300",
        capital_expenditure="-80",
    )
    db_session.commit()

    response = client.get("/api/v1/companies/MARI/financials")
    assert response.status_code == 200

    body = response.json()
    assert body["symbol"] == "MARI"
    assert body["period_type"] == "annual"
    years = [p["fiscal_year"] for p in body["periods"]]
    assert years == [2024, 2023]  # newest first

    latest = body["periods"][0]
    assert latest["income_statement"]["revenue"] == "1200.00"
    # free_cash_flow = OCF + CapEx = 300 + (-80) = 220
    assert latest["cash_flow"]["free_cash_flow"] == "220.00"


def test_financials_period_filter(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    company = seed_companies[1]  # UBL
    _add_statement(
        db_session,
        company,
        period_type=PeriodType.ANNUAL,
        fiscal_year=2024,
        fiscal_period="FY",
        period_end=date(2024, 12, 31),
        revenue="500",
        net_income="90",
        operating_cash_flow="110",
        capital_expenditure="-20",
    )
    _add_statement(
        db_session,
        company,
        period_type=PeriodType.QUARTERLY,
        fiscal_year=2024,
        fiscal_period="Q4",
        period_end=date(2024, 12, 31),
        revenue="130",
        net_income="24",
        operating_cash_flow="28",
        capital_expenditure="-5",
    )
    db_session.commit()

    annual = client.get("/api/v1/companies/UBL/financials", params={"period": "annual"})
    assert [p["fiscal_period"] for p in annual.json()["periods"]] == ["FY"]

    quarterly = client.get("/api/v1/companies/UBL/financials", params={"period": "quarterly"})
    assert [p["fiscal_period"] for p in quarterly.json()["periods"]] == ["Q4"]


def test_financials_empty_when_none(client: TestClient, seed_companies: list[Company]) -> None:
    response = client.get("/api/v1/companies/SYS/financials")
    assert response.status_code == 200
    assert response.json()["periods"] == []


def test_financials_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/financials")
    assert response.status_code == 404
