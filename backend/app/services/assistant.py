"""AI assistant service — deterministic natural-language answers about a company.

Stateless: given a company symbol and a free-text question, it pulls the
already-computed valuation and ratio data, classifies the question's intent, and
composes a plain-language answer. No conversation history, no authentication,
and no external LLM — the answer is a transparent function of the platform's own
outputs.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.assistant import intents, narrative
from app.repositories import company as company_repo
from app.schemas.assistant import AssistantAnswer
from app.schemas.valuation import Recommendation
from app.services import ratios as ratios_service
from app.services import valuation as valuation_service


def _facts(symbol: str, db: Session) -> narrative.Facts:
    valuation = valuation_service.get_valuation(db, symbol)
    ratios = ratios_service.get_ratios(db, symbol)
    return narrative.Facts(
        symbol=symbol,
        recommendation=valuation.recommendation.value,
        discount=valuation.discount,
        intrinsic_value=valuation.intrinsic_value,
        current_price=valuation.current_price,
        roe=ratios.profitability.roe,
        roic=ratios.profitability.roic,
        net_margin=ratios.profitability.net_margin,
        debt_to_equity=ratios.debt.debt_to_equity,
        interest_coverage=ratios.debt.interest_coverage,
        current_ratio=ratios.liquidity.current_ratio,
        revenue_cagr=ratios.growth.revenue_cagr,
        eps_cagr=ratios.growth.eps_cagr,
        dividend_cagr=ratios.growth.dividend_cagr,
        dividend_yield=ratios.valuation.dividend_yield,
        free_cash_flow=ratios.cash_flow.free_cash_flow,
        fcf_yield=ratios.cash_flow.fcf_yield,
    )


def ask(db: Session, symbol: str, question: str) -> AssistantAnswer:
    """Answer a question about a company (404 if the company is missing)."""
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    facts = _facts(company.symbol, db)
    intent = intents.classify(question)
    answer, highlights = narrative.compose(intent, facts)
    return AssistantAnswer(
        symbol=company.symbol,
        question=question,
        intent=intent.value,
        answer=answer,
        highlights=highlights,
        recommendation=Recommendation(facts.recommendation),
    )
