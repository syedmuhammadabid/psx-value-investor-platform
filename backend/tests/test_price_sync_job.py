"""Tests for the scheduled price-sync job and scheduler configuration."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.jobs.price_sync import run_price_sync
from app.jobs.scheduler import (
    PRICE_SYNC_HOUR_UTC,
    PRICE_SYNC_JOB_ID,
    PRICE_SYNC_JOB_NAME,
    PRICE_SYNC_MINUTE_UTC,
)


def test_price_sync_job_id() -> None:
    assert PRICE_SYNC_JOB_ID == "daily_price_sync"


def test_price_sync_job_name_mentions_pkt() -> None:
    assert "PKT" in PRICE_SYNC_JOB_NAME


def test_price_sync_fires_at_noon_utc() -> None:
    # 17:00 PKT = 12:00 UTC (PKT is UTC+5)
    assert PRICE_SYNC_HOUR_UTC == 12
    assert PRICE_SYNC_MINUTE_UTC == 0


def test_run_price_sync_logs_warning_when_no_rows(caplog: pytest.LogCaptureFixture) -> None:
    """run_price_sync should warn and return early when the snapshot is empty."""
    with (
        patch("app.jobs.price_sync._download"),
        patch("app.jobs.price_sync._extract_sql", return_value="-- empty"),
        patch(
            "app.jobs.price_sync.prices_module.parse_stocks_prices_dump",
            return_value=[],
        ),
        patch("app.jobs.price_sync.tempfile.TemporaryDirectory") as mock_tmp,
    ):
        mock_tmp.return_value.__enter__ = MagicMock(return_value="/tmp/fake")
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)

        import logging

        with caplog.at_level(logging.WARNING, logger="app.jobs.price_sync"):
            run_price_sync()

    assert any("no rows" in record.message for record in caplog.records)


def test_run_price_sync_calls_sync_service_on_success() -> None:
    """run_price_sync should call the price_sync service when rows are returned."""
    from decimal import Decimal
    from datetime import UTC, datetime
    from app.scraper.prices import PriceSnapshotRow

    fake_rows = [PriceSnapshotRow(symbol="MARI", price=Decimal("650.00"), as_of=datetime.now(UTC))]
    fake_result = MagicMock(
        status="SUCCEEDED",
        snapshot_symbols=1,
        matched=1,
        updated=1,
        unchanged=0,
        unmatched_symbols=[],
    )

    with (
        patch("app.jobs.price_sync._download"),
        patch("app.jobs.price_sync._extract_sql", return_value="-- sql"),
        patch(
            "app.jobs.price_sync.prices_module.parse_stocks_prices_dump",
            return_value=fake_rows,
        ),
        patch(
            "app.jobs.price_sync.price_sync_service.sync_prices",
            return_value=fake_result,
        ) as mock_sync,
        patch("app.jobs.price_sync.SessionLocal") as mock_session,
        patch("app.jobs.price_sync.tempfile.TemporaryDirectory") as mock_tmp,
    ):
        mock_tmp.return_value.__enter__ = MagicMock(return_value="/tmp/fake")
        mock_tmp.return_value.__exit__ = MagicMock(return_value=False)
        mock_session.return_value.__enter__ = MagicMock(return_value=MagicMock())
        mock_session.return_value.__exit__ = MagicMock(return_value=False)

        run_price_sync()

    mock_sync.assert_called_once()
