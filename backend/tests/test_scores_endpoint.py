"""Tests for the company scores endpoint."""

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
    "revenue": "300000000000",
    "gross_profit": "150000000000",
    "operating_income": "200000000000",
    "net_income": "150000000000",
    "eps_basic": "20",
    "total_assets": "800000000000",
    "current_assets": "250000000000",
    "current_liabilities": "150000000000",
    "total_equity": "500000000000",
    "total_debt": "100000000000",
    "total_liabilities": "300000000000",
    "cash_and_equivalents": "20000000000",
    "shares_outstanding": "5000000000",
    "operating_cash_flow": "180000000000",
    "capital_expenditure": "-30000000000",
    "dividends_paid": "-25000000000",
}

_LATEST = {
    "revenue": "420000000000",
    "gross_profit": "250000000000",
    "operating_income": "300000000000",
    "net_income": "210000000000",
    "eps_basic": "28",
    "total_assets": "1000000000000",
    "current_assets": "300000000000",
    "current_liabilities": "150000000000",
    "total_equity": "560000000000",
    "total_debt": "180000000000",
    "total_liabilities": "440000000000",
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


def _company(seed_companies: list[Company], symbol: str) -> Company:
    return next(c for c in seed_companies if c.symbol == symbol)


class TestScoresEndpoint:
    def test_full_scorecard(
        self, client: TestClient, db_session: Session, seed_companies: list[Company]
    ) -> None:
        _seed_mari(db_session, _company(seed_companies, "MARI"))

        response = client.get("/api/v1/companies/MARI/scores")

        assert response.status_code == 200
        body = response.json()
        assert body["symbol"] == "MARI"
        assert body["currency"] == "PKR"

        keys = {c["key"] for c in body["composites"]}
        assert keys == {"financial_health", "buffett", "graham", "quality"}
        for composite in body["composites"]:
            assert composite["value"] is not None
            assert composite["rating"] != "na"
            assert composite["checks"]

        piotroski = body["piotroski"]
        assert piotroski["max_score"] == 9
        assert 0 <= piotroski["value"] <= 9
        assert len(piotroski["checks"]) == 9

        assert body["altman_z"]["band"] in {"safe", "grey", "distress"}
        assert body["magic_formula"]["earnings_yield"] is not None

    def test_company_without_financials(
        self, client: TestClient, seed_companies: list[Company]
    ) -> None:
        response = client.get("/api/v1/companies/SYS/scores")

        assert response.status_code == 200
        body = response.json()
        assert body["piotroski"]["value"] is None
        assert body["piotroski"]["rating"] == "na"
        assert body["altman_z"]["band"] == "na"
        assert len(body["composites"]) == 4

    def test_case_insensitive_symbol(
        self, client: TestClient, db_session: Session, seed_companies: list[Company]
    ) -> None:
        _seed_mari(db_session, _company(seed_companies, "MARI"))

        response = client.get("/api/v1/companies/mari/scores")

        assert response.status_code == 200
        assert response.json()["symbol"] == "MARI"

    def test_unknown_symbol_returns_404(
        self, client: TestClient, seed_companies: list[Company]
    ) -> None:
        response = client.get("/api/v1/companies/NOPE/scores")

        assert response.status_code == 404
