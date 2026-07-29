"""Scores service — assembles the investment scorecard for a company.

Stateless: reuses the ratio engine for the composite-score inputs and the latest
two annual statements for the Piotroski, Altman, and Magic Formula figures, then
maps the pure scorecard results onto the response schema.
"""

from __future__ import annotations

from decimal import Decimal

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.calculations import ratios as calc
from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType
from app.repositories import company as company_repo
from app.repositories import financials as financials_repo
from app.schemas.ratios import FinancialRatios
from app.schemas.scores import (
    AltmanScore,
    CompanyScores,
    CompositeScore,
    MagicFormula,
    PiotroskiScore,
    ScoreCheck,
    ScoreRating,
)
from app.scores import scorecard
from app.services import ratios as ratios_service

# The F-Score compares the latest annual period against the one before it.
_TREND_PERIODS = 2


def _f(value: Decimal | None) -> float | None:
    return float(value) if value is not None else None


def _checks(checks: list[scorecard.ScoreCheck]) -> list[ScoreCheck]:
    return [ScoreCheck(label=c.label, detail=c.detail, passed=c.passed) for c in checks]


def _composite(key: str, label: str, result: scorecard.Composite) -> CompositeScore:
    return CompositeScore(
        key=key,
        label=label,
        value=result.value,
        rating=ScoreRating(result.rating),
        checks=_checks(result.checks),
    )


def _composites(ratios: FinancialRatios) -> list[CompositeScore]:
    prof, val, debt = ratios.profitability, ratios.valuation, ratios.debt
    liq, cash, growth = ratios.liquidity, ratios.cash_flow, ratios.growth
    return [
        _composite(
            "financial_health",
            "Financial Health",
            scorecard.financial_health(
                debt_to_equity=debt.debt_to_equity,
                free_cash_flow=cash.free_cash_flow,
                net_margin=prof.net_margin,
                revenue_cagr=growth.revenue_cagr,
                current_ratio=liq.current_ratio,
            ),
        ),
        _composite(
            "buffett",
            "Buffett Score",
            scorecard.buffett(
                roe=prof.roe,
                roic=prof.roic,
                debt_to_equity=debt.debt_to_equity,
                eps_cagr=growth.eps_cagr,
                dividend_yield=val.dividend_yield,
                free_cash_flow=cash.free_cash_flow,
            ),
        ),
        _composite(
            "graham",
            "Graham Score",
            scorecard.graham(
                pe=val.pe,
                pb=val.pb,
                debt_to_equity=debt.debt_to_equity,
                current_ratio=liq.current_ratio,
                # Net margin shares the sign of net income, so it stands in for the
                # "positive earnings" test (net income is not exposed by the ratios).
                net_income=prof.net_margin,
            ),
        ),
        _composite(
            "quality",
            "Quality Score",
            scorecard.quality(
                roic=prof.roic,
                eps_cagr=growth.eps_cagr,
                free_cash_flow=cash.free_cash_flow,
                debt_to_equity=debt.debt_to_equity,
                pe=val.pe,
            ),
        ),
    ]


def _period_inputs(s: FinancialStatement) -> scorecard.PeriodInputs:
    return scorecard.PeriodInputs(
        net_income=_f(s.net_income),
        total_assets=_f(s.total_assets),
        operating_cash_flow=_f(s.operating_cash_flow),
        total_debt=_f(s.total_debt),
        current_assets=_f(s.current_assets),
        current_liabilities=_f(s.current_liabilities),
        shares_outstanding=_f(s.shares_outstanding),
        gross_profit=_f(s.gross_profit),
        revenue=_f(s.revenue),
    )


def _piotroski(
    latest: FinancialStatement | None, prior: FinancialStatement | None
) -> PiotroskiScore:
    if latest is None or prior is None:
        return PiotroskiScore(value=None, rating=scorecard.RATING_NA, checks=[])
    result = scorecard.piotroski(_period_inputs(latest), _period_inputs(prior))
    return PiotroskiScore(value=result.value, rating=result.rating, checks=_checks(result.checks))


def _altman(company: Company, latest: FinancialStatement | None) -> AltmanScore:
    if latest is None:
        return AltmanScore(value=None, band=scorecard.RATING_NA, detail="Insufficient data")
    result = scorecard.altman_z(
        current_assets=_f(latest.current_assets),
        current_liabilities=_f(latest.current_liabilities),
        total_assets=_f(latest.total_assets),
        # Retained earnings are not stored; total equity is the closest proxy.
        retained_earnings=_f(latest.total_equity),
        total_liabilities=_f(latest.total_liabilities),
        operating_income=_f(latest.operating_income),
        revenue=_f(latest.revenue),
        market_cap=_f(company.market_cap),
    )
    return AltmanScore(value=result.value, band=result.band, detail=result.detail)


def _magic(
    company: Company, latest: FinancialStatement | None, ratios: FinancialRatios
) -> MagicFormula:
    if latest is None:
        return MagicFormula(roic=ratios.profitability.roic, earnings_yield=None, detail="No data")
    ev = calc.enterprise_value(
        _f(company.market_cap), _f(latest.total_debt), _f(latest.cash_and_equivalents)
    )
    result = scorecard.magic_formula(
        roic=ratios.profitability.roic,
        operating_income=_f(latest.operating_income),
        enterprise_value=ev,
    )
    return MagicFormula(
        roic=result.roic, earnings_yield=result.earnings_yield, detail=result.detail
    )


def get_scores(db: Session, symbol: str) -> CompanyScores:
    """Return the full investment scorecard for a company (404 if it is missing)."""
    company = company_repo.get_by_symbol(db, symbol)
    if company is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Company '{symbol}' not found.",
        )

    ratios = ratios_service.get_ratios(db, company.symbol)
    annual = financials_repo.list_financials(
        db, company.id, period_type=PeriodType.ANNUAL, limit=_TREND_PERIODS
    )
    latest = annual[0] if annual else None
    prior = annual[1] if len(annual) >= _TREND_PERIODS else None

    return CompanyScores(
        symbol=company.symbol,
        composites=_composites(ratios),
        piotroski=_piotroski(latest, prior),
        altman_z=_altman(company, latest),
        magic_formula=_magic(company, latest, ratios),
    )
