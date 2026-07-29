"""Buy & sell price zones derived from a company's intrinsic value.

The five bands translate a single fair-value estimate into actionable price
ranges using symmetric margin-of-safety thresholds. Like the other valuation
primitives these functions are pure and deterministic so they can be unit
tested exhaustively (see PROJECT_ROADMAP.md — target >=90% coverage on
``valuation/``).

Bands (relative to intrinsic value ``V``):

* Strong Buy   — price below ``V * 0.75``      (>= 25% margin of safety)
* Buy          — ``V * 0.75`` .. ``V * 0.90``  (10-25% below fair value)
* Hold         — ``V * 0.90`` .. ``V * 1.10``  (within +/-10% of fair value)
* Sell         — ``V * 1.10`` .. ``V * 1.25``  (10-25% above fair value)
* Strong Sell  — price above ``V * 1.25``      (> 25% overvalued)
"""

from __future__ import annotations

# Margin-of-safety thresholds that define the five bands around intrinsic value.
STRONG_BUY_MARGIN = 0.25  # price >= 25% below intrinsic value
BUY_MARGIN = 0.10  # price 10-25% below intrinsic value
SELL_MARGIN = 0.10  # price 10-25% above intrinsic value
STRONG_SELL_MARGIN = 0.25  # price > 25% above intrinsic value

# Ordered band identifiers, cheapest to most expensive.
ZONE_NAMES = ("STRONG_BUY", "BUY", "HOLD", "SELL", "STRONG_SELL")

# A band as (name, lower_bound, upper_bound); ``None`` bounds are unbounded.
Band = tuple[str, float | None, float | None]


def zone_bounds(intrinsic_value: float) -> tuple[float, float, float, float] | None:
    """Return the four ascending price boundaries, or ``None`` if invalid."""
    if intrinsic_value <= 0:
        return None
    strong_buy_ceiling = intrinsic_value * (1.0 - STRONG_BUY_MARGIN)
    buy_ceiling = intrinsic_value * (1.0 - BUY_MARGIN)
    hold_ceiling = intrinsic_value * (1.0 + SELL_MARGIN)
    sell_ceiling = intrinsic_value * (1.0 + STRONG_SELL_MARGIN)
    return (strong_buy_ceiling, buy_ceiling, hold_ceiling, sell_ceiling)


def price_bands(intrinsic_value: float) -> list[Band] | None:
    """Return the five price bands for an intrinsic value, or ``None``."""
    bounds = zone_bounds(intrinsic_value)
    if bounds is None:
        return None
    strong_buy, buy, hold, sell = bounds
    return [
        ("STRONG_BUY", None, strong_buy),
        ("BUY", strong_buy, buy),
        ("HOLD", buy, hold),
        ("SELL", hold, sell),
        ("STRONG_SELL", sell, None),
    ]


def classify_zone(intrinsic_value: float, price: float) -> str | None:
    """Return the band name a price falls into, or ``None`` if invalid.

    Boundaries are lower-inclusive: a price sitting exactly on a boundary
    belongs to the more expensive (higher) band.
    """
    bounds = zone_bounds(intrinsic_value)
    if bounds is None:
        return None
    strong_buy, buy, hold, sell = bounds
    if price < strong_buy:
        return "STRONG_BUY"
    if price < buy:
        return "BUY"
    if price < hold:
        return "HOLD"
    if price < sell:
        return "SELL"
    return "STRONG_SELL"
