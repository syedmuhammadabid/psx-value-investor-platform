"""Tests for the pure investment-scoring functions."""

from __future__ import annotations

import pytest

from app.scores import scorecard
from app.scores.scorecard import PeriodInputs


class TestRating:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [
            (100.0, "excellent"),
            (80.0, "excellent"),
            (79.9, "good"),
            (60.0, "good"),
            (40.0, "fair"),
            (39.9, "weak"),
            (0.0, "weak"),
            (None, "na"),
        ],
    )
    def test_rating_bands(self, value: float | None, expected: str) -> None:
        assert scorecard.rating(value) == expected


class TestComposites:
    def test_financial_health_all_pass(self) -> None:
        result = scorecard.financial_health(
            debt_to_equity=0.3,
            free_cash_flow=1000.0,
            net_margin=12.0,
            revenue_cagr=10.0,
            current_ratio=2.0,
        )
        assert result.value == 100.0
        assert result.rating == "excellent"
        assert all(c.passed for c in result.checks)

    def test_financial_health_mixed(self) -> None:
        result = scorecard.financial_health(
            debt_to_equity=2.0,  # fail
            free_cash_flow=-500.0,  # fail
            net_margin=12.0,  # pass
            revenue_cagr=10.0,  # pass
            current_ratio=2.0,  # pass
        )
        assert result.value == 60.0
        assert result.rating == "good"

    def test_all_missing_is_na(self) -> None:
        result = scorecard.buffett(
            roe=None,
            roic=None,
            debt_to_equity=None,
            eps_cagr=None,
            dividend_yield=None,
            free_cash_flow=None,
        )
        assert result.value is None
        assert result.rating == "na"
        assert all(c.passed is None for c in result.checks)

    def test_partial_data_scores_on_evaluable_only(self) -> None:
        # Only two checks have data; one passes, one fails -> 50.
        result = scorecard.graham(
            pe=10.0,  # pass
            pb=3.0,  # fail
            debt_to_equity=None,
            current_ratio=None,
            net_income=None,
        )
        assert result.value == 50.0

    def test_quality_all_pass(self) -> None:
        result = scorecard.quality(
            roic=18.0,
            eps_cagr=10.0,
            free_cash_flow=1000.0,
            debt_to_equity=0.3,
            pe=12.0,
        )
        assert result.value == 100.0


_STRONG_CURRENT = PeriodInputs(
    net_income=210.0,
    total_assets=1000.0,
    operating_cash_flow=260.0,
    total_debt=180.0,
    current_assets=300.0,
    current_liabilities=150.0,
    shares_outstanding=5000.0,
    gross_profit=250.0,
    revenue=420.0,
)
_WEAK_PRIOR = PeriodInputs(
    net_income=150.0,
    total_assets=1000.0,
    operating_cash_flow=180.0,
    total_debt=200.0,
    current_assets=250.0,
    current_liabilities=150.0,
    shares_outstanding=5000.0,
    gross_profit=180.0,
    revenue=380.0,
)
_EMPTY_PERIOD = PeriodInputs(*([None] * 9))


class TestPiotroski:
    def test_perfect_score(self) -> None:
        result = scorecard.piotroski(_STRONG_CURRENT, _WEAK_PRIOR)
        assert result.value == 9
        assert result.rating == "strong"
        assert len(result.checks) == 9

    def test_all_missing_is_na(self) -> None:
        result = scorecard.piotroski(_EMPTY_PERIOD, _EMPTY_PERIOD)
        assert result.value is None
        assert result.rating == "na"

    def test_declining_business_scores_low(self) -> None:
        # Swap the periods so every trend check declines.
        result = scorecard.piotroski(_WEAK_PRIOR, _STRONG_CURRENT)
        assert result.value is not None
        assert result.value <= scorecard._F_MODERATE
        assert result.rating in {"weak", "moderate"}


class TestAltman:
    def test_safe_zone(self) -> None:
        result = scorecard.altman_z(
            current_assets=600.0,
            current_liabilities=200.0,
            total_assets=1000.0,
            retained_earnings=500.0,
            total_liabilities=400.0,
            operating_income=300.0,
            revenue=1200.0,
            market_cap=2000.0,
        )
        assert result.value is not None
        assert result.value > scorecard._Z_SAFE
        assert result.band == "safe"

    def test_grey_zone(self) -> None:
        result = scorecard.altman_z(
            current_assets=400.0,
            current_liabilities=200.0,
            total_assets=1000.0,
            retained_earnings=200.0,
            total_liabilities=500.0,
            operating_income=100.0,
            revenue=800.0,
            market_cap=500.0,
        )
        assert result.band == "grey"

    def test_distress_zone(self) -> None:
        result = scorecard.altman_z(
            current_assets=100.0,
            current_liabilities=400.0,
            total_assets=1000.0,
            retained_earnings=-200.0,
            total_liabilities=900.0,
            operating_income=10.0,
            revenue=200.0,
            market_cap=100.0,
        )
        assert result.band == "distress"

    def test_missing_data_is_na(self) -> None:
        result = scorecard.altman_z(
            current_assets=None,
            current_liabilities=200.0,
            total_assets=1000.0,
            retained_earnings=500.0,
            total_liabilities=400.0,
            operating_income=300.0,
            revenue=1200.0,
            market_cap=2000.0,
        )
        assert result.value is None
        assert result.band == "na"


class TestMagicFormula:
    def test_computes_earnings_yield(self) -> None:
        result = scorecard.magic_formula(roic=15.0, operating_income=300.0, enterprise_value=1500.0)
        assert result.roic == 15.0
        assert result.earnings_yield == 20.0

    def test_missing_enterprise_value(self) -> None:
        result = scorecard.magic_formula(roic=15.0, operating_income=300.0, enterprise_value=None)
        assert result.earnings_yield is None
        assert result.roic == 15.0
