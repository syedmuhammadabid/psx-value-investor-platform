"""Parser for the public PSX market-data price snapshot.

PsxWorth publishes a daily PostgreSQL snapshot of PSX market data to a public
Cloudflare R2 bucket (documented in its ``docs/local-setup.md``). We reuse that
same source for authentic last-traded prices so this platform reflects real PSX
quotes instead of illustrative seed values.

The snapshot is a ``pg_dump`` custom-format archive. Its ``StocksPrices`` table
is extracted to plain SQL with ``pg_restore`` (see ``scripts/sync_prices.py``),
producing a ``COPY`` block of tab-separated rows::

    COPY public."StocksPrices" (symbol, price, "updatedAt") FROM stdin;
    FFC\t547.71\t2026-07-28 10:36:03.984+00
    OGDC\t321\t2026-07-28 10:36:03.98+00
    \\.

The functions here parse that block. They are pure and deterministic so they can
be golden-file tested without any network or database access.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

_COPY_HEADER_PREFIX = 'COPY public."StocksPrices"'
_COPY_HEADER_SUFFIX = "FROM stdin;"
_COPY_TERMINATOR = "\\."
_NULL_TOKEN = "\\N"
_EXPECTED_COLUMNS = 3


@dataclass(frozen=True, slots=True)
class PriceSnapshotRow:
    """A single last-traded price for a PSX symbol from the snapshot."""

    symbol: str
    price: Decimal
    as_of: datetime


def _parse_row(line: str) -> PriceSnapshotRow | None:
    """Parse one tab-separated ``COPY`` data row, or ``None`` if unusable."""
    fields = line.split("\t")
    if len(fields) != _EXPECTED_COLUMNS:
        return None

    symbol_raw, price_raw, as_of_raw = fields
    symbol = symbol_raw.strip().upper()
    if not symbol or _NULL_TOKEN in (price_raw, as_of_raw):
        return None

    try:
        price = Decimal(price_raw.strip())
        as_of = datetime.fromisoformat(as_of_raw.strip())
    except (InvalidOperation, ValueError):
        return None

    if not price.is_finite() or price < 0:
        return None

    return PriceSnapshotRow(symbol=symbol, price=price, as_of=as_of)


def parse_stocks_prices_dump(sql_text: str) -> list[PriceSnapshotRow]:
    """Parse the ``StocksPrices`` ``COPY`` block from pg_restore plain SQL.

    Rows that are malformed (wrong column count, non-numeric price, unparseable
    timestamp, or ``NULL`` values) are skipped rather than aborting the run.
    """
    rows: list[PriceSnapshotRow] = []
    in_copy = False

    for line in sql_text.splitlines():
        if not in_copy:
            stripped = line.strip()
            if stripped.startswith(_COPY_HEADER_PREFIX) and stripped.endswith(_COPY_HEADER_SUFFIX):
                in_copy = True
            continue

        if line.strip() == _COPY_TERMINATOR:
            break

        row = _parse_row(line)
        if row is not None:
            rows.append(row)

    return rows


def latest_by_symbol(rows: Iterable[PriceSnapshotRow]) -> dict[str, PriceSnapshotRow]:
    """Index rows by upper-cased symbol, keeping the most recent quote per symbol."""
    latest: dict[str, PriceSnapshotRow] = {}
    for row in rows:
        key = row.symbol.upper()
        existing = latest.get(key)
        if existing is None or row.as_of >= existing.as_of:
            latest[key] = row
    return latest
