"""data pipeline: ingestion jobs and data sources

Revision ID: 0003_data_pipeline
Revises: 0002_financials
Create Date: 2026-07-29

"""

from __future__ import annotations

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "0003_data_pipeline"
down_revision = "0002_financials"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "ingestion_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("source", sa.String(length=200), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "running",
                "succeeded",
                "partial",
                "failed",
                name="ingestion_job_status",
            ),
            nullable=False,
        ),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("records_processed", sa.Integer(), nullable=False),
        sa.Column("records_ingested", sa.Integer(), nullable=False),
        sa.Column("records_updated", sa.Integer(), nullable=False),
        sa.Column("records_skipped", sa.Integer(), nullable=False),
        sa.Column("records_rejected", sa.Integer(), nullable=False),
        sa.Column("records_flagged", sa.Integer(), nullable=False),
        sa.Column("error", sa.Text(), nullable=True),
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
    op.create_index("ix_ingestion_jobs_status", "ingestion_jobs", ["status"])

    op.create_table(
        "data_sources",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("company_id", sa.Uuid(), nullable=False),
        sa.Column("financial_statement_id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=True),
        sa.Column("source_type", sa.String(length=50), nullable=False),
        sa.Column("source_url", sa.String(length=1000), nullable=True),
        sa.Column("source_page", sa.Integer(), nullable=True),
        sa.Column("checksum", sa.String(length=64), nullable=False),
        sa.Column("extracted_at", sa.DateTime(timezone=True), nullable=False),
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
        sa.ForeignKeyConstraint(
            ["financial_statement_id"], ["financial_statements.id"], ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(["job_id"], ["ingestion_jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_data_sources_company_id", "data_sources", ["company_id"])
    op.create_index(
        "ix_data_sources_financial_statement_id",
        "data_sources",
        ["financial_statement_id"],
    )
    op.create_index("ix_data_sources_job_id", "data_sources", ["job_id"])
    op.create_index("ix_data_sources_checksum", "data_sources", ["checksum"])


def downgrade() -> None:
    op.drop_index("ix_data_sources_checksum", table_name="data_sources")
    op.drop_index("ix_data_sources_job_id", table_name="data_sources")
    op.drop_index("ix_data_sources_financial_statement_id", table_name="data_sources")
    op.drop_index("ix_data_sources_company_id", table_name="data_sources")
    op.drop_table("data_sources")
    op.drop_index("ix_ingestion_jobs_status", table_name="ingestion_jobs")
    op.drop_table("ingestion_jobs")
    sa.Enum(name="ingestion_job_status").drop(op.get_bind(), checkfirst=True)
