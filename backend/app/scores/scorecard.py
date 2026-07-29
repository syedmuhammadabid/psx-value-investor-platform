"""Pure investment-scoring functions.

Each function is deterministic and side-effect free. Inputs may be missing
(``None``); a check whose inputs are unavailable is reported with ``passed=None``
and excluded from the score, so a company with partial data still gets a
well-defined (if less complete) result.

Conventions match the ratio engine: percentage-style inputs (ROE, ROIC, margins,
growth, yields) arrive as percentages (e.g. ``23.0`` == 23%); multiples and
ratios (P/E, P/B, D/E, current ratio) are plain numbers. Monetary inputs are in
PKR.
"""

from __future__ import annotations

from typing import NamedTuple

from app.calculations import ratios as calc


class ScoreCheck(NamedTuple):
    """A single pass/fail criterion behind a score (``passed=None`` == no data)."""

    label: str
    detail: str
    passed: bool | None


class Composite(NamedTuple):
    """A 0-100 composite score with its underlying checks."""

    value: float | None
    rating: str
    checks: list[ScoreCheck]


class Piotroski(NamedTuple):
    """The Piotroski F-Score (0-9) with its nine checks."""

    value: int | None
    rating: str
    checks: list[ScoreCheck]


class Altman(NamedTuple):
    """The Altman Z-Score with its distress band."""

    value: float | None
    band: str
    detail: str


class Magic(NamedTuple):
    """The two Magic Formula components (both as percentages)."""

    roic: float | None
    earnings_yield: float | None
    detail: str


class PeriodInputs(NamedTuple):
    """The raw statement figures a single period contributes to the F-Score."""

    net_income: float | None
    total_assets: float | None
    operating_cash_flow: float | None
    total_debt: float | None
    current_assets: float | None
    current_liabilities: float | None
    shares_outstanding: float | None
    gross_profit: float | None
    revenue: float | None


# --------------------------------------------------------------------------- #
# Rating bands and thresholds
# --------------------------------------------------------------------------- #
RATING_NA = "na"

_EXCELLENT = 80.0
_GOOD = 60.0
_FAIR = 40.0

# Composite check thresholds (percentages unless noted).
_MIN_ROE = 15.0
_MIN_ROIC = 12.0
_MIN_EPS_GROWTH = 5.0
_MAX_DE = 1.0
_MAX_DE_STRONG = 0.5
_MAX_DE_QUALITY = 0.6
_MIN_CR_STABLE = 1.5
_MIN_CR_GRAHAM = 2.0
_MAX_PE_GRAHAM = 15.0
_MAX_PB_GRAHAM = 1.5
_MAX_PE_QUALITY = 20.0

# Altman Z-Score coefficients (original manufacturing model).
_Z_WC = 1.2
_Z_RE = 1.4
_Z_EBIT = 3.3
_Z_MV = 0.6
_Z_SALES = 1.0
_Z_SAFE = 2.99
_Z_DISTRESS = 1.81

# Piotroski rating bands (out of 9).
_F_STRONG = 7
_F_MODERATE = 4


def rating(value: float | None) -> str:
    """Map a 0-100 score to a coarse rating label."""
    if value is None:
        return RATING_NA
    if value >= _EXCELLENT:
        return "excellent"
    if value >= _GOOD:
        return "good"
    if value >= _FAIR:
        return "fair"
    return "weak"


# --------------------------------------------------------------------------- #
# Check builders
# --------------------------------------------------------------------------- #
def _pct_above(label: str, value: float | None, threshold: float) -> ScoreCheck:
    if value is None:
        return ScoreCheck(label, "No data", None)
    return ScoreCheck(label, f"{value:.1f}% (target > {threshold:g}%)", value > threshold)


def _num_above(label: str, value: float | None, threshold: float) -> ScoreCheck:
    if value is None:
        return ScoreCheck(label, "No data", None)
    return ScoreCheck(label, f"{value:.2f} (target > {threshold:g})", value > threshold)


def _num_below(label: str, value: float | None, threshold: float) -> ScoreCheck:
    if value is None:
        return ScoreCheck(label, "No data", None)
    return ScoreCheck(label, f"{value:.2f} (target < {threshold:g})", value < threshold)


def _positive(label: str, value: float | None) -> ScoreCheck:
    if value is None:
        return ScoreCheck(label, "No data", None)
    return ScoreCheck(label, "Positive" if value > 0 else "Negative", value > 0)


