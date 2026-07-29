"""Pure alert-signal detection rules.

Deterministic, side-effect-free functions that decide whether a noteworthy
condition currently holds for a company. Each returns a :class:`Signal` or
``None`` when nothing noteworthy applies. The service layer supplies the
current-vs-prior metrics gathered from the database.

This is the stateless core of the alerts feature: it computes the conditions
that *would* trigger a notification. Per-user subscriptions and delivery
(browser, email, Telegram) require authentication and are handled separately.
"""

from __future__ import annotations

from typing import NamedTuple

# Sentiment tags (kept as plain strings so this module stays free of schema
# dependencies; the service maps them onto the response enum).
POSITIVE = "positive"
NEGATIVE = "negative"
NEUTRAL = "neutral"

# Stable, machine-readable signal identifiers.
PRICE_BELOW_INTRINSIC = "price_below_intrinsic"
PRICE_ABOVE_INTRINSIC = "price_above_intrinsic"
ROIC_IMPROVED = "roic_improved"
ROIC_DECLINED = "roic_declined"
DEBT_INCREASED = "debt_increased"
DEBT_REDUCED = "debt_reduced"
EARNINGS_GROWTH = "earnings_growth"
EARNINGS_DECLINE = "earnings_decline"
DIVIDEND_INITIATED = "dividend_initiated"
DIVIDEND_INCREASED = "dividend_increased"
DIVIDEND_CUT = "dividend_cut"
RATING_BULLISH = "rating_bullish"
RATING_BEARISH = "rating_bearish"

# Thresholds — tuned to surface meaningful moves rather than noise.
VALUATION_MARGIN = 15.0  # % discount to flag under/overvaluation
ROIC_DELTA = 1.0  # percentage-point change in ROIC
DEBT_DELTA = 0.10  # change in debt-to-equity
EARNINGS_CHANGE = 5.0  # % change in EPS
_DIVIDEND_EPS = 1e-9  # ignore floating-point dust in dividend comparisons


class Signal(NamedTuple):
    """A single triggered alert condition."""

    type: str
    title: str
    detail: str
    sentiment: str


def valuation_signal(discount: float | None) -> Signal | None:
    """Flag when price is meaningfully below or above intrinsic value."""
    if discount is None:
        return None
    if discount >= VALUATION_MARGIN:
        return Signal(
            PRICE_BELOW_INTRINSIC,
            "Trading below intrinsic value",
            f"Price is {discount:.0f}% below the estimated intrinsic value.",
            POSITIVE,
        )
    if discount <= -VALUATION_MARGIN:
        return Signal(
            PRICE_ABOVE_INTRINSIC,
            "Trading above intrinsic value",
            f"Price is {abs(discount):.0f}% above the estimated intrinsic value.",
            NEGATIVE,
        )
    return None


def roic_signal(current: float | None, prior: float | None) -> Signal | None:
    """Flag a material rise or fall in return on invested capital (percent)."""
    if current is None or prior is None:
        return None
    delta = current - prior
    if delta >= ROIC_DELTA:
        return Signal(
            ROIC_IMPROVED,
            "ROIC improving",
            f"Return on invested capital rose to {current:.1f}% from {prior:.1f}%.",
            POSITIVE,
        )
    if delta <= -ROIC_DELTA:
        return Signal(
            ROIC_DECLINED,
            "ROIC declining",
            f"Return on invested capital fell to {current:.1f}% from {prior:.1f}%.",
            NEGATIVE,
        )
    return None


def debt_signal(current: float | None, prior: float | None) -> Signal | None:
    """Flag a material rise or fall in the debt-to-equity ratio."""
    if current is None or prior is None:
        return None
    delta = current - prior
    if delta >= DEBT_DELTA:
        return Signal(
            DEBT_INCREASED,
            "Debt increasing",
            f"Debt-to-equity rose to {current:.2f} from {prior:.2f}.",
            NEGATIVE,
        )
    if delta <= -DEBT_DELTA:
        return Signal(
            DEBT_REDUCED,
            "Debt reducing",
            f"Debt-to-equity fell to {current:.2f} from {prior:.2f}.",
            POSITIVE,
        )
    return None


def earnings_signal(current: float | None, prior: float | None) -> Signal | None:
    """Flag a material change in earnings per share versus the prior year."""
    if current is None or prior is None or prior == 0:
        return None
    change = (current - prior) / abs(prior) * 100.0
    if change >= EARNINGS_CHANGE:
        return Signal(
            EARNINGS_GROWTH,
            "Earnings growing",
            f"EPS grew {change:.0f}% to {current:.2f} from {prior:.2f}.",
            POSITIVE,
        )
    if change <= -EARNINGS_CHANGE:
        return Signal(
            EARNINGS_DECLINE,
            "Earnings declining",
            f"EPS fell {abs(change):.0f}% to {current:.2f} from {prior:.2f}.",
            NEGATIVE,
        )
    return None


def dividend_signal(current: float | None, prior: float | None) -> Signal | None:
    """Flag a dividend initiation, increase, or cut versus the prior year."""
    if current is None or prior is None:
        return None
    if prior <= _DIVIDEND_EPS < current:
        return Signal(
            DIVIDEND_INITIATED,
            "Dividend initiated",
            f"Started paying a dividend of {current:.2f} per share.",
            POSITIVE,
        )
    if current - prior > _DIVIDEND_EPS:
        return Signal(
            DIVIDEND_INCREASED,
            "Dividend increased",
            f"Dividend per share rose to {current:.2f} from {prior:.2f}.",
            POSITIVE,
        )
    if prior - current > _DIVIDEND_EPS:
        return Signal(
            DIVIDEND_CUT,
            "Dividend cut",
            f"Dividend per share fell to {current:.2f} from {prior:.2f}.",
            NEGATIVE,
        )
    return None


def rating_signal(recommendation: str | None) -> Signal | None:
    """Surface the current BUY/SELL call as an actionable alert."""
    if recommendation is None:
        return None
    rating = recommendation.upper()
    if rating == "BUY":
        return Signal(
            RATING_BULLISH,
            "Rated BUY",
            "The blended valuation currently rates this a BUY.",
            POSITIVE,
        )
    if rating == "SELL":
        return Signal(
            RATING_BEARISH,
            "Rated SELL",
            "The blended valuation currently rates this a SELL.",
            NEGATIVE,
        )
    return None
