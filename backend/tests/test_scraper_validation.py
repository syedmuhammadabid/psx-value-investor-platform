"""Tests for financial-record sanity checks."""

from __future__ import annotations

from app.scraper import validation
from app.scraper.validation import Figures, Severity


def _figures(**overrides: float | None) -> Figures:
    base: dict[str, float | None] = dict.fromkeys(Figures._fields)
    base.update(overrides)
    return Figures(**base)


def test_accounting_equation_passes_when_balanced() -> None:
    figures = _figures(total_assets=1000, total_liabilities=600, total_equity=400)
    assert validation.validate(figures) == []


def test_accounting_equation_flags_error_when_unbalanced() -> None:
    figures = _figures(total_assets=1000, total_liabilities=600, total_equity=200)
    codes = {issue.code for issue in validation.validate(figures)}
    assert "accounting_equation" in codes
    assert validation.has_errors(validation.validate(figures))


def test_negative_revenue_is_error() -> None:
    issues = validation.validate(_figures(revenue=-5))
    assert issues[0].severity is Severity.ERROR
    assert issues[0].code == "negative_revenue"


def test_current_assets_cannot_exceed_total() -> None:
    codes = {i.code for i in validation.validate(_figures(current_assets=900, total_assets=800))}
    assert "current_assets_exceed_total" in codes


def test_current_liabilities_cannot_exceed_total() -> None:
    figures = _figures(current_liabilities=900, total_liabilities=800)
    codes = {issue.code for issue in validation.validate(figures)}
    assert "current_liabilities_exceed_total" in codes


def test_gross_profit_mismatch_is_warning() -> None:
    figures = _figures(revenue=100, cost_of_revenue=60, gross_profit=50)
    issue = validation.validate(figures)[0]
    assert issue.code == "gross_profit_mismatch"
    assert issue.severity is Severity.WARNING
    assert not validation.has_errors([issue])


def test_net_income_mismatch_is_warning() -> None:
    figures = _figures(pretax_income=100, tax_expense=30, net_income=50)
    codes = {issue.code for issue in validation.validate(figures)}
    assert "net_income_mismatch" in codes


def test_non_positive_shares_is_warning() -> None:
    codes = {issue.code for issue in validation.validate(_figures(shares_outstanding=0))}
    assert "non_positive_shares" in codes


def test_eps_mismatch_is_warning() -> None:
    figures = _figures(eps_basic=10, net_income=100, shares_outstanding=100)
    codes = {issue.code for issue in validation.validate(figures)}
    assert "eps_mismatch" in codes


def test_eps_consistent_passes() -> None:
    figures = _figures(eps_basic=1, net_income=100, shares_outstanding=100)
    assert validation.validate(figures) == []


def test_validate_yoy_flags_large_swings() -> None:
    current = _figures(revenue=300, net_income=200)
    prior = _figures(revenue=100, net_income=50)
    codes = {issue.code for issue in validation.validate_yoy(current, prior)}
    assert codes == {"revenue_yoy_swing", "net_income_yoy_swing"}


def test_validate_yoy_ignores_modest_change() -> None:
    current = _figures(revenue=110, net_income=55)
    prior = _figures(revenue=100, net_income=50)
    assert validation.validate_yoy(current, prior) == []


def test_has_errors_false_for_warnings_only() -> None:
    issues = validation.validate(_figures(shares_outstanding=-1))
    assert issues
    assert not validation.has_errors(issues)
