"""Intent classification for the AI assistant.

A pure, keyword-based classifier that maps a free-text question about a company
to one of a small set of intents. There is no machine learning or external LLM
here — the mapping is transparent and deterministic so every answer can be
traced back to the question that produced it.
"""

from __future__ import annotations

from enum import StrEnum


class Intent(StrEnum):
    """The topic a question is asking about."""

    VERDICT = "verdict"
    VALUATION = "valuation"
    GROWTH = "growth"
    CASH_FLOW = "cash_flow"
    RISK = "risk"
    DIVIDEND = "dividend"
    PROFITABILITY = "profitability"
    OVERVIEW = "overview"


# Checked in order; the first intent with a matching keyword wins. Decision
# phrases ("should I buy") are checked before topical ones so an explicit
# buy/sell question always maps to the verdict intent.
_INTENT_KEYWORDS: tuple[tuple[Intent, tuple[str, ...]], ...] = (
    (
        Intent.VERDICT,
        (
            "should i",
            "should we",
            "worth buying",
            "good buy",
            "good investment",
            "buy or sell",
            "invest in",
            "recommend",
            "is it a buy",
            "buy this",
        ),
    ),
    (Intent.DIVIDEND, ("dividend", "payout", "yield")),
    (Intent.GROWTH, ("growth", "growing", "grow", "cagr", "expanding")),
    (Intent.CASH_FLOW, ("cash flow", "cashflow", "free cash", "fcf", "cash generation")),
    (Intent.RISK, ("risk", "risky", "debt", "leverage", "solvency", "safe", "bankrupt")),
    (
        Intent.PROFITABILITY,
        ("profit", "margin", "roe", "roic", "return on", "profitable"),
    ),
    (
        Intent.VALUATION,
        (
            "value",
            "valuation",
            "intrinsic",
            "worth",
            "cheap",
            "expensive",
            "undervalued",
            "overvalued",
            "price",
            "fair",
        ),
    ),
)


def classify(question: str) -> Intent:
    """Map a free-text question to an :class:`Intent` (defaults to overview)."""
    text = question.casefold()
    for intent, keywords in _INTENT_KEYWORDS:
        if any(keyword in text for keyword in keywords):
            return intent
    return Intent.OVERVIEW
