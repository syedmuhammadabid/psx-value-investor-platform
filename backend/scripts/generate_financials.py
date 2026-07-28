"""Deterministic synthetic financials generator for development seed data.

Given a company's headline figures, produces internally-consistent annual and
quarterly statements with realistic-looking trends. Output is illustrative only
and must never be used for real analysis. Deterministic per symbol so repeated
seeding yields stable numbers.
"""

from __future__ import annotations

import calendar
import random
from datetime import date
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

_MONTHS = {
    "january": 1,
    "february": 2,
    "march": 3,
    "april": 4,
    "may": 5,
    "june": 6,
    "july": 7,
    "august": 8,
    "september": 9,
    "october": 10,
    "november": 11,
    "december": 12,
}

_LATEST_FISCAL_YEAR = 2025


def _money(value: float) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _ratio(value: float, places: str = "0.0001") -> Decimal:
    return Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _fiscal_end_month(fiscal_year_end: str | None) -> int:
    if not fiscal_year_end:
        return 12
    return _MONTHS.get(fiscal_year_end.strip().lower(), 12)


def _last_day(year: int, month: int) -> date:
    return date(year, month, calendar.monthrange(year, month)[1])


def _add_months(anchor: date, months: int) -> date:
    total = (anchor.year * 12 + (anchor.month - 1)) + months
    year, month = divmod(total, 12)
    return _last_day(year, month + 1)


def _period_fields(
    *,
    revenue: float,
    rng: random.Random,
    shares: float,
    margins: dict[str, float],
) -> dict[str, Any]:
    """Derive a full statement from a revenue figure and stable margins."""
    gross_profit = revenue * margins["gross"]
    cost_of_revenue = revenue - gross_profit
    operating_income = revenue * margins["operating"]
    operating_expenses = gross_profit - operating_income
    interest_expense = revenue * margins["interest"]
    pretax_income = operating_income - interest_expense
    tax_expense = pretax_income * margins["tax"]
    net_income = pretax_income - tax_expense

    total_assets = revenue * margins["asset_turnover"]
    total_equity = total_assets * margins["equity"]
    total_liabilities = total_assets - total_equity
    total_debt = total_assets * margins["debt"]
    current_assets = total_assets * margins["current_assets"]
    current_liabilities = total_assets * margins["current_liabilities"]
    cash = current_assets * margins["cash"]
    inventory = current_assets * margins["inventory"]

    operating_cash_flow = net_income * margins["ocf"]
    capital_expenditure = -(revenue * margins["capex"])
    investing_cash_flow = capital_expenditure * (1 + rng.uniform(0.05, 0.25))
    dividends_paid = -(net_income * margins["payout"])
    financing_cash_flow = dividends_paid * (1 + rng.uniform(0.1, 0.4))

    return {
        "revenue": _money(revenue),
        "cost_of_revenue": _money(cost_of_revenue),
        "gross_profit": _money(gross_profit),
        "operating_expenses": _money(operating_expenses),
        "operating_income": _money(operating_income),
        "interest_expense": _money(interest_expense),
        "pretax_income": _money(pretax_income),
        "tax_expense": _money(tax_expense),
        "net_income": _money(net_income),
        "eps_basic": _ratio(net_income / shares if shares else 0.0),
        "shares_outstanding": _money(shares),
        "cash_and_equivalents": _money(cash),
        "inventory": _money(inventory),
        "current_assets": _money(current_assets),
        "total_assets": _money(total_assets),
        "current_liabilities": _money(current_liabilities),
        "total_debt": _money(total_debt),
        "total_liabilities": _money(total_liabilities),
        "total_equity": _money(total_equity),
        "operating_cash_flow": _money(operating_cash_flow),
        "capital_expenditure": _money(capital_expenditure),
        "investing_cash_flow": _money(investing_cash_flow),
        "financing_cash_flow": _money(financing_cash_flow),
        "dividends_paid": _money(dividends_paid),
    }


def generate_financials(
    *,
    symbol: str,
    market_cap: float | None,
    current_price: float | None,
    fiscal_year_end: str | None,
    annual_years: int = 10,
    quarters: int = 8,
) -> list[dict[str, Any]]:
    """Return a list of statement dicts (annual + quarterly) for a company."""
    if not market_cap:
        return []

    rng = random.Random(f"psx::{symbol}")
    shares = (market_cap / current_price) if current_price else market_cap / 100.0

    margins = {
        "gross": rng.uniform(0.28, 0.55),
        "operating": rng.uniform(0.14, 0.30),
        "interest": rng.uniform(0.01, 0.05),
        "tax": rng.uniform(0.24, 0.31),
        "asset_turnover": rng.uniform(1.3, 2.6),
        "equity": rng.uniform(0.38, 0.60),
        "debt": rng.uniform(0.12, 0.34),
        "current_assets": rng.uniform(0.35, 0.50),
        "current_liabilities": rng.uniform(0.20, 0.32),
        "cash": rng.uniform(0.18, 0.35),
        "inventory": rng.uniform(0.20, 0.38),
        "ocf": rng.uniform(1.05, 1.45),
        "capex": rng.uniform(0.05, 0.12),
        "payout": rng.uniform(0.20, 0.55),
    }

    end_month = _fiscal_end_month(fiscal_year_end)
    latest_revenue = market_cap * rng.uniform(0.45, 1.15)
    growth = rng.uniform(0.06, 0.17)

    statements: list[dict[str, Any]] = []

    # Annual statements, newest to oldest.
    for offset in range(annual_years):
        fiscal_year = _LATEST_FISCAL_YEAR - offset
        revenue = latest_revenue / ((1 + growth) ** offset)
        statements.append(
            {
                "period_type": "annual",
                "fiscal_year": fiscal_year,
                "fiscal_period": "FY",
                "period_end": _last_day(fiscal_year, end_month),
                "currency": "PKR",
                **_period_fields(revenue=revenue, rng=rng, shares=shares, margins=margins),
            }
        )

    # Quarterly statements for the most recent quarters.
    seasonality = [0.22, 0.24, 0.26, 0.28]
    for offset in range(quarters):
        year_offset, quarter_idx = divmod(offset, 4)
        fiscal_year = _LATEST_FISCAL_YEAR - year_offset
        annual_revenue = latest_revenue / ((1 + growth) ** year_offset)
        quarter_number = 4 - quarter_idx  # Q4 newest within a fiscal year
        revenue = annual_revenue * seasonality[quarter_number - 1]
        months_before_year_end = (4 - quarter_number) * 3
        period_end = _add_months(_last_day(fiscal_year, end_month), -months_before_year_end)
        statements.append(
            {
                "period_type": "quarterly",
                "fiscal_year": fiscal_year,
                "fiscal_period": f"Q{quarter_number}",
                "period_end": period_end,
                "currency": "PKR",
                **_period_fields(revenue=revenue, rng=rng, shares=shares, margins=margins),
            }
        )

    return statements
