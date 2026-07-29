"""Alerts service — evaluates which alert conditions currently hold.

This is a stateless engine: given a company's latest valuation and its two most
recent annual statements, it reports the conditions that would trigger a
notification (price vs intrinsic value, ROIC/debt/earnings/dividend moves, and
the standing recommendation). Delivering those alerts to subscribed users
(browser, email, Telegram) requires authentication and is out of scope here.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.alerts import rules
from app.calculations import ratios as calc
from app.models.financial_statement import FinancialStatement, PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.schemas.alerts import AlertReport, AlertSentiment, AlertSignal
from app.services import valuation as valuation_service

# We compare the latest annual period against the one before it.
_TREND_PERIODS = 2


def _f(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _roic_pct(s: FinancialStatement) -> float | None:
    roic = calc.return_on_invested_capital(
        _f(s.operating_income),
        _f(s.tax_expense),
        _f(s.pretax_income),
        _f(s.total_debt),
        _f(s.total_equity),
        _f(s.cash_and_equivalents),
    )
    return roic * 100.0 if roic is not None else None


def _debt_to_equity(s: FinancialStatement) -> float | None:
    return calc.debt_to_equity(_f(s.total_debt), _f(s.total_equity))


def _dividend_per_share(s: FinancialStatement) -> float | None:
    dividends = _f(s.dividends_paid)
    # Dividends paid are stored as a negative outflow; per share uses magnitude.
    total = abs(dividends) if dividends is not None else None
    return calc.safe_div(total, _f(s.shares_outstanding))


def _trend_signals(latest: FinancialStatement, prior: FinancialStatement) -> list[rules.Signal]:
    candidates = (
        rules.roic_signal(_roic_pct(latest), _roic_pct(prior)),
        rules.debt_signal(_debt_to_equity(latest), _debt_to_equity(prior)),
        rules.earnings_signal(_f(latest.eps_basic), _f(prior.eps_basic)),
        rules.dividend_signal(_dividend_per_share(latest), _dividend_per_share(prior)),
    )
    return [signal for signal in candidates if signal is not None]


def get_alerts(db: Session, symbol: str) -> AlertReport:
    """Return the alert conditions active for a company (404 if it is missing)."""
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    valuation = valuation_service.get_valuation(db, company.symbol)
    signals: list[rules.Signal] = []
    for signal in (
        rules.valuation_signal(valuation.discount),
        rules.rating_signal(valuation.recommendation.value),
    ):
        if signal is not None:
            signals.append(signal)

    annual = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.ANNUAL, limit=_TREND_PERIODS
    )
    if len(annual) >= _TREND_PERIODS:
        signals.extend(_trend_signals(annual[0], annual[1]))

    alerts = [
        AlertSignal(
            type=signal.type,
            title=signal.title,
            detail=signal.detail,
            sentiment=AlertSentiment(signal.sentiment),
        )
        for signal in signals
    ]
    return AlertReport(symbol=company.symbol, alerts=alerts)
