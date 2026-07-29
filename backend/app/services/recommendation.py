"""Explainable recommendation service — the headline call plus its reasons."""

from __future__ import annotations

from sqlalchemy.orm import Session

from app.schemas.recommendation import (
    RecommendationReason,
    RecommendationReport,
    Sentiment,
)
from app.schemas.valuation import Recommendation
from app.services import ratios as ratios_service
from app.services import valuation as valuation_service
from app.valuation import recommendation as reasons_model


def _summary(symbol: str, recommendation: Recommendation, discount: float | None) -> str:
    """Compose a one-line verdict that mirrors the recommendation and discount."""
    if recommendation is Recommendation.BUY:
        base = f"{symbol} looks undervalued"
    elif recommendation is Recommendation.SELL:
        base = f"{symbol} looks overvalued"
    else:
        base = f"{symbol} appears fairly valued"

    if discount is None:
        return f"{base} — intrinsic value could not be estimated from available data."
    if discount > 0:
        return f"{base}, trading {discount:.0f}% below its estimated intrinsic value."
    if discount < 0:
        return f"{base}, trading {abs(discount):.0f}% above its estimated intrinsic value."
    return f"{base}, trading in line with its estimated intrinsic value."


def get_recommendation(db: Session, symbol: str) -> RecommendationReport:
    """Return the recommendation with explainable reasons (404 if company missing)."""
    valuation = valuation_service.get_valuation(db, symbol)
    ratios = ratios_service.get_ratios(db, symbol)

    factors = reasons_model.build_reasons(
        discount=valuation.discount,
        roe=ratios.profitability.roe,
        roic=ratios.profitability.roic,
        net_margin=ratios.profitability.net_margin,
        debt_to_equity=ratios.debt.debt_to_equity,
        eps_cagr=ratios.growth.eps_cagr,
        dividend_cagr=ratios.growth.dividend_cagr,
        revenue_cagr=ratios.growth.revenue_cagr,
        interest_coverage=ratios.debt.interest_coverage,
        current_ratio=ratios.liquidity.current_ratio,
    )
    reasons = [
        RecommendationReason(
            label=factor.label,
            detail=factor.detail,
            sentiment=Sentiment(factor.sentiment),
        )
        for factor in factors
    ]

    return RecommendationReport(
        symbol=valuation.symbol,
        recommendation=valuation.recommendation,
        summary=_summary(valuation.symbol, valuation.recommendation, valuation.discount),
        intrinsic_value=valuation.intrinsic_value,
        current_price=valuation.current_price,
        discount=valuation.discount,
        reasons=reasons,
    )
