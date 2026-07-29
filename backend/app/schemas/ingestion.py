"""Ingestion input and report schemas."""

from __future__ import annotations

import uuid
from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field

from app.models.financial_statement import PeriodType
from app.scraper.validation import Severity


class RawFinancialRecord(BaseModel):
    """A single financial period as received from a data source.

    Numeric fields are in the filing's reported ``scale``; the pipeline scales
    them to base PKR. Unknown fields are rejected so a malformed source cannot
    silently write garbage.
    """

    model_config = ConfigDict(extra="forbid")

    symbol: str = Field(min_length=1, max_length=20)
    period_type: PeriodType
    fiscal_year: int = Field(ge=1900, le=2200)
    fiscal_period: str | None = None
    period_end: date
    currency: str = Field(default="PKR", min_length=3, max_length=3)
    scale: str | None = None

    # Provenance
    source_url: str | None = Field(default=None, max_length=1000)
    source_page: int | None = Field(default=None, ge=1)

    # Income statement
    revenue: float | None = None
    cost_of_revenue: float | None = None
    gross_profit: float | None = None
    operating_expenses: float | None = None
    operating_income: float | None = None
    interest_expense: float | None = None
    pretax_income: float | None = None
    tax_expense: float | None = None
    net_income: float | None = None
    eps_basic: float | None = None
    shares_outstanding: float | None = None

    # Balance sheet
    cash_and_equivalents: float | None = None
    inventory: float | None = None
    current_assets: float | None = None
    total_assets: float | None = None
    current_liabilities: float | None = None
    total_debt: float | None = None
    total_liabilities: float | None = None
    total_equity: float | None = None

    # Cash flow
    operating_cash_flow: float | None = None
    capital_expenditure: float | None = None
    investing_cash_flow: float | None = None
    financing_cash_flow: float | None = None
    dividends_paid: float | None = None


class RecordStatus(StrEnum):
    """The outcome of ingesting a single record."""

    INGESTED = "ingested"
    UPDATED = "updated"
    SKIPPED = "skipped"
    REJECTED = "rejected"


class ValidationIssueOut(BaseModel):
    """A validation issue surfaced in the ingestion report."""

    code: str
    message: str
    severity: Severity


class RecordOutcome(BaseModel):
    """What happened to one record during ingestion."""

    symbol: str
    period_type: PeriodType
    fiscal_year: int
    fiscal_period: str
    status: RecordStatus
    issues: list[ValidationIssueOut] = Field(default_factory=list)


class IngestionReport(BaseModel):
    """Summary of an ingestion run."""

    source: str
    job_id: uuid.UUID
    status: str
    processed: int
    ingested: int
    updated: int
    skipped: int
    rejected: int
    flagged: int
    outcomes: list[RecordOutcome]
