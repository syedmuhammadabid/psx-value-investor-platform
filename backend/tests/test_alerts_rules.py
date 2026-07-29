"""Unit tests for the pure alert-signal rules."""

from __future__ import annotations

import pytest

from app.alerts import rules


class TestValuationSignal:
    def test_none_returns_none(self) -> None:
        assert rules.valuation_signal(None) is None

    def test_deep_discount_is_positive(self) -> None:
        signal = rules.valuation_signal(25.0)
        assert signal is not None
        assert signal.type == rules.PRICE_BELOW_INTRINSIC
        assert signal.sentiment == rules.POSITIVE

    def test_premium_is_negative(self) -> None:
        signal = rules.valuation_signal(-20.0)
        assert signal is not None
        assert signal.type == rules.PRICE_ABOVE_INTRINSIC
        assert signal.sentiment == rules.NEGATIVE

    def test_within_band_returns_none(self) -> None:
        assert rules.valuation_signal(5.0) is None
        assert rules.valuation_signal(-5.0) is None

    def test_boundary_is_inclusive(self) -> None:
        assert rules.valuation_signal(rules.VALUATION_MARGIN) is not None
        assert rules.valuation_signal(-rules.VALUATION_MARGIN) is not None


class TestRoicSignal:
    def test_missing_inputs_return_none(self) -> None:
        assert rules.roic_signal(None, 10.0) is None
        assert rules.roic_signal(10.0, None) is None

    def test_improvement_is_positive(self) -> None:
        signal = rules.roic_signal(15.0, 12.0)
        assert signal is not None
        assert signal.type == rules.ROIC_IMPROVED
        assert signal.sentiment == rules.POSITIVE

    def test_decline_is_negative(self) -> None:
        signal = rules.roic_signal(10.0, 14.0)
        assert signal is not None
        assert signal.type == rules.ROIC_DECLINED

    def test_flat_returns_none(self) -> None:
        assert rules.roic_signal(12.0, 12.5) is None


class TestDebtSignal:
    def test_missing_inputs_return_none(self) -> None:
        assert rules.debt_signal(None, 0.3) is None
        assert rules.debt_signal(0.3, None) is None

    def test_increase_is_negative(self) -> None:
        signal = rules.debt_signal(0.45, 0.30)
        assert signal is not None
        assert signal.type == rules.DEBT_INCREASED
        assert signal.sentiment == rules.NEGATIVE

    def test_reduction_is_positive(self) -> None:
        signal = rules.debt_signal(0.20, 0.40)
        assert signal is not None
        assert signal.type == rules.DEBT_REDUCED
        assert signal.sentiment == rules.POSITIVE

    def test_small_change_returns_none(self) -> None:
        assert rules.debt_signal(0.32, 0.30) is None


class TestEarningsSignal:
    def test_missing_or_zero_base_returns_none(self) -> None:
        assert rules.earnings_signal(None, 10.0) is None
        assert rules.earnings_signal(10.0, None) is None
        assert rules.earnings_signal(10.0, 0.0) is None

    def test_growth_is_positive(self) -> None:
        signal = rules.earnings_signal(28.0, 20.0)
        assert signal is not None
        assert signal.type == rules.EARNINGS_GROWTH

    def test_decline_is_negative(self) -> None:
        signal = rules.earnings_signal(18.0, 20.0)
        assert signal is not None
        assert signal.type == rules.EARNINGS_DECLINE

    def test_flat_returns_none(self) -> None:
        assert rules.earnings_signal(20.4, 20.0) is None


class TestDividendSignal:
    def test_missing_inputs_return_none(self) -> None:
        assert rules.dividend_signal(None, 1.0) is None
        assert rules.dividend_signal(1.0, None) is None

    def test_initiation_is_positive(self) -> None:
        signal = rules.dividend_signal(5.0, 0.0)
        assert signal is not None
        assert signal.type == rules.DIVIDEND_INITIATED

    def test_increase_is_positive(self) -> None:
        signal = rules.dividend_signal(8.0, 5.0)
        assert signal is not None
        assert signal.type == rules.DIVIDEND_INCREASED

    def test_cut_is_negative(self) -> None:
        signal = rules.dividend_signal(3.0, 5.0)
        assert signal is not None
        assert signal.type == rules.DIVIDEND_CUT
        assert signal.sentiment == rules.NEGATIVE

    def test_unchanged_returns_none(self) -> None:
        assert rules.dividend_signal(5.0, 5.0) is None


class TestRatingSignal:
    def test_none_returns_none(self) -> None:
        assert rules.rating_signal(None) is None

    @pytest.mark.parametrize(
        ("rating", "expected"),
        [("BUY", rules.RATING_BULLISH), ("SELL", rules.RATING_BEARISH)],
    )
    def test_actionable_ratings(self, rating: str, expected: str) -> None:
        signal = rules.rating_signal(rating)
        assert signal is not None
        assert signal.type == expected

    def test_hold_returns_none(self) -> None:
        assert rules.rating_signal("HOLD") is None
