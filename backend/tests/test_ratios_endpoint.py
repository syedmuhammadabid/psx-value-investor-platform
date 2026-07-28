"""Tests for the financial ratios endpoint."""

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


_PRIOR = {
    "revenue": "1000",
    "gross_profit": "400",
    "operating_income": "250",
    "interest_expense": "25",
    "pretax_income": "200",
    "tax_expense": "60",
    "net_income": "150",
    "eps_basic": "10",
    "total_equity": "600",
    "total_assets": "1500",
    "total_debt": "300",
    "cash_and_equivalents": "100",
    "current_assets": "600",
    "current_liabilities": "300",
    "inventory": "200",
    "operating_cash_flow": "300",
    "capital_expenditure": "-80",
    "dividends_paid": "-50",
}

_LATEST = {
    "revenue": "1200",
    "gross_profit": "480",
    "operating_income": "300",
    "interest_expense": "30",
    "pretax_income": "240",
    "tax_expense": "72",
    "net_income": "168",
    "eps_basic": "12",
    "total_equity": "700",
    "total_assets": "1700",
    "total_debt": "320",
    "cash_and_equivalents": "120",
    "current_assets": "700",
    "current_liabilities": "320",
    "inventory": "220",
    "operating_cash_flow": "360",
    "capital_expenditure": "-90",
    "dividends_paid": "-60",
}


def test_ratios_computed_from_latest_period(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    company = seed_companies[0]  # MARI, market_cap 2.6e12
    company.dividend_yield = Decimal("2.10")
    _add_annual(db_session, company, fiscal_year=2023, period_end=date(2023, 6, 30), values=_PRIOR)
    _add_annual(db_session, company, fiscal_year=2024, period_end=date(2024, 6, 30), values=_LATEST)
    db_session.commit()

    response = client.get("/api/v1/companies/MARI/ratios")
    assert response.status_code == 200
    body = response.json()

    assert body["symbol"] == "MARI"
    assert body["fiscal_year"] == 2024
    assert body["fiscal_period"] == "FY"

    prof = body["profitability"]
    assert prof["gross_margin"] == pytest.approx(40.0)
    assert prof["operating_margin"] == pytest.approx(25.0)
    assert prof["net_margin"] == pytest.approx(14.0)
    assert prof["roe"] == pytest.approx(24.0)
    assert prof["roa"] == pytest.approx(168 / 1700 * 100)
    # NOPAT = 300 * (1 - 72/240) = 210; capital = 320 + 700 - 120 = 900.
    assert prof["roic"] == pytest.approx(210 / 900 * 100)

    val = body["valuation"]
    assert val["pe"] == pytest.approx(2_600_000_000_000 / 168)
    assert val["dividend_yield"] == pytest.approx(2.10)
    assert val["peg"] is not None and val["peg"] > 0

    debt = body["debt"]
    assert debt["debt_to_equity"] == pytest.approx(320 / 700)
    assert debt["interest_coverage"] == pytest.approx(10.0)

    liq = body["liquidity"]
    assert liq["current_ratio"] == pytest.approx(700 / 320)
    assert liq["quick_ratio"] == pytest.approx((700 - 220) / 320)

    cash = body["cash_flow"]
    assert cash["free_cash_flow"] == pytest.approx(270.0)
    assert cash["fcf_yield"] == pytest.approx(270 / 2_600_000_000_000 * 100)

    growth = body["growth"]
    assert growth["years"] == 1
    assert growth["revenue_cagr"] == pytest.approx(20.0)
    assert growth["eps_cagr"] == pytest.approx(20.0)
    assert growth["dividend_cagr"] == pytest.approx(20.0)


def test_ratios_empty_when_no_financials(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    company = seed_companies[1]  # UBL
    company.dividend_yield = Decimal("8.50")
    db_session.commit()

    response = client.get("/api/v1/companies/UBL/ratios")
    assert response.status_code == 200
    body = response.json()

    assert body["fiscal_year"] is None
    assert body["profitability"]["roe"] is None
    # Dividend yield comes from the company profile, not the statements.
    assert body["valuation"]["dividend_yield"] == pytest.approx(8.50)
    assert body["growth"]["years"] == 0


def test_ratios_unknown_company_404(client: TestClient) -> None:
    response = client.get("/api/v1/companies/NOPE/ratios")
    assert response.status_code == 404
