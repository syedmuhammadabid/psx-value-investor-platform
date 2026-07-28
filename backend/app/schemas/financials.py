"""Financial statement response schemas."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from app.models.financial_statement import PeriodType

if TYPE_CHECKING:
    from app.models.financial_statement import FinancialStatement


class IncomeStatement(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    revenue: Decimal | None = None
    cost_of_revenue: Decimal | None = None
    gross_profit: Decimal | None = None
    operating_expenses: Decimal | None = None
    operating_income: Decimal | None = None
    interest_expense: Decimal | None = None
    pretax_income: Decimal | None = None
    tax_expense: Decimal | None = None
    net_income: Decimal | None = None
    eps_basic: Decimal | None = None
    shares_outstanding: Decimal | None = None


class BalanceSheet(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    cash_and_equivalents: Decimal | None = None
    inventory: Decimal | None = None
    current_assets: Decimal | None = None
    total_assets: Decimal | None = None
    current_liabilities: Decimal | None = None
    total_debt: Decimal | None = None
    total_liabilities: Decimal | None = None
    total_equity: Decimal | None = None


class CashFlow(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    operating_cash_flow: Decimal | None = None
    capital_expenditure: Decimal | None = None
    investing_cash_flow: Decimal | None = None
    financing_cash_flow: Decimal | None = None
    dividends_paid: Decimal | None = None
    free_cash_flow: Decimal | None = None


class FinancialPeriod(BaseModel):
    """One reporting period with all three statements."""

    fiscal_year: int
    fiscal_period: str
    period_end: date
    currency: str
    income_statement: IncomeStatement
    balance_sheet: BalanceSheet
    cash_flow: CashFlow

    @classmethod
    def from_model(cls, statement: FinancialStatement) -> FinancialPeriod:
        cash_flow = CashFlow.model_validate(statement)
        if statement.operating_cash_flow is not None and statement.capital_expenditure is not None:
            # CapEx is stored as a negative outflow; FCF = OCF + CapEx.
            cash_flow.free_cash_flow = statement.operating_cash_flow + statement.capital_expenditure
        return cls(
            fiscal_year=statement.fiscal_year,
            fiscal_period=statement.fiscal_period,
            period_end=statement.period_end,
            currency=statement.currency,
            income_statement=IncomeStatement.model_validate(statement),
            balance_sheet=BalanceSheet.model_validate(statement),
            cash_flow=cash_flow,
        )


class FinancialStatements(BaseModel):
    """A company's financials for a chosen cadence, newest period first."""

    symbol: str
    period_type: PeriodType
    periods: list[FinancialPeriod]