def _composite(checks: list[ScoreCheck]) -> Composite:
    evaluable = [c.passed for c in checks if c.passed is not None]
    if not evaluable:
        return Composite(value=None, rating=RATING_NA, checks=checks)
    value = sum(1 for passed in evaluable if passed) / len(evaluable) * 100.0
    return Composite(value=value, rating=rating(value), checks=checks)


# --------------------------------------------------------------------------- #
# Composite scores
# --------------------------------------------------------------------------- #
def financial_health(
    *,
    debt_to_equity: float | None,
    free_cash_flow: float | None,
    net_margin: float | None,
    revenue_cagr: float | None,
    current_ratio: float | None,
) -> Composite:
    """0-100 blend of debt, cash flow, profitability, growth, and stability."""
    return _composite(
        [
            _num_below("Manageable debt", debt_to_equity, _MAX_DE),
            _positive("Positive free cash flow", free_cash_flow),
            _pct_above("Profitable (net margin)", net_margin, 0.0),
            _pct_above("Revenue growth", revenue_cagr, 0.0),
            _num_above("Liquidity (current ratio)", current_ratio, _MIN_CR_STABLE),
        ]
    )


def buffett(
    *,
    roe: float | None,
    roic: float | None,
    debt_to_equity: float | None,
    eps_cagr: float | None,
    dividend_yield: float | None,
    free_cash_flow: float | None,
) -> Composite:
    """0-100 Buffett-style quality: high returns, low debt, growth, dividends, FCF."""
    return _composite(
        [
            _pct_above("High return on equity", roe, _MIN_ROE),
            _pct_above("High return on invested capital", roic, _MIN_ROIC),
            _num_below("Low debt", debt_to_equity, _MAX_DE_STRONG),
            _pct_above("Growing earnings", eps_cagr, 0.0),
            _pct_above("Pays a dividend", dividend_yield, 0.0),
            _positive("Positive free cash flow", free_cash_flow),
        ]
    )


def graham(
    *,
    pe: float | None,
    pb: float | None,
    debt_to_equity: float | None,
    current_ratio: float | None,
    net_income: float | None,
) -> Composite:
    """0-100 Graham defensive value: cheap multiples, low debt, liquidity, profits."""
    return _composite(
        [
            _num_below("Modest P/E", pe, _MAX_PE_GRAHAM),
            _num_below("Modest P/B", pb, _MAX_PB_GRAHAM),
            _num_below("Conservative debt", debt_to_equity, _MAX_DE),
            _num_above("Strong current ratio", current_ratio, _MIN_CR_GRAHAM),
            _positive("Positive earnings", net_income),
        ]
    )


def quality(
    *,
    roic: float | None,
    eps_cagr: float | None,
    free_cash_flow: float | None,
    debt_to_equity: float | None,
    pe: float | None,
) -> Composite:
    """0-100 overall quality: profitability, growth, cash flow, debt, valuation."""
    return _composite(
        [
            _pct_above("Profitability (ROIC)", roic, _MIN_ROIC),
            _pct_above("Growth (EPS CAGR)", eps_cagr, _MIN_EPS_GROWTH),
            _positive("Cash generation (FCF)", free_cash_flow),
            _num_below("Balance sheet (D/E)", debt_to_equity, _MAX_DE_QUALITY),
            _num_below("Valuation (P/E)", pe, _MAX_PE_QUALITY),
        ]
    )


# --------------------------------------------------------------------------- #
# Piotroski F-Score
# --------------------------------------------------------------------------- #
def _delta_check(label: str, current: float | None, prior: float | None) -> ScoreCheck:
    if current is None or prior is None:
        return ScoreCheck(label, "No data", None)
    return ScoreCheck(label, "Improved" if current > prior else "Declined", current > prior)


def _piotroski_rating(value: int) -> str:
    if value >= _F_STRONG:
        return "strong"
    if value >= _F_MODERATE:
        return "moderate"
    return "weak"


