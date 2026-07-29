"""Unit tests for the pure portfolio analytics math."""

from __future__ import annotations

import math

import pytest

from app.calculations import portfolio as calc


class TestMarginOfSafety:
    def test_undervalued_is_positive(self) -> None:
        assert calc.margin_of_safety(400.0, 300.0) == pytest.approx(25.0)

    def test_overvalued_is_negative(self) -> None:
        assert calc.margin_of_safety(300.0, 360.0) == pytest.approx(-20.0)

    @pytest.mark.parametrize("intrinsic", [None, 0.0, -10.0])
    def test_no_intrinsic_returns_none(self, intrinsic: float | None) -> None:
        assert calc.margin_of_safety(intrinsic, 100.0) is None

    def test_no_price_returns_none(self) -> None:
        assert calc.margin_of_safety(400.0, None) is None


class TestExpectedCagr:
    def test_converging_up(self) -> None:
        # Doubling over 5 years ≈ 14.87% CAGR.
        assert calc.expected_cagr(200.0, 100.0, years=5) == pytest.approx(14.8698, abs=1e-3)

    def test_fairly_valued_is_zero(self) -> None:
        assert calc.expected_cagr(100.0, 100.0) == pytest.approx(0.0)

    @pytest.mark.parametrize(
        ("intrinsic", "price", "years"),
        [(None, 100.0, 5), (100.0, None, 5), (0.0, 100.0, 5), (100.0, 0.0, 5), (100.0, 50.0, 0)],
    )
    def test_invalid_inputs_return_none(
        self, intrinsic: float | None, price: float | None, years: int
    ) -> None:
        assert calc.expected_cagr(intrinsic, price, years=years) is None


class TestValuationScore:
    @pytest.mark.parametrize(
        ("mos", "expected"),
        [(25.0, 100.0), (-25.0, 0.0), (0.0, 50.0), (12.5, 75.0), (100.0, 100.0), (-100.0, 0.0)],
    )
    def test_maps_mos_to_score(self, mos: float, expected: float) -> None:
        assert calc.valuation_score(mos) == pytest.approx(expected)

    def test_none_returns_none(self) -> None:
        assert calc.valuation_score(None) is None


class TestDiversification:
    def test_herfindahl_of_equal_weights(self) -> None:
        assert calc.herfindahl([0.5, 0.5]) == pytest.approx(0.5)

    def test_empty_returns_none(self) -> None:
        assert calc.diversification_score([]) is None

    def test_single_holding_is_zero(self) -> None:
        assert calc.diversification_score([1.0]) == 0.0

    def test_equal_weights_is_full_score(self) -> None:
        assert calc.diversification_score([0.25, 0.25, 0.25, 0.25]) == pytest.approx(100.0)

    def test_concentration_lowers_score(self) -> None:
        score = calc.diversification_score([0.9, 0.05, 0.05])
        assert score is not None
        assert 0.0 < score < 100.0


class TestWeightedAverage:
    def test_basic(self) -> None:
        assert calc.weighted_average([(10.0, 1.0), (20.0, 3.0)]) == pytest.approx(17.5)

    def test_skips_none_values_and_zero_weights(self) -> None:
        assert calc.weighted_average([(None, 1.0), (20.0, 0.0), (30.0, 2.0)]) == pytest.approx(30.0)

    def test_no_usable_pairs_returns_none(self) -> None:
        assert calc.weighted_average([(None, 1.0), (10.0, 0.0)]) is None


class TestHealthScore:
    def test_all_components_blend(self) -> None:
        score = calc.health_score(valuation=100.0, conviction=100.0, diversification=100.0)
        assert score == 100

    def test_renormalises_when_component_missing(self) -> None:
        # Only valuation present -> equals that component, rounded.
        assert calc.health_score(valuation=80.0, conviction=None, diversification=None) == 80

    def test_weighted_blend(self) -> None:
        score = calc.health_score(valuation=100.0, conviction=0.0, diversification=0.0)
        assert score == 40  # 0.4 weight on valuation

    def test_all_missing_returns_none(self) -> None:
        assert calc.health_score(valuation=None, conviction=None, diversification=None) is None

    def test_weights_sum_to_one(self) -> None:
        total = calc.VALUATION_WEIGHT + calc.CONVICTION_WEIGHT + calc.DIVERSIFICATION_WEIGHT
        assert math.isclose(total, 1.0)
