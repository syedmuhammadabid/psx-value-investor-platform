"""Shared pytest fixtures."""

from __future__ import annotations

from collections.abc import Iterator
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app import models  # noqa: F401  (register metadata)
from app.core.database import Base, get_db
from app.main import app
from app.models.company import Company
from app.models.sector import Sector


@pytest.fixture
def db_session() -> Iterator[Session]:
    """An isolated in-memory SQLite database per test."""
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    testing_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = testing_session()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    """A FastAPI test client backed by the in-memory database."""

    def override_get_db() -> Iterator[Session]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def seed_companies(db_session: Session) -> list[Company]:
    """Insert a small, deterministic set of sectors and companies."""
    energy = Sector(name="Energy")
    banks = Sector(name="Commercial Banks")
    tech = Sector(name="Technology & Communication")
    db_session.add_all([energy, banks, tech])
    db_session.flush()

    companies = [
        Company(
            symbol="MARI",
            name="Mari Petroleum Company Limited",
            sector=energy,
            industry="Oil & Gas Exploration",
            market_cap=Decimal("2600000000000.00"),
            current_price=Decimal("620.5000"),
            is_active=True,
        ),
        Company(
            symbol="UBL",
            name="United Bank Limited",
            sector=banks,
            industry="Commercial Banking",
            market_cap=Decimal("450000000000.00"),
            current_price=Decimal("365.2500"),
            is_active=True,
        ),
        Company(
            symbol="SYS",
            name="Systems Limited",
            sector=tech,
            industry="Software & IT Services",
            market_cap=Decimal("290000000000.00"),
            current_price=Decimal("985.0000"),
            is_active=True,
        ),
        Company(
            symbol="OLDCO",
            name="Delisted Holdings Limited",
            sector=None,
            industry=None,
            market_cap=None,
            current_price=None,
            is_active=False,
        ),
    ]
    db_session.add_all(companies)
    db_session.commit()
    return companies
