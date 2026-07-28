"""Unit tests for the pure ratio calculations."""

from __future__ import annotations

import math

import pytest

from app.calculations import ratios as calc


class TestSafeDiv:
    def test_normal(self) -> None:
        assert calc.safe_div(10, 4) == 2.5

    @pytest.mark.parametrize(
        ("num", "den"),
        [(None, 4), (10, None), (10, 0)],
    )
    def test_guards_return_none(self, num: float | None, den: float | None) -> None:
        assert calc.safe_div(num, den) is None


class TestProfitability:
    def test_margins(self) -> None:
        assert calc.gross_margin(400, 1000) == 0.4
        assert calc.operating_margin(250, 1000) == 0.25
        assert calc.net_margin(150, 1000) == 0.15

    def test_returns(self) -> None:
        assert calc.return_on_equity(150, 600) == 0.25
        assert calc.return_on_assets(150, 1500) == 0.1

    def test_effective_tax_rate(self) -> None:
        assert calc.effective_tax_rate(30, 100) == 0.3
        assert calc.effective_tax_rate(30, 0) is None

    def test_invested_capital(self) -> None:
        assert calc.invested_capital(400, 600, 100) == 900.0
        # Missing pieces default to zero.
        assert calc.invested_capital(None, 600, None) == 600.0
        # Both debt and equity missing -> undefined.
        assert calc.invested_capital(None, None, 50) is None

    def test_roic(self) -> None:
        # NOPAT = 200 * (1 - 0.30) = 140; capital = 400 + 600 - 100 = 900.
        result = calc.return_on_invested_capital(200, 30, 100, 400, 600, 100)
        assert result == pytest.approx(140.0 / 900.0)

    def test_roic_defaults_tax_to_zero(self) -> None:
        # pretax income 0 -> tax rate undefined -> treated as 0; NOPAT == EBIT.
        result = calc.return_on_invested_capital(200, 30, 0, 400, 600, 0)
        assert result == pytest.approx(200.0 / 1000.0)

    def test_roic_missing_operating_income(self) -> None:
        assert calc.return_on_invested_capital(None, 30, 100, 400, 600, 100) is None


class TestValuation:
    def test_pe(self) -> None:
        assert calc.price_to_earnings(1000, 50) == 20.0

    def test_pe_non_positive_earnings(self) -> None:
        assert calc.price_to_earnings(1000, 0) is None
        assert calc.price_to_earnings(1000, -50) is None

    def test_pb(self) -> None:
        assert calc.price_to_book(1200, 600) == 2.0
        assert calc.price_to_book(1200, 0) is None

    def test_price_to_sales(self) -> None:
        assert calc.price_to_sales(2000, 1000) == 2.0

    def test_peg(self) -> None:
        # PEG = 20 / (0.20 * 100) = 1.0
        assert calc.peg_ratio(20, 0.20) == pytest.approx(1.0)

    def test_peg_non_positive_growth(self) -> None:
        assert calc.peg_ratio(20, 0) is None
        assert calc.peg_ratio(20, -0.05) is None
        assert calc.peg_ratio(None, 0.2) is None

    def test_enterprise_value(self) -> None:
        assert calc.enterprise_value(1000, 400, 100) == 1300.0
        assert calc.enterprise_value(None, 400, 100) is None

    def test_ebitda(self) -> None:
        # DA proxy = max(OCF - NI, 0) = max(300 - 150, 0) = 150.
        assert calc.ebitda(250, 300, 150) == 400.0
        # Negative proxy floored at zero.
        assert calc.ebitda(250, 100, 150) == 250.0
        assert calc.ebitda(None, 300, 150) is None

    def test_ev_to_ebitda(self) -> None:
        assert calc.ev_to_ebitda(1300, 260) == 5.0
        assert calc.ev_to_ebitda(1300, 0) is None


class TestDebt:
    def test_debt_to_equity(self) -> None:
        assert calc.debt_to_equity(300, 600) == 0.5

    def test_interest_coverage(self) -> None:
        assert calc.interest_coverage(250, 25) == 10.0
        assert calc.interest_coverage(250, 0) is None


class TestLiquidity:
    def test_current_ratio(self) -> None:
        assert calc.current_ratio(600, 300) == 2.0

    def test_quick_ratio(self) -> None:
        assert calc.quick_ratio(600, 200, 200) == 2.0
        # Missing inventory treated as zero.
        assert calc.quick_ratio(600, None, 300) == 2.0
        assert calc.quick_ratio(None, 200, 200) is None


class TestCashFlow:
    def test_free_cash_flow(self) -> None:
        assert calc.free_cash_flow(300, -80) == 220.0
        assert calc.free_cash_flow(None, -80) is None

    def test_fcf_yield(self) -> None:
        assert calc.fcf_yield(220, 4400) == 0.05


class TestCagr:
    def test_cagr(self) -> None:
        # Doubling over 2 years -> sqrt(2) - 1.
        assert calc.cagr(100, 200, 2) == pytest.approx(math.sqrt(2) - 1)

    @pytest.mark.parametrize(
        ("earliest", "latest", "years"),
        [
            (None, 200, 2),
            (100, None, 2),
            (100, 200, None),
            (0, 200, 2),
            (100, -5, 2),
            (100, 200, 0),
        ],
    )
    def test_cagr_guards(
        self, earliest: float | None, latest: float | None, years: float | None
    ) -> None:
        assert calc.cagr(earliest, latest, years) is None
