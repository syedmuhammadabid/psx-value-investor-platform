"""financial statements

Revision ID: 0002_financials
Revises: 0001_initial
Create Date: 2026-07-28

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0002_financials"
down_revision = "0001_initial"
branch_labels = None
depends_on = None

_MONEY = sa.Numeric(precision=24, scale=2)


def upgrade() -> None:
    op.create_table(
        "financial_statements",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column(
            "period_type",
            sa.Enum("annual", "quarterly", name="period_type"),
            nullable=False,
        ),
        sa.Column("fiscal_year", sa.Integer(), nullable=False),
        sa.Column("fiscal_period", sa.String(length=8), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        # Income statement
        sa.Column("revenue", _MONEY, nullable=True),
        sa.Column("cost_of_revenue", _MONEY, nullable=True),
        sa.Column("gross_profit", _MONEY, nullable=True),
        sa.Column("operating_expenses", _MONEY, nullable=True),
        sa.Column("operating_income", _MONEY, nullable=True),
        sa.Column("interest_expense", _MONEY, nullable=True),
        sa.Column("pretax_income", _MONEY, nullable=True),
        sa.Column("tax_expense", _MONEY, nullable=True),
        sa.Column("net_income", _MONEY, nullable=True),
        sa.Column("eps_basic", sa.Numeric(precision=12, scale=4), nullable=True),
        sa.Column("shares_outstanding", _MONEY, nullable=True),
        # Balance sheet
        sa.Column("cash_and_equivalents", _MONEY, nullable=True),
        sa.Column("inventory", _MONEY, nullable=True),
        sa.Column("current_assets", _MONEY, nullable=True),
        sa.Column("total_assets", _MONEY, nullable=True),
        sa.Column("current_liabilities", _MONEY, nullable=True),
        sa.Column("total_debt", _MONEY, nullable=True),
        sa.Column("total_liabilities", _MONEY, nullable=True),
        sa.Column("total_equity", _MONEY, nullable=True),
        # Cash flow
        sa.Column("operating_cash_flow", _MONEY, nullable=True),
        sa.Column("capital_expenditure", _MONEY, nullable=True),
        sa.Column("investing_cash_flow", _MONEY, nullable=True),
        sa.Column("financing_cash_flow", _MONEY, nullable=True),
        sa.Column("dividends_paid", _MONEY, nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "company_id",
            "period_type",
            "fiscal_year",
            "fiscal_period",
            name="uq_financials_company_period",
        ),
    )
    op.create_index(
        "ix_financial_statements_company_id",
        "financial_statements",
        ["company_id"],
    )
    op.create_index(
        "ix_financial_statements_period_type",
        "financial_statements",
        ["period_type"],
    )
    op.create_index(
        "ix_financial_statements_fiscal_year",
        "financial_statements",
        ["fiscal_year"],
    )
    op.create_index(
        "ix_financial_statements_period_end",
        "financial_statements",
        ["period_end"],
    )


def downgrade() -> None:
    op.drop_index("ix_financial_statements_period_end", table_name="financial_statements")
    op.drop_index("ix_financial_statements_fiscal_year", table_name="financial_statements")
    op.drop_index("ix_financial_statements_period_type", table_name="financial_statements")
    op.drop_index("ix_financial_statements_company_id", table_name="financial_statements")
    op.drop_table("financial_statements")
    sa.Enum(name="period_type").drop(op.get_bind(), checkfirst=True)
