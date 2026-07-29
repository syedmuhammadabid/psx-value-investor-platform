"""Pure, deterministic valuation models.

Each model returns an estimated intrinsic value **per share** (or ``None`` when
inputs are insufficient). The models are intentionally free of I/O so they can
be unit-tested exhaustively (see PROJECT_ROADMAP.md — target >=90% coverage on
``valuation/``). The service layer gathers inputs from the database and blends
the model outputs into a single weighted intrinsic value.

Assumptions (discount rate, terminal growth, fair multiples) reflect the
higher-risk Pakistani market and are surfaced to users for transparency.
"""

from __future__ import annotations

import math

Number = float | int | None

# --- Default assumptions -------------------------------------------------
# Required return / cost of equity — Pakistan carries a high risk-free rate.
DEFAULT_DISCOUNT_RATE = 0.15
# Long-run terminal growth (roughly inflation + real GDP).
DEFAULT_TERMINAL_GROWTH = 0.04
# Explicit DCF projection horizon in years.
DEFAULT_PROJECTION_YEARS = 5
# Fallback fair multiples when peer/market data is unavailable.
DEFAULT_MARKET_PE = 10.0
DEFAULT_EV_EBITDA = 8.0
# Graham's revised valuation constant (V = sqrt(22.5 * EPS * BVPS)).
GRAHAM_MULTIPLIER = 22.5

# Model identifiers and their blend weights (must sum to 1.0).
MODEL_WEIGHTS: dict[str, float] = {
    "Discounted Cash Flow": 0.30,
    "Graham Intrinsic Value": 0.20,
    "Historical P/E": 0.15,
    "Industry P/E": 0.10,
    "EV/EBITDA": 0.10,
    "Residual Income": 0.10,
    "Dividend Discount Model": 0.05,
}


def _clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def discounted_cash_flow(
    free_cash_flow: Number,
    shares_outstanding: Number,
    net_debt: Number,
    *,
    growth: Number,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    terminal_growth: float = DEFAULT_TERMINAL_GROWTH,
    years: int = DEFAULT_PROJECTION_YEARS,
) -> float | None:
    """Two-stage DCF: discount projected FCF plus a Gordon terminal value.

    Returns equity value per share. ``None`` when FCF is non-positive, shares
    are missing, or the discount rate does not exceed terminal growth.
    """
    if free_cash_flow is None or free_cash_flow <= 0:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None
    if discount_rate <= terminal_growth:
        return None

    g = _clamp(float(growth) if growth is not None else 0.0, 0.0, 0.15)
    debt = float(net_debt) if net_debt is not None else 0.0

    enterprise = 0.0
    projected = float(free_cash_flow)
    for year in range(1, years + 1):
        projected = float(free_cash_flow) * (1.0 + g) ** year
        enterprise += projected / (1.0 + discount_rate) ** year

    terminal = projected * (1.0 + terminal_growth) / (discount_rate - terminal_growth)
    enterprise += terminal / (1.0 + discount_rate) ** years

    equity = enterprise - debt
    if equity <= 0:
        return None
    return equity / float(shares_outstanding)


def graham_number(eps: Number, book_value_per_share: Number) -> float | None:
    """Graham's number: sqrt(22.5 * EPS * BVPS). Requires positive inputs."""
    if eps is None or book_value_per_share is None:
        return None
    if eps <= 0 or book_value_per_share <= 0:
        return None
    return math.sqrt(GRAHAM_MULTIPLIER * float(eps) * float(book_value_per_share))


def historical_pe_value(normalized_eps: Number, historical_pe: Number) -> float | None:
    """Value smoothed (normalized) earnings at the company's own P/E multiple."""
    if normalized_eps is None or historical_pe is None:
        return None
    if normalized_eps <= 0 or historical_pe <= 0:
        return None
    return float(historical_pe) * float(normalized_eps)


def industry_pe_value(eps: Number, industry_pe: Number) -> float | None:
    """Value current earnings at the sector's average P/E multiple."""
    if eps is None or industry_pe is None:
        return None
    if eps <= 0 or industry_pe <= 0:
        return None
    return float(industry_pe) * float(eps)


def ev_ebitda_value(
    ebitda: Number,
    ev_ebitda_multiple: float,
    net_debt: Number,
    shares_outstanding: Number,
) -> float | None:
    """Enterprise value from an EV/EBITDA multiple, less net debt, per share."""
    if ebitda is None or ebitda <= 0:
        return None
    if shares_outstanding is None or shares_outstanding <= 0:
        return None
    debt = float(net_debt) if net_debt is not None else 0.0
    equity = float(ebitda) * ev_ebitda_multiple - debt
    if equity <= 0:
        return None
    return equity / float(shares_outstanding)


def residual_income_value(
    book_value_per_share: Number,
    roe: Number,
    cost_of_equity: float = DEFAULT_DISCOUNT_RATE,
    growth: Number = None,
    terminal_growth: float = DEFAULT_TERMINAL_GROWTH,
) -> float | None:
    """Single-stage residual income: BVPS + (ROE - r) * BVPS / (r - g).

    ``roe`` is a fraction (0.23 == 23%). Perpetual growth is capped at the
    terminal rate so the denominator stays stable. Returns ``None`` for missing
    book value/ROE or a non-positive result.
    """
    if book_value_per_share is None or book_value_per_share <= 0:
        return None
    if roe is None:
        return None
    g = _clamp(float(growth) if growth is not None else 0.0, 0.0, terminal_growth)
    denominator = cost_of_equity - g
    if denominator <= 0:
        return None
    residual = (float(roe) - cost_of_equity) * float(book_value_per_share)
    value = float(book_value_per_share) + residual / denominator
    if value <= 0:
        return None
    return value


def dividend_discount_value(
    dividend_per_share: Number,
    growth: Number,
    discount_rate: float = DEFAULT_DISCOUNT_RATE,
    terminal_growth: float = DEFAULT_TERMINAL_GROWTH,
) -> float | None:
    """Gordon growth DDM: D0 * (1 + g) / (r - g). Dividend payers only.

    Perpetual growth is capped at the terminal rate to keep the model stable.
    """
    if dividend_per_share is None or dividend_per_share <= 0:
        return None
    g = _clamp(float(growth) if growth is not None else 0.0, 0.0, terminal_growth)
    denominator = discount_rate - g
    if denominator <= 0:
        return None
    return float(dividend_per_share) * (1.0 + g) / denominator


def weighted_intrinsic_value(components: list[tuple[float | None, float]]) -> float | None:
    """Blend model outputs, re-normalizing weights over applicable models.

    Non-positive or missing model values are ignored so a single broken model
    never drags the blended value down. Returns ``None`` if nothing applies.
    """
    total_value = 0.0
    total_weight = 0.0
    for value, weight in components:
        if value is None or value <= 0:
            continue
        total_value += value * weight
        total_weight += weight
    if total_weight == 0:
        return None
    return total_value / total_weight


def classify_recommendation(discount_pct: float | None) -> str:
    """Map a discount-to-intrinsic percentage to BUY / HOLD / SELL."""
    buy_threshold = 15.0
    sell_threshold = -15.0
    if discount_pct is None:
        return "HOLD"
    if discount_pct >= buy_threshold:
        return "BUY"
    if discount_pct <= sell_threshold:
        return "SELL"
    return "HOLD"
