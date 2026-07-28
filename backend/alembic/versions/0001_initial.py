"""initial companies and sectors

Revision ID: 0001_initial
Revises:
Create Date: 2026-07-28

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "sectors",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
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
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_sectors_name", "sectors", ["name"], unique=True)

    op.create_table(
        "companies",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("sector_id", sa.Uuid(), nullable=True),
        sa.Column("industry", sa.String(length=160), nullable=True),
        sa.Column("market_cap", sa.Numeric(precision=24, scale=2), nullable=True),
        sa.Column("current_price", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("fifty_two_week_high", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("fifty_two_week_low", sa.Numeric(precision=20, scale=4), nullable=True),
        sa.Column("dividend_yield", sa.Numeric(precision=8, scale=4), nullable=True),
        sa.Column("website", sa.String(length=255), nullable=True),
        sa.Column("fiscal_year_end", sa.String(length=40), nullable=True),
        sa.Column("listing_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column(
            "is_active",
            sa.Boolean(),
            server_default=sa.text("true"),
            nullable=False,
        ),
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
        sa.ForeignKeyConstraint(["sector_id"], ["sectors.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_symbol", "companies", ["symbol"], unique=True)
    op.create_index("ix_companies_name", "companies", ["name"])
    op.create_index("ix_companies_sector_id", "companies", ["sector_id"])
    op.create_index("ix_companies_industry", "companies", ["industry"])


def downgrade() -> None:
    op.drop_index("ix_companies_industry", table_name="companies")
    op.drop_index("ix_companies_sector_id", table_name="companies")
    op.drop_index("ix_companies_name", table_name="companies")
    op.drop_index("ix_companies_symbol", table_name="companies")
    op.drop_table("companies")
    op.drop_index("ix_sectors_name", table_name="sectors")
    op.drop_table("sectors")
