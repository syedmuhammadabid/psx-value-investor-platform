"""Tests for the assistant's pure intent classification and answer composition."""

from __future__ import annotations

import pytest

from app.assistant import narrative
from app.assistant.intents import Intent, classify

_FULL_FACTS = narrative.Facts(
    symbol="ENGRO",
    recommendation="BUY",
    discount=21.0,
    intrinsic_value=395.0,
    current_price=310.0,
    roe=23.0,
    roic=18.0,
    net_margin=12.5,
    debt_to_equity=0.45,
    interest_coverage=8.2,
    current_ratio=1.7,
    revenue_cagr=14.0,
    eps_cagr=11.0,
    dividend_cagr=9.0,
    dividend_yield=6.5,
    free_cash_flow=45000000000.0,
    fcf_yield=7.1,
)

_EMPTY_FACTS = narrative.Facts(
    symbol="SYS",
    recommendation="HOLD",
    discount=None,
    intrinsic_value=None,
    current_price=985.0,
    roe=None,
    roic=None,
    net_margin=None,
    debt_to_equity=None,
    interest_coverage=None,
    current_ratio=None,
    revenue_cagr=None,
    eps_cagr=None,
    dividend_cagr=None,
    dividend_yield=None,
    free_cash_flow=None,
    fcf_yield=None,
)


class TestClassify:
    @pytest.mark.parametrize(
        ("question", "expected"),
        [
            ("Should I buy ENGRO?", Intent.VERDICT),
            ("Is it a buy right now?", Intent.VERDICT),
            ("Would you recommend this stock?", Intent.VERDICT),
            ("What dividend does it pay?", Intent.DIVIDEND),
            ("How fast is revenue growing?", Intent.GROWTH),
            ("What is the CAGR?", Intent.GROWTH),
            ("Tell me about its free cash flow", Intent.CASH_FLOW),
            ("How much debt does it carry?", Intent.RISK),
            ("Is this a risky company?", Intent.RISK),
            ("What are the margins?", Intent.PROFITABILITY),
            ("What is the ROE?", Intent.PROFITABILITY),
            ("Is the stock undervalued?", Intent.VALUATION),
            ("What is it worth?", Intent.VALUATION),
            ("Tell me about this company", Intent.OVERVIEW),
            ("", Intent.OVERVIEW),
        ],
    )
    def test_classifies_questions(self, question: str, expected: Intent) -> None:
        assert classify(question) == expected

    def test_is_case_insensitive(self) -> None:
        assert classify("SHOULD I BUY?") == Intent.VERDICT

    def test_verdict_wins_over_valuation(self) -> None:
        # A decision phrase should take priority over a topical keyword.
        assert classify("Should I buy this undervalued stock?") == Intent.VERDICT


class TestCompose:
    @pytest.mark.parametrize("intent", list(Intent))
    def test_every_intent_produces_answer_and_highlights(self, intent: Intent) -> None:
        answer, highlights = narrative.compose(intent, _FULL_FACTS)
        assert answer
        assert "ENGRO" in answer or highlights
        assert highlights
        assert all(highlights)

    def test_verdict_mentions_recommendation_and_discount(self) -> None:
        answer, highlights = narrative.compose(Intent.VERDICT, _FULL_FACTS)
        assert "BUY" in answer
        assert "21% below" in answer
        assert "Recommendation: BUY" in highlights

    def test_valuation_uses_stance(self) -> None:
        answer, _ = narrative.compose(Intent.VALUATION, _FULL_FACTS)
        assert "undervalued" in answer
        assert "Rs 395.00" in answer

    def test_missing_data_degrades_gracefully(self) -> None:
        answer, highlights = narrative.compose(Intent.OVERVIEW, _EMPTY_FACTS)
        assert "n/a" in answer
        assert "could not be estimated" in answer
        assert highlights

    def test_overvalued_stance_for_sell(self) -> None:
        facts = _FULL_FACTS._replace(recommendation="SELL", discount=-12.0)
        answer, _ = narrative.compose(Intent.VALUATION, facts)
        assert "overvalued" in answer
        assert "12% above" in answer

    def test_fairly_valued_when_flat(self) -> None:
        facts = _FULL_FACTS._replace(recommendation="HOLD", discount=0.0)
        answer, _ = narrative.compose(Intent.OVERVIEW, facts)
        assert "fairly valued" in answer
        assert "in line with" in answer
