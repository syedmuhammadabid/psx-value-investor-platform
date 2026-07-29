"""Portfolio analytics — pure, deterministic holding & portfolio math.

Every figure is expressed the same way the rest of the platform reports it:
percentages for margins/returns, plain numbers (PKR) for money. The margin of
safety and expected CAGR compare a holding's price to its estimated intrinsic
value; the health score blends valuation, conviction, and diversification into
a single 0-100 gauge.
"""

from __future__ import annotations

# Default horizon over which a price is assumed to converge to intrinsic value.
DEFAULT_HORIZON_YEARS = 5

# Health-score component weights (sum to 1.0).
VALUATION_WEIGHT = 0.40
CONVICTION_WEIGHT = 0.30
DIVERSIFICATION_WEIGHT = 0.30

# Margin-of-safety span (percent) mapped onto the 0..100 valuation score.
_MOS_SPAN = 25.0
_FAIR_SCORE = 50.0
_MAX_SCORE = 100.0


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def margin_of_safety(intrinsic_value: float | None, price: float | None) -> float | None:
    """Percent discount of price to intrinsic value (positive == undervalued)."""
    if intrinsic_value is None or intrinsic_value <= 0 or price is None:
        return None
    return (intrinsic_value - price) / intrinsic_value * 100.0


def expected_cagr(
    intrinsic_value: float | None,
    price: float | None,
    *,
    years: int = DEFAULT_HORIZON_YEARS,
) -> float | None:
    """Annualised return if price converges to intrinsic value over ``years``."""
    if intrinsic_value is None or price is None or intrinsic_value <= 0 or price <= 0 or years <= 0:
        return None
    return (float((intrinsic_value / price) ** (1.0 / years)) - 1.0) * 100.0


def valuation_score(portfolio_mos: float | None) -> float | None:
    """Map a portfolio's margin of safety onto a 0..100 score (50 == fair value)."""
    if portfolio_mos is None:
        return None
    return _clamp(_FAIR_SCORE + portfolio_mos * (_FAIR_SCORE / _MOS_SPAN), 0.0, _MAX_SCORE)


def herfindahl(weights: list[float]) -> float:
    """Herfindahl concentration index of portfolio weight fractions."""
    return sum(weight * weight for weight in weights)


def diversification_score(weights: list[float]) -> float | None:
    """0..100 score rewarding even diversification (equal-weight == 100)."""
    count = len(weights)
    if count == 0:
        return None
    if count == 1:
        return 0.0
    # Best (equal weight) HHI is 1/n; worst (all in one) is 1 — normalise onto 0..100.
    normalised = (1.0 - herfindahl(weights)) / (1.0 - 1.0 / count)
    return _clamp(normalised * _MAX_SCORE, 0.0, _MAX_SCORE)


def weighted_average(pairs: list[tuple[float | None, float]]) -> float | None:
    """Weight-average the values, skipping entries with no value or weight <= 0."""
    total = 0.0
    total_weight = 0.0
    for value, weight in pairs:
        if value is None or weight <= 0:
            continue
        total += value * weight
        total_weight += weight
    if total_weight <= 0:
        return None
    return total / total_weight


def health_score(
    *,
    valuation: float | None,
    conviction: float | None,
    diversification: float | None,
) -> int | None:
    """Blend the three 0..100 component scores into a single rounded 0..100 score."""
    blended = weighted_average(
        [
            (valuation, VALUATION_WEIGHT),
            (conviction, CONVICTION_WEIGHT),
            (diversification, DIVERSIFICATION_WEIGHT),
        ]
    )
    if blended is None:
        return None
    return round(blended)
