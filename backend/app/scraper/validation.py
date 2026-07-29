"""Sanity checks for parsed financial records.

Financial-data errors destroy user trust, so every record is validated before it
touches the database. Checks are pure functions over a small set of figures and
return structured issues (errors block ingestion; warnings flag a record for
review but still allow it in). Thresholds are relative to guard against unit
mistakes without flagging normal rounding.
"""

from __future__ import annotations

from enum import StrEnum
from typing import NamedTuple


class Severity(StrEnum):
    """How serious a validation issue is."""

    ERROR = "error"
    WARNING = "warning"


class ValidationIssue(NamedTuple):
    """A single failed sanity check."""

    code: str
    message: str
    severity: Severity


class Figures(NamedTuple):
    """The numeric fields the sanity checks reason about (base PKR)."""

    revenue: float | None
    cost_of_revenue: float | None
    gross_profit: float | None
    operating_income: float | None
    pretax_income: float | None
    tax_expense: float | None
    net_income: float | None
    eps_basic: float | None
    shares_outstanding: float | None
    current_assets: float | None
    total_assets: float | None
    current_liabilities: float | None
    total_liabilities: float | None
    total_equity: float | None


# Relative tolerance for identity checks (2%) — absorbs rounding without hiding
# unit mistakes (which are off by factors of 1,000+).
_REL_TOL = 0.02
# A year-over-year swing beyond this fraction is flagged for manual review.
_YOY_SWING = 1.0


def _close(actual: float, expected: float) -> bool:
    return abs(actual - expected) <= _REL_TOL * max(abs(expected), 1.0)


def _accounting_equation(f: Figures) -> ValidationIssue | None:
    if f.total_assets is None or f.total_liabilities is None or f.total_equity is None:
        return None
    if _close(f.total_assets, f.total_liabilities + f.total_equity):
        return None
    return ValidationIssue(
        "accounting_equation",
        "Total assets do not equal liabilities plus equity.",
        Severity.ERROR,
    )


def _non_negative_revenue(f: Figures) -> ValidationIssue | None:
    if f.revenue is not None and f.revenue < 0:
        return ValidationIssue("negative_revenue", "Revenue is negative.", Severity.ERROR)
    return None


def _assets_within_total(f: Figures) -> ValidationIssue | None:
    if (
        f.current_assets is not None
        and f.total_assets is not None
        and f.current_assets > f.total_assets * (1 + _REL_TOL)
    ):
        return ValidationIssue(
            "current_assets_exceed_total",
            "Current assets exceed total assets.",
            Severity.ERROR,
        )
    return None


def _liabilities_within_total(f: Figures) -> ValidationIssue | None:
    if (
        f.current_liabilities is not None
        and f.total_liabilities is not None
        and f.current_liabilities > f.total_liabilities * (1 + _REL_TOL)
    ):
        return ValidationIssue(
            "current_liabilities_exceed_total",
            "Current liabilities exceed total liabilities.",
            Severity.ERROR,
        )
    return None


def _gross_profit_consistent(f: Figures) -> ValidationIssue | None:
    if f.revenue is None or f.cost_of_revenue is None or f.gross_profit is None:
        return None
    if _close(f.gross_profit, f.revenue - f.cost_of_revenue):
        return None
    return ValidationIssue(
        "gross_profit_mismatch",
        "Gross profit does not equal revenue minus cost of revenue.",
        Severity.WARNING,
    )


def _net_income_consistent(f: Figures) -> ValidationIssue | None:
    if f.pretax_income is None or f.tax_expense is None or f.net_income is None:
        return None
    if _close(f.net_income, f.pretax_income - f.tax_expense):
        return None
    return ValidationIssue(
        "net_income_mismatch",
        "Net income does not equal pretax income minus tax.",
        Severity.WARNING,
    )


def _shares_positive(f: Figures) -> ValidationIssue | None:
    if f.shares_outstanding is not None and f.shares_outstanding <= 0:
        return ValidationIssue(
            "non_positive_shares",
            "Shares outstanding is not positive.",
            Severity.WARNING,
        )
    return None


def _eps_consistent(f: Figures) -> ValidationIssue | None:
    if (
        f.eps_basic is None
        or f.net_income is None
        or f.shares_outstanding is None
        or f.shares_outstanding <= 0
    ):
        return None
    implied = f.net_income / f.shares_outstanding
    if _close(f.eps_basic, implied):
        return None
    return ValidationIssue(
        "eps_mismatch",
        "Reported EPS is inconsistent with net income over shares.",
        Severity.WARNING,
    )


_CHECKS = (
    _accounting_equation,
    _non_negative_revenue,
    _assets_within_total,
    _liabilities_within_total,
    _gross_profit_consistent,
    _net_income_consistent,
    _shares_positive,
    _eps_consistent,
)


def validate(figures: Figures) -> list[ValidationIssue]:
    """Run every single-period sanity check and return the issues found."""
    return [issue for check in _CHECKS if (issue := check(figures)) is not None]


def _yoy_swing(
    label: str, code: str, current: float | None, prior: float | None
) -> ValidationIssue | None:
    if current is None or prior is None or prior == 0:
        return None
    if abs(current - prior) / abs(prior) > _YOY_SWING:
        return ValidationIssue(
            code,
            f"{label} changed more than {_YOY_SWING:.0%} year over year.",
            Severity.WARNING,
        )
    return None


def validate_yoy(current: Figures, prior: Figures) -> list[ValidationIssue]:
    """Flag implausible year-over-year swings against the prior period."""
    candidates = (
        _yoy_swing("Revenue", "revenue_yoy_swing", current.revenue, prior.revenue),
        _yoy_swing("Net income", "net_income_yoy_swing", current.net_income, prior.net_income),
    )
    return [issue for issue in candidates if issue is not None]


def has_errors(issues: list[ValidationIssue]) -> bool:
    """Return ``True`` if any issue is error-severity (blocks ingestion)."""
    return any(issue.severity is Severity.ERROR for issue in issues)
