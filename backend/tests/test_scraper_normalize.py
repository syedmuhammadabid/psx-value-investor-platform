"""Tests for unit normalization."""

from __future__ import annotations

from decimal import Decimal

import pytest

from app.models.financial_statement import PeriodType
from app.scraper import normalize
from app.scraper.normalize import NormalizationError, Scale


def test_parse_scale_defaults_to_units() -> None:
    assert normalize.parse_scale(None) is Scale.UNITS


@pytest.mark.parametrize(
    ("label", "expected"),
    [
        ("thousands", Scale.THOUSANDS),
        ("  Millions ", Scale.MILLIONS),
        ("BILLIONS", Scale.BILLIONS),
    ],
)
def test_parse_scale_accepts_known_labels(label: str, expected: Scale) -> None:
    assert normalize.parse_scale(label) is expected


def test_parse_scale_rejects_unknown() -> None:
    with pytest.raises(NormalizationError):
        normalize.parse_scale("lakhs")


def test_normalize_amount_scales_by_factor() -> None:
    assert normalize.normalize_amount(Decimal("5"), Scale.MILLIONS) == Decimal("5000000")


def test_normalize_amount_passes_through_none() -> None:
    assert normalize.normalize_amount(None, Scale.BILLIONS) is None


def test_normalize_figures_scales_only_money_fields() -> None:
    figures = {"revenue": Decimal("10"), "eps_basic": Decimal("2.5")}
    result = normalize.normalize_figures(figures, Scale.THOUSANDS)
    assert result["revenue"] == Decimal("10000")
    assert result["eps_basic"] == Decimal("2.5")


def test_canonical_fiscal_period_annual_is_fy() -> None:
    assert normalize.canonical_fiscal_period(PeriodType.ANNUAL, None) == "FY"


def test_canonical_fiscal_period_quarterly_normalizes_case() -> None:
    assert normalize.canonical_fiscal_period(PeriodType.QUARTERLY, "q3") == "Q3"


def test_canonical_fiscal_period_quarterly_requires_value() -> None:
    with pytest.raises(NormalizationError):
        normalize.canonical_fiscal_period(PeriodType.QUARTERLY, None)


def test_canonical_fiscal_period_rejects_bad_quarter() -> None:
    with pytest.raises(NormalizationError):
        normalize.canonical_fiscal_period(PeriodType.QUARTERLY, "Q5")
