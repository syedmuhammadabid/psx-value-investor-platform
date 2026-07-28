"""Pure financial-ratio calculations.

Every function is deterministic and side-effect free. Inputs may be missing
(``None``) and denominators may be zero; in those cases the function returns
``None`` rather than raising, so the caller always gets a well-defined result.

All values are treated as plain floats. Callers are responsible for currency
and unit normalisation (PKR) before calling in, and for presentation (e.g.
converting a margin fraction to a percentage) after calling out.
"""

from __future__ import annotations

Number = float | int | None


def safe_div(numerator: Number, denominator: Number) -> float | None:
    """Divide two numbers, returning ``None`` on missing input or zero divisor."""
    if numerator is None or denominator is None:
        return None
    if denominator == 0:
        return None
    return float(numerator) / float(denominator)


# --------------------------------------------------------------------------- #
# Profitability (returns are expressed as fractions, e.g. 0.23 == 23%)
# --------------------------------------------------------------------------- #
def gross_margin(gross_profit: Number, revenue: Number) -> float | None:
    return safe_div(gross_profit, revenue)


def operating_margin(operating_income: Number, revenue: Number) -> float | None:
    return safe_div(operating_income, revenue)


def net_margin(net_income: Number, revenue: Number) -> float | None:
    return safe_div(net_income, revenue)


def return_on_equity(net_income: Number, total_equity: Number) -> float | None:
    return safe_div(net_income, total_equity)


def return_on_assets(net_income: Number, total_assets: Number) -> float | None:
    return safe_div(net_income, total_assets)


def effective_tax_rate(tax_expense: Number, pretax_income: Number) -> float | None:
    return safe_div(tax_expense, pretax_income)


def invested_capital(
    total_debt: Number, total_equity: Number, cash_and_equivalents: Number
) -> float | None:
    """Debt + equity net of cash. ``None`` if debt and equity are both missing."""
    if total_debt is None and total_equity is None:
        return None
    debt = float(total_debt) if total_debt is not None else 0.0
    equity = float(total_equity) if total_equity is not None else 0.0
    cash = float(cash_and_equivalents) if cash_and_equivalents is not None else 0.0
    return debt + equity - cash


def return_on_invested_capital(  # noqa: PLR0917
    operating_income: Number,
    tax_expense: Number,
    pretax_income: Number,
    total_debt: Number,
    total_equity: Number,
    cash_and_equivalents: Number,
) -> float | None:
    """ROIC = NOPAT / invested capital.

    NOPAT is operating income after tax, using the effective tax rate (defaulting
    to zero when it cannot be derived). Invested capital is debt + equity - cash.
    """
    if operating_income is None:
        return None
    tax_rate = effective_tax_rate(tax_expense, pretax_income)
    if tax_rate is None:
        tax_rate = 0.0
    nopat = float(operating_income) * (1.0 - tax_rate)
    capital = invested_capital(total_debt, total_equity, cash_and_equivalents)
    return safe_div(nopat, capital)


# --------------------------------------------------------------------------- #
# Valuation (multiples are plain numbers; market_cap is current)
# --------------------------------------------------------------------------- #
def price_to_earnings(market_cap: Number, net_income: Number) -> float | None:
    """P/E; ``None`` for non-positive earnings (a negative P/E is not meaningful)."""
    if net_income is None or float(net_income) <= 0:
        return None
    return safe_div(market_cap, net_income)


def price_to_book(market_cap: Number, total_equity: Number) -> float | None:
    if total_equity is None or float(total_equity) <= 0:
        return None
    return safe_div(market_cap, total_equity)


def price_to_sales(market_cap: Number, revenue: Number) -> float | None:
    return safe_div(market_cap, revenue)


def peg_ratio(pe: Number, earnings_growth: Number) -> float | None:
    """PEG = P/E divided by the earnings growth rate expressed as a percentage.

    ``earnings_growth`` is a fraction (0.15 == 15%). Non-positive growth yields
    ``None`` because PEG is undefined for flat or shrinking earnings.
    """
    if pe is None or earnings_growth is None or float(earnings_growth) <= 0:
        return None
    return safe_div(pe, float(earnings_growth) * 100.0)


def enterprise_value(
    market_cap: Number, total_debt: Number, cash_and_equivalents: Number
) -> float | None:
    if market_cap is None:
        return None
    debt = float(total_debt) if total_debt is not None else 0.0
    cash = float(cash_and_equivalents) if cash_and_equivalents is not None else 0.0
    return float(market_cap) + debt - cash


def ebitda(
    operating_income: Number, operating_cash_flow: Number, net_income: Number
) -> float | None:
    """Approximate EBITDA as operating income plus a depreciation proxy.

    Depreciation & amortisation are not captured as a separate line item, so we
    proxy the non-cash add-back with ``operating_cash_flow - net_income`` when
    positive. This is an approximation suitable for illustrative data.
    """
    if operating_income is None:
        return None
    da_proxy = 0.0
    if operating_cash_flow is not None and net_income is not None:
        da_proxy = max(float(operating_cash_flow) - float(net_income), 0.0)
    return float(operating_income) + da_proxy


def ev_to_ebitda(enterprise_value_: Number, ebitda_: Number) -> float | None:
    if ebitda_ is None or float(ebitda_) <= 0:
        return None
    return safe_div(enterprise_value_, ebitda_)


# --------------------------------------------------------------------------- #
# Debt
# --------------------------------------------------------------------------- #
def debt_to_equity(total_debt: Number, total_equity: Number) -> float | None:
    return safe_div(total_debt, total_equity)


def interest_coverage(operating_income: Number, interest_expense: Number) -> float | None:
    """EBIT / interest expense; ``None`` when there is no interest burden."""
    if interest_expense is None or float(interest_expense) == 0:
        return None
    return safe_div(operating_income, interest_expense)


# --------------------------------------------------------------------------- #
# Liquidity
# --------------------------------------------------------------------------- #
def current_ratio(current_assets: Number, current_liabilities: Number) -> float | None:
    return safe_div(current_assets, current_liabilities)


def quick_ratio(
    current_assets: Number, inventory: Number, current_liabilities: Number
) -> float | None:
    if current_assets is None:
        return None
    inv = float(inventory) if inventory is not None else 0.0
    return safe_div(float(current_assets) - inv, current_liabilities)


# --------------------------------------------------------------------------- #
# Cash flow
# --------------------------------------------------------------------------- #
def free_cash_flow(operating_cash_flow: Number, capital_expenditure: Number) -> float | None:
    """FCF = operating cash flow + capital expenditure (CapEx stored negative)."""
    if operating_cash_flow is None or capital_expenditure is None:
        return None
    return float(operating_cash_flow) + float(capital_expenditure)


def fcf_yield(free_cash_flow_: Number, market_cap: Number) -> float | None:
    return safe_div(free_cash_flow_, market_cap)


# --------------------------------------------------------------------------- #
# Growth
# --------------------------------------------------------------------------- #
def cagr(earliest: Number, latest: Number, years: Number) -> float | None:
    """Compound annual growth rate over ``years`` intervals, as a fraction.

    Returns ``None`` unless both endpoints are positive and ``years`` >= 1, since
    CAGR is undefined for non-positive endpoints.
    """
    if earliest is None or latest is None or years is None:
        return None
    if float(earliest) <= 0 or float(latest) <= 0 or float(years) < 1:
        return None
    return float((float(latest) / float(earliest)) ** (1.0 / float(years)) - 1.0)
