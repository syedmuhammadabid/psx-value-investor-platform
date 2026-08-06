"""Scheduled price-sync job.

Runs once daily at 17:00 PKT (12:00 UTC) to pull the latest PSX market-data
snapshot and update ``current_price`` for every tracked company.

The job mirrors the logic in ``scripts/sync_prices.py`` but is driven by
APScheduler rather than the CLI so it fires automatically while the API server
is running.
"""

from __future__ import annotations

import logging
import subprocess
import tempfile
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.scraper import prices as prices_module
from app.services import price_sync as price_sync_service

logger = logging.getLogger(__name__)


def _download(url: str, dest: Path) -> None:
    with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes():
                fh.write(chunk)


def _extract_sql(dump_path: Path, pg_restore: str = "pg_restore") -> str:
    result = subprocess.run(
        [pg_restore, "--data-only", "--table=StocksPrices", "-f", "-", str(dump_path)],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def run_price_sync() -> None:
    """Download the PSX snapshot and sync prices. Called by the scheduler."""
    url = settings.psx_price_snapshot_url
    logger.info("price sync starting — source: %s", url)

    try:
        with tempfile.TemporaryDirectory() as tmp:
            dump_path = Path(tmp) / "psx-data.dmp"
            _download(url, dump_path)
            sql_text = _extract_sql(dump_path)

        rows = prices_module.parse_stocks_prices_dump(sql_text)
        if not rows:
            logger.warning("price sync: no rows found in snapshot — skipping")
            return

        with SessionLocal() as db:
            result = price_sync_service.sync_prices(db, rows, source=url)

        logger.info(
            "price sync %s: %d snapshot symbols, %d matched, %d updated, %d unchanged",
            result.status,
            result.snapshot_symbols,
            result.matched,
            result.updated,
            result.unchanged,
        )
        if result.unmatched_symbols:
            logger.debug("price sync unmatched: %s", ", ".join(sorted(result.unmatched_symbols)))

    except subprocess.CalledProcessError as exc:
        logger.error("price sync: pg_restore failed — %s", exc.stderr.strip())
    except Exception:
        logger.exception("price sync: unexpected error")
