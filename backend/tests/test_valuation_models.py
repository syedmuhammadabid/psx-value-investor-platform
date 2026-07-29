"""Unit tests for the pure valuation models."""

from __future__ import annotations

import math

import pytest

from app.valuation import models


class TestDiscountedCashFlow:
    def test_returns_expected_per_share_value(self) -> None:
        value = models.discounted_cash_flow(
            100.0,
            10.0,
            0.0,
            growth=0.10,
            discount_rate=0.15,
            terminal_growth=0.04,
            years=5,
        )
        assert value == pytest.approx(119.55, rel=1e-2)

    def test_missing_fcf_returns_none(self) -> None:
        assert models.discounted_cash_flow(None, 10.0, 0.0, growth=0.1) is None

    def test_non_positive_fcf_returns_none(self) -> None:
        assert models.discounted_cash_flow(-5.0, 10.0, 0.0, growth=0.1) is None

    def test_missing_shares_returns_none(self) -> None:
        assert models.discounted_cash_flow(100.0, None, 0.0, growth=0.1) is None

    def test_non_positive_shares_returns_none(self) -> None:
        assert models.discounted_cash_flow(100.0, 0.0, 0.0, growth=0.1) is None

    def test_discount_not_above_terminal_returns_none(self) -> None:
        value = models.discounted_cash_flow(
            100.0, 10.0, 0.0, growth=0.1, discount_rate=0.04, terminal_growth=0.04
        )
        assert value is None

    def test_large_net_debt_makes_equity_non_positive(self) -> None:
        assert models.discounted_cash_flow(10.0, 10.0, 1_000_000.0, growth=0.0) is None

    def test_none_growth_and_net_debt_defaults(self) -> None:
        value = models.discounted_cash_flow(100.0, 10.0, None, growth=None)
        assert value is not None and value > 0


class TestGrahamNumber:
    def test_valid(self) -> None:
        assert models.graham_number(20.0, 80.0) == pytest.approx(math.sqrt(36000.0))

    @pytest.mark.parametrize(
        ("eps", "bvps"),
        [(None, 80.0), (20.0, None), (0.0, 80.0), (20.0, -1.0)],
    )
    def test_invalid_inputs_return_none(self, eps: float | None, bvps: float | None) -> None:
        assert models.graham_number(eps, bvps) is None


class TestHistoricalPe:
    def test_valid(self) -> None:
        assert models.historical_pe_value(15.0, 10.0) == pytest.approx(150.0)

    @pytest.mark.parametrize(
        ("eps", "pe"),
        [(None, 10.0), (15.0, None), (-1.0, 10.0), (15.0, 0.0)],
    )
    def test_invalid_inputs_return_none(self, eps: float | None, pe: float | None) -> None:
        assert models.historical_pe_value(eps, pe) is None


class TestIndustryPe:
    def test_valid(self) -> None:
        assert models.industry_pe_value(20.0, 12.0) == pytest.approx(240.0)

    @pytest.mark.parametrize(
        ("eps", "pe"),
        [(None, 12.0), (20.0, None), (0.0, 12.0), (20.0, -3.0)],
    )
    def test_invalid_inputs_return_none(self, eps: float | None, pe: float | None) -> None:
        assert models.industry_pe_value(eps, pe) is None


class TestEvEbitda:
    def test_valid(self) -> None:
        assert models.ev_ebitda_value(100.0, 8.0, 50.0, 10.0) == pytest.approx(75.0)

    def test_none_net_debt_defaults_to_zero(self) -> None:
        assert models.ev_ebitda_value(100.0, 8.0, None, 10.0) == pytest.approx(80.0)

    @pytest.mark.parametrize(
        ("ebitda", "shares"),
        [(None, 10.0), (0.0, 10.0), (100.0, None), (100.0, 0.0)],
    )
    def test_invalid_inputs_return_none(self, ebitda: float | None, shares: float | None) -> None:
        assert models.ev_ebitda_value(ebitda, 8.0, 50.0, shares) is None

    def test_equity_non_positive_returns_none(self) -> None:
        assert models.ev_ebitda_value(10.0, 8.0, 1000.0, 10.0) is None


class TestResidualIncome:
    def test_valid(self) -> None:
        value = models.residual_income_value(100.0, 0.20, cost_of_equity=0.15, growth=0.05)
        assert value == pytest.approx(145.45, rel=1e-3)

    @pytest.mark.parametrize("bvps", [None, 0.0, -10.0])
    def test_invalid_bvps_returns_none(self, bvps: float | None) -> None:
        assert models.residual_income_value(bvps, 0.20) is None

    def test_missing_roe_returns_none(self) -> None:
        assert models.residual_income_value(100.0, None) is None

    def test_negative_roe_can_produce_none(self) -> None:
        value = models.residual_income_value(100.0, -5.0, cost_of_equity=0.15, growth=0.0)
        assert value is None


class TestDividendDiscount:
    def test_valid(self) -> None:
        value = models.dividend_discount_value(10.0, 0.05, discount_rate=0.15)
        assert value == pytest.approx(94.545, rel=1e-3)

    @pytest.mark.parametrize("dps", [None, 0.0, -2.0])
    def test_invalid_dps_returns_none(self, dps: float | None) -> None:
        assert models.dividend_discount_value(dps, 0.05) is None

    def test_none_growth_defaults_to_zero(self) -> None:
        value = models.dividend_discount_value(10.0, None, discount_rate=0.15)
        assert value == pytest.approx(10.0 / 0.15, rel=1e-3)


class TestWeightedIntrinsicValue:
    def test_simple_average(self) -> None:
        assert models.weighted_intrinsic_value([(100.0, 0.5), (200.0, 0.5)]) == pytest.approx(150.0)

    def test_ignores_missing_and_non_positive_and_renormalizes(self) -> None:
        value = models.weighted_intrinsic_value(
            [(100.0, 0.3), (None, 0.2), (0.0, 0.1), (200.0, 0.4)]
        )
        assert value == pytest.approx(110.0 / 0.7, rel=1e-6)

    def test_all_missing_returns_none(self) -> None:
        assert models.weighted_intrinsic_value([(None, 0.5), (-1.0, 0.5)]) is None


class TestClassifyRecommendation:
    @pytest.mark.parametrize(
        ("discount", "expected"),
        [
            (None, "HOLD"),
            (20.0, "BUY"),
            (15.0, "BUY"),
            (0.0, "HOLD"),
            (-15.0, "SELL"),
            (-30.0, "SELL"),
        ],
    )
    def test_thresholds(self, discount: float | None, expected: str) -> None:
        assert models.classify_recommendation(discount) == expected


def test_model_weights_sum_to_one() -> None:
    assert sum(models.MODEL_WEIGHTS.values()) == pytest.approx(1.0)
