"""Idempotent seed loader for development data.

Usage (inside the backend container or a venv with DATABASE_URL set)::

    python -m scripts.seed

Loads ``database/seeds/companies.json`` and upserts sectors and companies by
their natural keys (sector name / company symbol). Safe to run repeatedly.
"""

from __future__ import annotations

import json
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType
from app.models.sector import Sector
from scripts.generate_financials import generate_financials

SEED_FILE = Path(__file__).resolve().parents[2] / "database" / "seeds" / "companies.json"

_DECIMAL_FIELDS = (
    "market_cap",
    "current_price",
    "fifty_two_week_high",
    "fifty_two_week_low",
    "dividend_yield",
)


def _to_decimal(value: Any) -> Decimal | None:
    return None if value is None else Decimal(str(value))


def _to_date(value: str | None) -> date | None:
    return None if value is None else date.fromisoformat(value)


def _seed_financials(session: Session, company: Company, row: dict[str, Any]) -> None:
    """Generate and upsert synthetic statements for a single company."""
    existing = {(fs.period_type, fs.fiscal_year, fs.fiscal_period): fs for fs in company.financials}
    for record in generate_financials(
        symbol=row["symbol"],
        market_cap=row.get("market_cap"),
        current_price=row.get("current_price"),
        fiscal_year_end=row.get("fiscal_year_end"),
    ):
        key = (
            PeriodType(record["period_type"]),
            record["fiscal_year"],
            record["fiscal_period"],
        )
        statement = existing.get(key)
        if statement is None:
            statement = FinancialStatement(
                company=company,
                period_type=PeriodType(record["period_type"]),
                fiscal_year=record["fiscal_year"],
                fiscal_period=record["fiscal_period"],
            )
            session.add(statement)
        statement.period_end = record["period_end"]
        statement.currency = record["currency"]
        for field, value in record.items():
            if field in {
                "period_type",
                "fiscal_year",
                "fiscal_period",
                "period_end",
                "currency",
            }:
                continue
            setattr(statement, field, value)


def load_seed_data(path: Path = SEED_FILE) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def seed() -> None:
    data = load_seed_data()
    session = SessionLocal()
    try:
        sectors: dict[str, Sector] = {}
        for name in data["sectors"]:
            sector = session.execute(select(Sector).where(Sector.name == name)).scalar_one_or_none()
            if sector is None:
                sector = Sector(name=name)
                session.add(sector)
            sectors[name] = sector
        session.flush()

        created = 0
        updated = 0
        for row in data["companies"]:
            company = session.execute(
                select(Company).where(Company.symbol == row["symbol"])
            ).scalar_one_or_none()
            if company is None:
                company = Company(symbol=row["symbol"])
                session.add(company)
                created += 1
            else:
                updated += 1

            company.name = row["name"]
            company.sector = sectors.get(row["sector"]) if row.get("sector") else None
            company.industry = row.get("industry")
            for field in _DECIMAL_FIELDS:
                setattr(company, field, _to_decimal(row.get(field)))
            company.website = row.get("website")
            company.fiscal_year_end = row.get("fiscal_year_end")
            company.listing_date = _to_date(row.get("listing_date"))
            company.description = row.get("description")
            company.is_active = True

            session.flush()
            _seed_financials(session, company, row)

        session.commit()
        print(f"Seed complete: {created} created, {updated} updated.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
