"""Explainable recommendation reasons — pure, deterministic factor logic.

Turns a company's headline metrics (valuation discount plus key ratios) into a
list of plain-language *reasons* that justify a BUY / HOLD / SELL call. Every
figure is expressed the same way the ratio engine reports it: percentages for
returns, margins and growth; plain multiples for leverage, coverage and
liquidity. The discount is a percentage where a positive value means the price
sits *below* intrinsic value (i.e. undervalued).
"""

from __future__ import annotations

from typing import NamedTuple

POSITIVE = "positive"
NEGATIVE = "negative"
NEUTRAL = "neutral"

# Valuation discount to intrinsic value (percent; positive == undervalued).
UNDERVALUED_DISCOUNT = 15.0
OVERVALUED_DISCOUNT = -15.0

# Profitability thresholds (percent).
STRONG_ROE = 15.0
WEAK_ROE = 8.0
STRONG_ROIC = 12.0
WEAK_ROIC = 8.0
STRONG_NET_MARGIN = 15.0
WEAK_NET_MARGIN = 5.0

# Leverage thresholds (debt-to-equity multiple; lower is better).
LOW_DEBT = 0.5
HIGH_DEBT = 1.5

# Interest-coverage thresholds (multiple).
STRONG_COVERAGE = 5.0
WEAK_COVERAGE = 1.5

# Current-ratio thresholds (multiple).
HEALTHY_CURRENT = 1.5
WEAK_CURRENT = 1.0


class Factor(NamedTuple):
    """A single explainable reason behind the recommendation."""

    label: str
    detail: str
    sentiment: str


def _band(value: float, *, strong: float, weak: float, high_is_good: bool) -> str:
    """Classify ``value`` into a positive/negative/neutral sentiment band."""
    if high_is_good:
        if value >= strong:
            return POSITIVE
        if value < weak:
            return NEGATIVE
        return NEUTRAL
    if value <= strong:
        return POSITIVE
    if value > weak:
        return NEGATIVE
    return NEUTRAL


def _metric_reason(
    value: float | None,
    *,
    label: str,
    strong: float,
    weak: float,
    high_is_good: bool,
    good: str,
    bad: str,
    neutral: str,
) -> Factor | None:
    """Build a banded reason from a numeric metric, or ``None`` if unavailable."""
    if value is None:
        return None
    sentiment = _band(value, strong=strong, weak=weak, high_is_good=high_is_good)
    template = {POSITIVE: good, NEGATIVE: bad, NEUTRAL: neutral}[sentiment]
    return Factor(label=label, detail=template.format(v=value), sentiment=sentiment)


def _growth_reason(value: float | None, *, label: str, noun: str) -> Factor | None:
    """Build a growth reason (growing / declining / flat) from a CAGR percent."""
    if value is None:
        return None
    if value > 0:
        return Factor(label=label, detail=f"Growing {noun} ({value:.0f}% CAGR)", sentiment=POSITIVE)
    if value < 0:
        return Factor(
            label=label, detail=f"Declining {noun} ({value:.0f}% CAGR)", sentiment=NEGATIVE
        )
    return Factor(label=label, detail=f"Flat {noun}", sentiment=NEUTRAL)


def _valuation_reason(discount: float | None) -> Factor | None:
    """Build the headline valuation reason from the discount to intrinsic value."""
    if discount is None:
        return None
    label = "Valuation"
    if discount >= UNDERVALUED_DISCOUNT:
        return Factor(
            label=label,
            detail=f"Trading {discount:.0f}% below intrinsic value",
            sentiment=POSITIVE,
        )
    if discount <= OVERVALUED_DISCOUNT:
        return Factor(
            label=label,
            detail=f"Trading {abs(discount):.0f}% above intrinsic value",
            sentiment=NEGATIVE,
        )
    return Factor(
        label=label,
        detail="Trading close to intrinsic value",
        sentiment=NEUTRAL,
    )


def build_reasons(
    *,
    discount: float | None,
    roe: float | None,
    roic: float | None,
    net_margin: float | None,
    debt_to_equity: float | None,
    eps_cagr: float | None,
    dividend_cagr: float | None,
    revenue_cagr: float | None,
    interest_coverage: float | None,
    current_ratio: float | None,
) -> list[Factor]:
    """Assemble the ordered list of explainable reasons from the inputs available."""
    candidates = [
        _valuation_reason(discount),
        _metric_reason(
            roe,
            label="Return on equity",
            strong=STRONG_ROE,
            weak=WEAK_ROE,
            high_is_good=True,
            good="Strong ROE ({v:.0f}%)",
            bad="Weak ROE ({v:.0f}%)",
            neutral="ROE {v:.0f}%",
        ),
        _metric_reason(
            roic,
            label="Return on invested capital",
            strong=STRONG_ROIC,
            weak=WEAK_ROIC,
            high_is_good=True,
            good="Strong ROIC ({v:.0f}%)",
            bad="Weak ROIC ({v:.0f}%)",
            neutral="ROIC {v:.0f}%",
        ),
        _metric_reason(
            net_margin,
            label="Net margin",
            strong=STRONG_NET_MARGIN,
            weak=WEAK_NET_MARGIN,
            high_is_good=True,
            good="Healthy net margin ({v:.0f}%)",
            bad="Thin net margin ({v:.0f}%)",
            neutral="Net margin {v:.0f}%",
        ),
        _metric_reason(
            debt_to_equity,
            label="Leverage",
            strong=LOW_DEBT,
            weak=HIGH_DEBT,
            high_is_good=False,
            good="Low debt (D/E {v:.2f})",
            bad="High debt (D/E {v:.2f})",
            neutral="Moderate debt (D/E {v:.2f})",
        ),
        _growth_reason(eps_cagr, label="Earnings growth", noun="EPS"),
        _growth_reason(dividend_cagr, label="Dividend growth", noun="dividend"),
        _growth_reason(revenue_cagr, label="Revenue growth", noun="revenue"),
        _metric_reason(
            interest_coverage,
            label="Interest coverage",
            strong=STRONG_COVERAGE,
            weak=WEAK_COVERAGE,
            high_is_good=True,
            good="Comfortable interest coverage ({v:.1f}x)",
            bad="Thin interest coverage ({v:.1f}x)",
            neutral="Interest coverage {v:.1f}x",
        ),
        _metric_reason(
            current_ratio,
            label="Liquidity",
            strong=HEALTHY_CURRENT,
            weak=WEAK_CURRENT,
            high_is_good=True,
            good="Healthy liquidity (current ratio {v:.2f})",
            bad="Weak liquidity (current ratio {v:.2f})",
            neutral="Adequate liquidity (current ratio {v:.2f})",
        ),
    ]
    return [c for c in candidates if c is not None]
