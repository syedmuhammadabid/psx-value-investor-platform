"""Unit normalization for parsed financial records.

PSX filings report figures in mixed units (absolute rupees, thousands, or
millions). Before anything touches the database, every monetary line item is
scaled to base PKR and fiscal periods are canonicalized. These functions are
pure and deterministic so they can be golden-file tested against known filings.
"""

from __future__ import annotations

from collections.abc import Mapping
from decimal import Decimal
from enum import StrEnum

from app.models.financial_statement import PeriodType

# Every monetary column on ``financial_statements`` plus the share count — all
# reported in the filing's scale and therefore scaled to base units. ``eps_basic``
# is a per-share figure and is deliberately excluded.
MONEY_FIELDS: frozenset[str] = frozenset(
    {
        "revenue",
        "cost_of_revenue",
        "gross_profit",
        "operating_expenses",
        "operating_income",
        "interest_expense",
        "pretax_income",
        "tax_expense",
        "net_income",
        "shares_outstanding",
        "cash_and_equivalents",
        "inventory",
        "current_assets",
        "total_assets",
        "current_liabilities",
        "total_debt",
        "total_liabilities",
        "total_equity",
        "operating_cash_flow",
        "capital_expenditure",
        "investing_cash_flow",
        "financing_cash_flow",
        "dividends_paid",
    }
)

_QUARTERS: frozenset[str] = frozenset({"Q1", "Q2", "Q3", "Q4"})


class Scale(StrEnum):
    """The unit a filing reports monetary figures in."""

    UNITS = "units"
    THOUSANDS = "thousands"
    MILLIONS = "millions"
    BILLIONS = "billions"


_SCALE_FACTORS: dict[Scale, Decimal] = {
    Scale.UNITS: Decimal(1),
    Scale.THOUSANDS: Decimal(1_000),
    Scale.MILLIONS: Decimal(1_000_000),
    Scale.BILLIONS: Decimal(1_000_000_000),
}


class NormalizationError(ValueError):
    """Raised when a record cannot be normalized (bad scale or fiscal period)."""


def parse_scale(value: str | None) -> Scale:
    """Coerce a free-text scale label to a :class:`Scale` (defaults to units)."""
    if value is None:
        return Scale.UNITS
    try:
        return Scale(value.strip().lower())
    except ValueError as exc:
        raise NormalizationError(f"Unknown scale '{value}'.") from exc


def normalize_amount(value: Decimal | None, scale: Scale) -> Decimal | None:
    """Scale a single monetary figure to base PKR."""
    if value is None:
        return None
    return value * _SCALE_FACTORS[scale]


def normalize_figures(
    figures: Mapping[str, Decimal | None], scale: Scale
) -> dict[str, Decimal | None]:
    """Return a copy of ``figures`` with monetary fields scaled to base units."""
    return {
        field: normalize_amount(value, scale) if field in MONEY_FIELDS else value
        for field, value in figures.items()
    }


def canonical_fiscal_period(period_type: PeriodType, raw: str | None) -> str:
    """Validate and canonicalize the fiscal-period label for a cadence.

    Annual periods are always ``"FY"``; quarterly periods must be ``"Q1".."Q4"``.
    """
    if period_type is PeriodType.ANNUAL:
        return "FY"
    if raw is None:
        raise NormalizationError("Quarterly records require a fiscal period (Q1-Q4).")
    candidate = raw.strip().upper()
    if candidate not in _QUARTERS:
        raise NormalizationError(f"Invalid quarterly fiscal period '{raw}'.")
    return candidate
