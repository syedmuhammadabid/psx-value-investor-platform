"""CLI to refresh company prices from the public PSX market-data snapshot.

PsxWorth publishes a daily PostgreSQL snapshot of PSX market data to a public R2
bucket. This script reuses that same source to update ``current_price`` for the
companies we track with real last-traded PSX prices.

The snapshot is a ``pg_dump`` custom-format archive. Its ``StocksPrices`` table
must be extracted to plain SQL with ``pg_restore`` (which must be at least as new
as the server that produced the dump — currently PostgreSQL 17). Two workflows
are supported:

Convenience (a compatible ``pg_restore`` is on PATH)::

    python -m scripts.sync_prices                    # download + extract + sync
    python -m scripts.sync_prices --dump-file x.dmp  # extract + sync

Two-step (no local ``pg_restore``; use a postgres:17 container to extract)::

    curl -sSL -o tmp/psx.dmp "$PSX_PRICE_SNAPSHOT_URL"
    docker run --rm -v "$PWD/tmp:/d" postgres:17 \\
        pg_restore --data-only --table=StocksPrices -f /d/prices.sql /d/psx.dmp
    python -m scripts.sync_prices --sql-file tmp/prices.sql

Idempotent: re-running with an unchanged snapshot reports every price as
unchanged. Exits non-zero when no snapshot prices matched a tracked company.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
from pathlib import Path

import httpx

from app.core.config import settings
from app.core.database import SessionLocal
from app.scraper import prices as prices_module
from app.services import price_sync as price_sync_service


def _download(url: str, dest: Path) -> None:
    """Stream the snapshot archive to ``dest``."""
    with httpx.stream("GET", url, follow_redirects=True, timeout=120.0) as response:
        response.raise_for_status()
        with dest.open("wb") as fh:
            for chunk in response.iter_bytes():
                fh.write(chunk)


def _extract_sql(dump_path: Path, pg_restore: str) -> str:
    """Extract the ``StocksPrices`` table from a custom-format dump to plain SQL."""
    try:
        completed = subprocess.run(
            [
                pg_restore,
                "--data-only",
                "--table=StocksPrices",
                "-f",
                "-",
                str(dump_path),
            ],
            capture_output=True,
            text=True,
            check=True,
        )
    except FileNotFoundError:
        raise SystemExit(
            f"'{pg_restore}' not found. Install postgresql-client (>= the dump's server "
            "version, currently 17) or use the two-step --sql-file workflow."
        ) from None
    except subprocess.CalledProcessError as exc:
        raise SystemExit(f"pg_restore failed: {exc.stderr.strip()}") from exc
    return completed.stdout


def _resolve_sql(args: argparse.Namespace) -> tuple[str, str]:
    """Return ``(sql_text, source_label)`` from the provided arguments."""
    if args.sql_file:
        path = Path(args.sql_file)
        return path.read_text(encoding="utf-8"), str(path)

    if args.dump_file:
        dump_path = Path(args.dump_file)
        return _extract_sql(dump_path, args.pg_restore), str(dump_path)

    url = args.url or settings.psx_price_snapshot_url
    with tempfile.TemporaryDirectory() as tmp:
        dump_path = Path(tmp) / "psx-data.dmp"
        _download(url, dump_path)
        return _extract_sql(dump_path, args.pg_restore), url


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sync PSX prices from the public snapshot.")
    parser.add_argument("--url", help="Snapshot URL (defaults to PSX_PRICE_SNAPSHOT_URL).")
    parser.add_argument("--dump-file", help="Path to a downloaded custom-format .dmp archive.")
    parser.add_argument("--sql-file", help="Path to pre-extracted StocksPrices plain SQL.")
    parser.add_argument("--pg-restore", default="pg_restore", help="pg_restore binary to use.")
    parser.add_argument(
        "--dry-run", action="store_true", help="Parse and report without writing to the database."
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    sql_text, source = _resolve_sql(args)
    rows = prices_module.parse_stocks_prices_dump(sql_text)
    if not rows:
        print("No price rows found in snapshot — nothing to sync.")
        return 1

    if args.dry_run:
        print(f"Parsed {len(rows)} price rows from {source} (dry run — no changes written).")
        return 0

    with SessionLocal() as db:
        result = price_sync_service.sync_prices(db, rows, source=source)

    print(
        f"Price sync {result.status}: {result.snapshot_symbols} snapshot symbols, "
        f"{result.matched} matched, {result.updated} updated, {result.unchanged} unchanged."
    )
    if result.unmatched_symbols:
        print(f"  Unmatched (no snapshot price): {', '.join(sorted(result.unmatched_symbols))}")
    return 0 if result.matched > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
