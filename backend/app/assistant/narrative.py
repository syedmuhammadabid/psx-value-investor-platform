"""Deterministic answer composition for the AI assistant.

Pure functions: given a bundle of already-computed company facts, each builder
returns a short natural-language answer plus a list of highlight bullets. There
is no database access and no external LLM — the "intelligence" is a transparent
mapping from the platform's own valuation, ratio, and growth outputs to prose.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import NamedTuple

from app.assistant.intents import Intent


class Facts(NamedTuple):
    """The pre-computed figures an answer can draw on."""

    symbol: str
    recommendation: str
    discount: float | None
    intrinsic_value: float | None
    current_price: float | None
    roe: float | None
    roic: float | None
    net_margin: float | None
    debt_to_equity: float | None
    interest_coverage: float | None
    current_ratio: float | None
    revenue_cagr: float | None
    eps_cagr: float | None
    dividend_cagr: float | None
    dividend_yield: float | None
    free_cash_flow: float | None
    fcf_yield: float | None


def _pct(value: float | None) -> str:
    return f"{value:.1f}%" if value is not None else "n/a"


def _money(value: float | None) -> str:
    return f"Rs {value:,.2f}" if value is not None else "n/a"


def _multiple(value: float | None) -> str:
    return f"{value:.2f}\u00d7" if value is not None else "n/a"


def _ratio(value: float | None) -> str:
    return f"{value:.2f}" if value is not None else "n/a"


def _stance(recommendation: str) -> str:
    if recommendation == "BUY":
        return "undervalued"
    if recommendation == "SELL":
        return "overvalued"
    return "fairly valued"


def _discount_clause(facts: Facts) -> str:
    """Describe where the price sits relative to the estimated intrinsic value."""
    if facts.discount is None:
        return "an intrinsic value could not be estimated from the available data"
    target = _money(facts.intrinsic_value)
    if facts.discount > 0:
        return (
            f"it trades about {facts.discount:.0f}% below the estimated intrinsic value of {target}"
        )
    if facts.discount < 0:
        return (
            f"it trades about {abs(facts.discount):.0f}% above the estimated "
            f"intrinsic value of {target}"
        )
    return f"it trades in line with the estimated intrinsic value of {target}"


def _verdict(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"{facts.symbol} currently screens as a {facts.recommendation}: "
        f"{_discount_clause(facts)}. Profitability shows ROE {_pct(facts.roe)} and "
        f"ROIC {_pct(facts.roic)}, with debt-to-equity at {_ratio(facts.debt_to_equity)}."
    )
    highlights = [
        f"Recommendation: {facts.recommendation}",
        f"Current price: {_money(facts.current_price)}",
        f"Intrinsic value: {_money(facts.intrinsic_value)}",
        f"Discount: {_pct(facts.discount)}",
    ]
    return answer, highlights


def _valuation(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"On a blended intrinsic-value basis {facts.symbol} looks "
        f"{_stance(facts.recommendation)}. The current price is "
        f"{_money(facts.current_price)} against an estimated intrinsic value of "
        f"{_money(facts.intrinsic_value)}, so {_discount_clause(facts)}."
    )
    highlights = [
        f"Intrinsic value: {_money(facts.intrinsic_value)}",
        f"Current price: {_money(facts.current_price)}",
        f"Discount: {_pct(facts.discount)}",
    ]
    return answer, highlights


def _growth(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"Over recent years {facts.symbol} has compounded revenue at "
        f"{_pct(facts.revenue_cagr)} and EPS at {_pct(facts.eps_cagr)} a year, with "
        f"dividends growing {_pct(facts.dividend_cagr)} annually."
    )
    highlights = [
        f"Revenue CAGR: {_pct(facts.revenue_cagr)}",
        f"EPS CAGR: {_pct(facts.eps_cagr)}",
        f"Dividend CAGR: {_pct(facts.dividend_cagr)}",
    ]
    return answer, highlights


def _cash_flow(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"{facts.symbol} generated free cash flow of {_money(facts.free_cash_flow)} in "
        f"the latest year, an FCF yield of {_pct(facts.fcf_yield)} on its market value."
    )
    highlights = [
        f"Free cash flow: {_money(facts.free_cash_flow)}",
        f"FCF yield: {_pct(facts.fcf_yield)}",
    ]
    return answer, highlights


def _risk(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"On balance-sheet risk, {facts.symbol} carries debt-to-equity of "
        f"{_ratio(facts.debt_to_equity)} with interest coverage of "
        f"{_multiple(facts.interest_coverage)} and a current ratio of "
        f"{_ratio(facts.current_ratio)}."
    )
    highlights = [
        f"Debt-to-equity: {_ratio(facts.debt_to_equity)}",
        f"Interest coverage: {_multiple(facts.interest_coverage)}",
        f"Current ratio: {_ratio(facts.current_ratio)}",
    ]
    return answer, highlights


def _dividend(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"{facts.symbol} offers a dividend yield of {_pct(facts.dividend_yield)}, with "
        f"the payout growing {_pct(facts.dividend_cagr)} a year."
    )
    highlights = [
        f"Dividend yield: {_pct(facts.dividend_yield)}",
        f"Dividend CAGR: {_pct(facts.dividend_cagr)}",
    ]
    return answer, highlights


def _profitability(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"{facts.symbol} earns a return on equity of {_pct(facts.roe)} and a return on "
        f"invested capital of {_pct(facts.roic)}, on a net margin of "
        f"{_pct(facts.net_margin)}."
    )
    highlights = [
        f"ROE: {_pct(facts.roe)}",
        f"ROIC: {_pct(facts.roic)}",
        f"Net margin: {_pct(facts.net_margin)}",
    ]
    return answer, highlights


def _overview(facts: Facts) -> tuple[str, list[str]]:
    answer = (
        f"{facts.symbol} currently looks {_stance(facts.recommendation)} "
        f"({facts.recommendation}): {_discount_clause(facts)}. It earns ROE "
        f"{_pct(facts.roe)} and ROIC {_pct(facts.roic)}, grew EPS {_pct(facts.eps_cagr)} "
        f"a year, and carries debt-to-equity of {_ratio(facts.debt_to_equity)}."
    )
    highlights = [
        f"Recommendation: {facts.recommendation}",
        f"Intrinsic value: {_money(facts.intrinsic_value)}",
        f"Current price: {_money(facts.current_price)}",
        f"ROIC: {_pct(facts.roic)}",
    ]
    return answer, highlights


_BUILDERS: dict[Intent, Callable[[Facts], tuple[str, list[str]]]] = {
    Intent.VERDICT: _verdict,
    Intent.VALUATION: _valuation,
    Intent.GROWTH: _growth,
    Intent.CASH_FLOW: _cash_flow,
    Intent.RISK: _risk,
    Intent.DIVIDEND: _dividend,
    Intent.PROFITABILITY: _profitability,
    Intent.OVERVIEW: _overview,
}


def compose(intent: Intent, facts: Facts) -> tuple[str, list[str]]:
    """Build the answer text and highlight bullets for an intent."""
    return _BUILDERS[intent](facts)
