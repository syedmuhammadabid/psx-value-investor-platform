"""auth: users, watchlists, portfolio positions, alert subscriptions

Revision ID: 0004_auth
Revises: 0003_data_pipeline
Create Date: 2026-08-04

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0004_auth"
down_revision = "0003_data_pipeline"
branch_labels = None
depends_on = None


def _timestamps() -> tuple[sa.Column, sa.Column]:
    return (
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
    )


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("full_name", sa.String(length=200), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        *_timestamps(),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table(
        "watchlist_items",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "symbol", name="uq_watchlist_user_symbol"),
    )
    op.create_index("ix_watchlist_items_user_id", "watchlist_items", ["user_id"])

    op.create_table(
        "portfolio_positions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=24, scale=4), nullable=False),
        sa.Column("average_cost", sa.Numeric(precision=24, scale=4), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "symbol", name="uq_portfolio_user_symbol"),
    )
    op.create_index("ix_portfolio_positions_user_id", "portfolio_positions", ["user_id"])

    op.create_table(
        "alert_subscriptions",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("symbol", sa.String(length=20), nullable=False),
        *_timestamps(),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "symbol", name="uq_alert_sub_user_symbol"),
    )
    op.create_index("ix_alert_subscriptions_user_id", "alert_subscriptions", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_alert_subscriptions_user_id", table_name="alert_subscriptions")
    op.drop_table("alert_subscriptions")
    op.drop_index("ix_portfolio_positions_user_id", table_name="portfolio_positions")
    op.drop_table("portfolio_positions")
    op.drop_index("ix_watchlist_items_user_id", table_name="watchlist_items")
    op.drop_table("watchlist_items")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