def piotroski(current: PeriodInputs, prior: PeriodInputs) -> Piotroski:
    """The 9-point Piotroski F-Score comparing the latest year to the prior year."""
    cur_roa = calc.return_on_assets(current.net_income, current.total_assets)
    pri_roa = calc.return_on_assets(prior.net_income, prior.total_assets)
    cur_cfo_ta = calc.safe_div(current.operating_cash_flow, current.total_assets)
    cur_leverage = calc.safe_div(current.total_debt, current.total_assets)
    pri_leverage = calc.safe_div(prior.total_debt, prior.total_assets)
    cur_cr = calc.current_ratio(current.current_assets, current.current_liabilities)
    pri_cr = calc.current_ratio(prior.current_assets, prior.current_liabilities)
    cur_gm = calc.gross_margin(current.gross_profit, current.revenue)
    pri_gm = calc.gross_margin(prior.gross_profit, prior.revenue)
    cur_turnover = calc.safe_div(current.revenue, current.total_assets)
    pri_turnover = calc.safe_div(prior.revenue, prior.total_assets)

    checks = [
        _positive("Positive return on assets", cur_roa),
        _positive("Positive operating cash flow", current.operating_cash_flow),
        _delta_check("Rising return on assets", cur_roa, pri_roa),
        _accruals_check(cur_cfo_ta, cur_roa),
        _delta_check("Falling leverage", pri_leverage, cur_leverage),
        _delta_check("Rising current ratio", cur_cr, pri_cr),
        _no_dilution_check(current.shares_outstanding, prior.shares_outstanding),
        _delta_check("Rising gross margin", cur_gm, pri_gm),
        _delta_check("Rising asset turnover", cur_turnover, pri_turnover),
    ]

    evaluable = [c.passed for c in checks if c.passed is not None]
    if not evaluable:
        return Piotroski(value=None, rating=RATING_NA, checks=checks)
    value = sum(1 for passed in evaluable if passed)
    return Piotroski(value=value, rating=_piotroski_rating(value), checks=checks)


def _accruals_check(cfo_to_assets: float | None, roa: float | None) -> ScoreCheck:
    label = "Cash-backed earnings"
    if cfo_to_assets is None or roa is None:
        return ScoreCheck(label, "No data", None)
    passed = cfo_to_assets > roa
    return ScoreCheck(label, "Cash flow exceeds accruals" if passed else "Accruals-heavy", passed)


def _no_dilution_check(current: float | None, prior: float | None) -> ScoreCheck:
    label = "No share dilution"
    if current is None or prior is None:
        return ScoreCheck(label, "No data", None)
    passed = current <= prior
    return ScoreCheck(label, "Shares steady or lower" if passed else "Shares increased", passed)


# --------------------------------------------------------------------------- #
# Altman Z-Score
# --------------------------------------------------------------------------- #
def altman_z(
    *,
    current_assets: float | None,
    current_liabilities: float | None,
    total_assets: float | None,
    retained_earnings: float | None,
    total_liabilities: float | None,
    operating_income: float | None,
    revenue: float | None,
    market_cap: float | None,
) -> Altman:
    """Altman Z-Score for bankruptcy risk (original manufacturing coefficients).

    Retained earnings are not captured as a line item; the caller supplies an
    approximation (typically total equity), which the ``X2`` term relies on.
    """
    x1 = _z_term(current_assets, current_liabilities, total_assets)
    x2 = calc.safe_div(retained_earnings, total_assets)
    x3 = calc.safe_div(operating_income, total_assets)
    x4 = calc.safe_div(market_cap, total_liabilities)
    x5 = calc.safe_div(revenue, total_assets)
    if x1 is None or x2 is None or x3 is None or x4 is None or x5 is None:
        return Altman(value=None, band=RATING_NA, detail="Insufficient data")

    z = _Z_WC * x1 + _Z_RE * x2 + _Z_EBIT * x3 + _Z_MV * x4 + _Z_SALES * x5
    if z >= _Z_SAFE:
        return Altman(value=z, band="safe", detail="Low bankruptcy risk")
    if z >= _Z_DISTRESS:
        return Altman(value=z, band="grey", detail="Some bankruptcy risk")
    return Altman(value=z, band="distress", detail="Elevated bankruptcy risk")


def _z_term(
    current_assets: float | None,
    current_liabilities: float | None,
    total_assets: float | None,
) -> float | None:
    if current_assets is None or current_liabilities is None:
        return None
    return calc.safe_div(current_assets - current_liabilities, total_assets)


# --------------------------------------------------------------------------- #
# Magic Formula
# --------------------------------------------------------------------------- #
def magic_formula(
    *,
    roic: float | None,
    operating_income: float | None,
    enterprise_value: float | None,
) -> Magic:
    """Greenblatt's two Magic Formula components: ROIC and earnings yield.

    ``roic`` arrives as a percentage. Earnings yield is EBIT / enterprise value,
    returned as a percentage. A universe-wide combined ranking is out of scope
    for a single-company view.
    """
    yield_fraction = calc.safe_div(operating_income, enterprise_value)
    earnings_yield = yield_fraction * 100.0 if yield_fraction is not None else None
    return Magic(
        roic=roic,
        earnings_yield=earnings_yield,
        detail="Higher ROIC and earnings yield rank better on the Magic Formula.",
    )
