"""Unit tests for the explainable recommendation reason logic."""

from __future__ import annotations

import pytest

from app.valuation import recommendation as rec


class TestValuationReason:
    def test_none_discount_yields_no_reason(self) -> None:
        assert rec._valuation_reason(None) is None

    def test_undervalued_is_positive(self) -> None:
        factor = rec._valuation_reason(21.0)
        assert factor is not None
        assert factor.sentiment == rec.POSITIVE
        assert factor.detail == "Trading 21% below intrinsic value"

    def test_overvalued_is_negative(self) -> None:
        factor = rec._valuation_reason(-30.0)
        assert factor is not None
        assert factor.sentiment == rec.NEGATIVE
        assert factor.detail == "Trading 30% above intrinsic value"

    def test_fairly_valued_is_neutral(self) -> None:
        factor = rec._valuation_reason(3.0)
        assert factor is not None
        assert factor.sentiment == rec.NEUTRAL
        assert "close to intrinsic value" in factor.detail


class TestBand:
    @pytest.mark.parametrize(
        ("value", "expected"),
        [(20.0, rec.POSITIVE), (15.0, rec.POSITIVE), (10.0, rec.NEUTRAL), (5.0, rec.NEGATIVE)],
    )
    def test_high_is_good(self, value: float, expected: str) -> None:
        assert rec._band(value, strong=15.0, weak=8.0, high_is_good=True) == expected

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(0.4, rec.POSITIVE), (0.5, rec.POSITIVE), (1.0, rec.NEUTRAL), (2.0, rec.NEGATIVE)],
    )
    def test_low_is_good(self, value: float, expected: str) -> None:
        assert rec._band(value, strong=0.5, weak=1.5, high_is_good=False) == expected


class TestMetricReason:
    def test_none_value_yields_no_reason(self) -> None:
        assert (
            rec._metric_reason(
                None,
                label="ROE",
                strong=15.0,
                weak=8.0,
                high_is_good=True,
                good="good",
                bad="bad",
                neutral="neutral",
            )
            is None
        )

    def test_strong_uses_good_template(self) -> None:
        factor = rec._metric_reason(
            23.0,
            label="Return on equity",
            strong=15.0,
            weak=8.0,
            high_is_good=True,
            good="Strong ROE ({v:.0f}%)",
            bad="Weak ROE ({v:.0f}%)",
            neutral="ROE {v:.0f}%",
        )
        assert factor is not None
        assert factor.sentiment == rec.POSITIVE
        assert factor.detail == "Strong ROE (23%)"


class TestGrowthReason:
    def test_none_value_yields_no_reason(self) -> None:
        assert rec._growth_reason(None, label="EPS", noun="EPS") is None

    def test_positive_growth(self) -> None:
        factor = rec._growth_reason(12.0, label="Earnings growth", noun="EPS")
        assert factor is not None
        assert factor.sentiment == rec.POSITIVE
        assert factor.detail == "Growing EPS (12% CAGR)"

    def test_negative_growth(self) -> None:
        factor = rec._growth_reason(-8.0, label="Earnings growth", noun="EPS")
        assert factor is not None
        assert factor.sentiment == rec.NEGATIVE
        assert factor.detail == "Declining EPS (-8% CAGR)"

    def test_flat_growth(self) -> None:
        factor = rec._growth_reason(0.0, label="Dividend growth", noun="dividend")
        assert factor is not None
        assert factor.sentiment == rec.NEUTRAL
        assert factor.detail == "Flat dividend"


class TestBuildReasons:
    def test_no_inputs_yields_empty_list(self) -> None:
        reasons = rec.build_reasons(
            discount=None,
            roe=None,
            roic=None,
            net_margin=None,
            debt_to_equity=None,
            eps_cagr=None,
            dividend_cagr=None,
            revenue_cagr=None,
            interest_coverage=None,
            current_ratio=None,
        )
        assert reasons == []

    def test_full_inputs_cover_every_factor(self) -> None:
        reasons = rec.build_reasons(
            discount=21.0,
            roe=23.0,
            roic=18.0,
            net_margin=20.0,
            debt_to_equity=0.3,
            eps_cagr=12.0,
            dividend_cagr=8.0,
            revenue_cagr=10.0,
            interest_coverage=9.0,
            current_ratio=2.1,
        )
        # One reason per supplied metric; valuation reason first.
        assert len(reasons) == 10
        assert reasons[0].label == "Valuation"
        assert all(r.sentiment == rec.POSITIVE for r in reasons)

    def test_weak_metrics_are_negative(self) -> None:
        reasons = rec.build_reasons(
            discount=-25.0,
            roe=4.0,
            roic=3.0,
            net_margin=2.0,
            debt_to_equity=2.5,
            eps_cagr=-5.0,
            dividend_cagr=-3.0,
            revenue_cagr=-2.0,
            interest_coverage=1.0,
            current_ratio=0.7,
        )
        assert all(r.sentiment == rec.NEGATIVE for r in reasons)

    def test_partial_inputs_skip_missing(self) -> None:
        reasons = rec.build_reasons(
            discount=None,
            roe=23.0,
            roic=None,
            net_margin=None,
            debt_to_equity=None,
            eps_cagr=None,
            dividend_cagr=None,
            revenue_cagr=None,
            interest_coverage=None,
            current_ratio=None,
        )
        assert len(reasons) == 1
        assert reasons[0].label == "Return on equity"
