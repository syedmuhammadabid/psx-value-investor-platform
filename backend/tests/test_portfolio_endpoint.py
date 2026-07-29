"""Tests for the stateless portfolio analysis endpoint."""

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


def _seed_mari(db: Session, company: Company) -> None:
    _add_annual(db, company, fiscal_year=2024, period_end=date(2024, 6, 30), values=_LATEST)
    _add_annual(db, company, fiscal_year=2023, period_end=date(2023, 6, 30), values=_PRIOR)
    db.commit()


def test_analyze_single_holding(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    mari = seed_companies[0]  # MARI, current price 620.50
    _seed_mari(db_session, mari)

    response = client.post(
        "/api/v1/portfolio/analyze",
        json={"holdings": [{"symbol": "MARI", "quantity": 100, "average_cost": 500}]},
    )
    assert response.status_code == 200
    body = response.json()

    assert body["currency"] == "PKR"
    summary = body["summary"]
    assert summary["holdings_count"] == 1
    assert summary["total_cost"] == 50000.0
    assert summary["total_market_value"] == 62050.0  # 100 * 620.50
    assert summary["total_gain_loss"] == 12050.0
    assert summary["total_gain_loss_pct"] > 0

    holding = body["holdings"][0]
    assert holding["symbol"] == "MARI"
    assert holding["name"] is not None
    assert holding["cost_basis"] == 50000.0
    assert holding["market_value"] == 62050.0
    assert holding["weight"] == 100.0
    assert holding["recommendation"] in {"BUY", "HOLD", "SELL"}


def test_analyze_multiple_holdings_scores_and_weights(
    client: TestClient, db_session: Session, seed_companies: list[Company]
) -> None:
    mari, ubl = seed_companies[0], seed_companies[1]
    _seed_mari(db_session, mari)
    _add_annual(db_session, ubl, fiscal_year=2024, period_end=date(2024, 12, 31), values=_LATEST)
    _add_annual(db_session, ubl, fiscal_year=2023, period_end=date(2023, 12, 31), values=_PRIOR)
    db_session.commit()

    response = client.post(
        "/api/v1/portfolio/analyze",
        json={
            "holdings": [
                {"symbol": "MARI", "quantity": 100, "average_cost": 500},
                {"symbol": "UBL", "quantity": 200, "average_cost": 300},
            ]
        },
    )
    assert response.status_code == 200
    body = response.json()

    summary = body["summary"]
    assert summary["holdings_count"] == 2
    assert summary["health_score"] is not None
    assert 0 <= summary["health_score"] <= 100

    weights = [h["weight"] for h in body["holdings"]]
    assert all(w is not None for w in weights)
    assert sum(weights) == pytest.approx(100.0)  # weights are percents of market value


def test_analyze_holding_without_financials_still_values_position(
    client: TestClient, seed_companies: list[Company]
) -> None:
    # SYS has a price but no financials -> no intrinsic value, but gain/loss still computes.
    response = client.post(
        "/api/v1/portfolio/analyze",
        json={"holdings": [{"symbol": "SYS", "quantity": 10, "average_cost": 900}]},
    )
    assert response.status_code == 200
    body = response.json()

    holding = body["holdings"][0]
    assert holding["market_value"] == 9850.0  # 10 * 985.00
    assert holding["intrinsic_value"] is None
    assert holding["margin_of_safety"] is None
    assert holding["expected_cagr"] is None
    assert body["summary"]["total_intrinsic_value"] is None


def test_analyze_unknown_symbol_404(client: TestClient) -> None:
    response = client.post(
        "/api/v1/portfolio/analyze",
        json={"holdings": [{"symbol": "NOPE", "quantity": 1, "average_cost": 10}]},
    )
    assert response.status_code == 404


def test_analyze_rejects_invalid_quantity(client: TestClient) -> None:
    response = client.post(
        "/api/v1/portfolio/analyze",
        json={"holdings": [{"symbol": "MARI", "quantity": 0, "average_cost": 500}]},
    )
    assert response.status_code == 422


def test_analyze_rejects_empty_portfolio(client: TestClient) -> None:
    response = client.post("/api/v1/portfolio/analyze", json={"holdings": []})
    assert response.status_code == 422
