"""SQLAlchemy ORM models.

Importing the models here ensures their metadata is registered on ``Base``
for Alembic autogeneration and ``create_all``.
"""

from app.models.alert_subscription import AlertSubscription
from app.models.company import Company
from app.models.data_source import DataSource
from app.models.financial_statement import FinancialStatement, PeriodType
from app.models.ingestion_job import IngestionJob, JobStatus
from app.models.portfolio_position import PortfolioPosition
from app.models.sector import Sector
from app.models.user import User
from app.models.watchlist import WatchlistItem

__all__ = [
    "AlertSubscription",
    "Company",
    "DataSource",
    "FinancialStatement",
    "IngestionJob",
    "JobStatus",
    "PeriodType",
    "PortfolioPosition",
    "Sector",
    "User",
    "WatchlistItem",
]
