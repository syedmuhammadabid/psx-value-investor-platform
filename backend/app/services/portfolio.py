"""Portfolio analytics service — stateless holdings-in, analysis-out."""

from __future__ import annotations

from typing import NamedTuple

from sqlalchemy.orm import Session

from app.calculations import portfolio as calc
from app.repositories import company as company_repo
from app.schemas.portfolio import (
    HoldingAnalysis,
    PortfolioAnalysis,
    PortfolioHolding,
    PortfolioRequest,
    PortfolioSummary,
)
from app.schemas.valuation import Recommendation
from app.services import valuation as valuation_service

_REC_SCORE: dict[Recommendation, float] = {
    Recommendation.BUY: 100.0,
    Recommendation.HOLD: 50.0,
    Recommendation.SELL: 0.0,
}


class _Computed(NamedTuple):
    """Intermediate per-holding figures gathered before portfolio roll-up."""

    holding: PortfolioHolding
    name: str | None
    current_price: float | None
    intrinsic_value: float | None
    recommendation: Recommendation
    cost_basis: float
    market_value: float | None
    intrinsic_total: float | None


def _gather(db: Session, holding: PortfolioHolding) -> _Computed:
    """Enrich a submitted holding with valuation data and raw money figures."""
    valuation = valuation_service.get_valuation(db, holding.symbol)  # 404 if symbol unknown
    company = company_repo.get_by_symbol(db, holding.symbol)
    current = valuation.current_price
    intrinsic = valuation.intrinsic_value
    return _Computed(
        holding=holding,
        name=company.name if company is not None else None,
        current_price=current,
        intrinsic_value=intrinsic,
        recommendation=valuation.recommendation,
        cost_basis=holding.quantity * holding.average_cost,
        market_value=holding.quantity * current if current is not None else None,
        intrinsic_total=holding.quantity * intrinsic if intrinsic is not None else None,
    )


def _holding_analysis(row: _Computed, total_market_value: float | None) -> HoldingAnalysis:
    """Build the per-holding response from gathered figures and the portfolio total."""
    market_value = row.market_value
    gain_loss = market_value - row.cost_basis if market_value is not None else None
    gain_loss_pct = (
        gain_loss / row.cost_basis * 100.0 if gain_loss is not None and row.cost_basis > 0 else None
    )
    weight = (
        market_value / total_market_value * 100.0
        if market_value is not None and total_market_value
        else None
    )
    return HoldingAnalysis(
        symbol=row.holding.symbol,
        name=row.name,
        quantity=row.holding.quantity,
        average_cost=row.holding.average_cost,
        current_price=row.current_price,
        cost_basis=row.cost_basis,
        market_value=market_value,
        gain_loss=gain_loss,
        gain_loss_pct=gain_loss_pct,
        intrinsic_value=row.intrinsic_value,
        intrinsic_total=row.intrinsic_total,
        margin_of_safety=calc.margin_of_safety(row.intrinsic_value, row.current_price),
        expected_cagr=calc.expected_cagr(row.intrinsic_value, row.current_price),
        recommendation=row.recommendation,
        weight=weight,
    )


def _summary(rows: list[_Computed]) -> PortfolioSummary:
    """Roll gathered holdings up into portfolio-level analytics."""
    total_cost = sum(row.cost_basis for row in rows)

    market_values = [row.market_value for row in rows if row.market_value is not None]
    total_market = sum(market_values) if market_values else 0.0
    total_market_opt = total_market if total_market > 0 else None

    intrinsic_totals = [row.intrinsic_total for row in rows if row.intrinsic_total is not None]
    total_intrinsic = sum(intrinsic_totals) if intrinsic_totals else None

    total_gain_loss = total_market - total_cost if total_market_opt is not None else None
    total_gain_loss_pct = (
        total_gain_loss / total_cost * 100.0
        if total_gain_loss is not None and total_cost > 0
        else None
    )

    portfolio_mos = calc.margin_of_safety(total_intrinsic, total_market_opt)
    expected = calc.weighted_average(
        [
            (calc.expected_cagr(row.intrinsic_value, row.current_price), row.market_value or 0.0)
            for row in rows
        ]
    )
    conviction = calc.weighted_average(
        [(_REC_SCORE[row.recommendation], row.market_value or 0.0) for row in rows]
    )
    weight_fractions = (
        [value / total_market for value in market_values] if total_market_opt is not None else []
    )
    health = calc.health_score(
        valuation=calc.valuation_score(portfolio_mos),
        conviction=conviction,
        diversification=calc.diversification_score(weight_fractions),
    )

    return PortfolioSummary(
        holdings_count=len(rows),
        total_cost=total_cost,
        total_market_value=total_market_opt,
        total_gain_loss=total_gain_loss,
        total_gain_loss_pct=total_gain_loss_pct,
        total_intrinsic_value=total_intrinsic,
        margin_of_safety=portfolio_mos,
        expected_cagr=expected,
        health_score=health,
    )


def analyze_portfolio(db: Session, request: PortfolioRequest) -> PortfolioAnalysis:
    """Analyse a submitted portfolio (404 if any holding's symbol is unknown)."""
    rows = [_gather(db, holding) for holding in request.holdings]
    summary = _summary(rows)
    holdings = [_holding_analysis(row, summary.total_market_value) for row in rows]
    return PortfolioAnalysis(summary=summary, holdings=holdings)
