"""Investment-score response schemas."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel


class ScoreRating(StrEnum):
    """Coarse quality band for a 0-100 composite score."""

    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    WEAK = "weak"
    NA = "na"


class ScoreCheck(BaseModel):
    """A single pass/fail criterion behind a score (``passed`` null == no data)."""

    label: str
    detail: str
    passed: bool | None = None


class CompositeScore(BaseModel):
    """A 0-100 composite score with its underlying checks."""

    key: str
    label: str
    value: float | None = None
    rating: ScoreRating
    checks: list[ScoreCheck]


class PiotroskiScore(BaseModel):
    """The Piotroski F-Score (0-9) with its nine checks."""

    value: int | None = None
    max_score: int = 9
    rating: str
    checks: list[ScoreCheck]


class AltmanScore(BaseModel):
    """The Altman Z-Score with its distress band."""

    value: float | None = None
    band: str
    detail: str


class MagicFormula(BaseModel):
    """The two Magic Formula components, each as a percentage."""

    roic: float | None = None
    earnings_yield: float | None = None
    detail: str


class CompanyScores(BaseModel):
    """The full scorecard for a company."""

    symbol: str
    currency: str = "PKR"
    composites: list[CompositeScore]
    piotroski: PiotroskiScore
    altman_z: AltmanScore
    magic_formula: MagicFormula
