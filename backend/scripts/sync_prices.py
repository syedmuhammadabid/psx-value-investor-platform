"""CLI to refresh company prices from PSX using the psxdata package.

Fetches live/latest quotes for each tracked company directly from PSX via
the ``psxdata`` library, replacing the earlier pg_dump / pg_restore workflow.

Usage::

    python -m scripts.sync_prices            # fetch quotes + update DB
    python -m scripts.sync_prices --dry-run  # print fetched prices, no DB write

Idempotent: re-running when prices haven't changed leaves the database
unchanged.  Exits non-zero when no prices could be matched to a tracked
company.
"""

from __future__ import annotations

import argparse
import contextlib
import sys
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

import psxdata
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.company import Company
from app.scraper.prices import PriceSnapshotRow
from app.services import price_sync as price_sync_service


def _strip_xd(symbol: str) -> str:
    """Remove the ex-dividend 'XD' suffix PSX temporarily appends to a symbol."""
    return symbol[:-2] if symbol.upper().endswith("XD") else symbol


def _get_price_from_quote(q: object) -> Decimal | None:
    """Extract a valid price from a psxdata quote object.

    psxdata.quote() returns a single-row DataFrame.  We squeeze it to a
    Series with .iloc[0] so that column access yields a scalar, not another
    Series.
    """
    # Single-row DataFrame → extract the row as a Series first.
    # An empty DataFrame means psxdata found no match for that symbol.
    if hasattr(q, "iloc") and hasattr(q, "columns"):
        if len(q) == 0:
            return None
        q = q.iloc[0]  # type: ignore[assignment]

    raw = None
    if hasattr(q, "price"):
        raw = q.price  # type: ignore[union-attr]
    elif hasattr(q, "__getitem__"):
        try:
            raw = q["price"]  # type: ignore[index]
        except (KeyError, TypeError):
            return None

    if raw is None:
        return None

    try:
        price = Decimal(str(raw))
    except (InvalidOperation, ValueError):
        return None

    return price if price.is_finite() and price >= 0 else None


def _fetch_quotes(symbols: list[str]) -> list[PriceSnapshotRow]:
    """Fetch a live quote from PSX for each symbol.

    Symbols that fail (network error, unknown ticker, missing price field)
    are skipped with a warning printed to *stderr*.
    """
    rows: list[PriceSnapshotRow] = []
    now = datetime.now(UTC)

    for symbol in symbols:
        try:
            q = psxdata.quote(symbol)
        except Exception as exc:  # noqa: BLE001
            print(f"  [WARN] {symbol}: quote failed — {exc}", file=sys.stderr)
            continue

        # PSX temporarily appends "XD" to symbols during ex-dividend periods.
        # If the base symbol returns no data, fall back to the XD variant.
        if hasattr(q, "iloc") and hasattr(q, "columns") and len(q) == 0:
            with contextlib.suppress(Exception):
                q = psxdata.quote(symbol + "XD")

        price = _get_price_from_quote(q)
        if price is None:
            print(f"  [WARN] {symbol}: no valid price in quote response", file=sys.stderr)
            continue

        # Always store under the clean base symbol — no XD suffix in the DB.
        rows.append(PriceSnapshotRow(symbol=symbol.upper(), price=price, as_of=now))

    return rows


def _get_tracked_symbols(db_session: object) -> list[str]:
    """Return the PSX symbols for every company currently tracked in the DB."""
    companies = list(db_session.execute(select(Company)).scalars().unique().all())  # type: ignore[union-attr]
    return [c.symbol for c in companies]


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync PSX prices via the psxdata package.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Fetch and print prices without writing to the database.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    with SessionLocal() as db:
        symbols = _get_tracked_symbols(db)

    if not symbols:
        print("No companies tracked — nothing to sync.")
        return 1

    print(f"Fetching quotes for {len(symbols)} tracked companies via psxdata…")
    rows = _fetch_quotes(symbols)

    if not rows:
        print("No prices fetched — nothing to sync.")
        return 1

    if args.dry_run:
        print(f"Fetched {len(rows)}/{len(symbols)} prices (dry run — no changes written).")
        for row in sorted(rows, key=lambda r: r.symbol):
            print(f"  {row.symbol}: {row.price}")
        return 0

    with SessionLocal() as db:
        result = price_sync_service.sync_prices(db, rows, source="psxdata")

    print(
        f"Price sync {result.status}: {result.snapshot_symbols} fetched, "
        f"{result.matched} matched, {result.updated} updated, "
        f"{result.unchanged} unchanged."
    )
    if result.unmatched_symbols:
        print(f"  Unmatched (no quote returned): {', '.join(sorted(result.unmatched_symbols))}")
    return 0 if result.matched > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
