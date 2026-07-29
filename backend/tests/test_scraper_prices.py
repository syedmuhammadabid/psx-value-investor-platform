"""Tests for the PSX price-snapshot parser."""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal

from app.scraper import prices
from app.scraper.prices import PriceSnapshotRow

_DUMP = """--
-- PostgreSQL database dump
--

SET statement_timeout = 0;

COPY public."StocksPrices" (symbol, price, "updatedAt") FROM stdin;
FFC\t547.71\t2026-07-28 10:36:03.984+00
OGDC\t321\t2026-07-28 10:36:03.98+00
cnergy\t10.95\t2026-07-28 10:36:03.977+00
\\.


--
-- PostgreSQL database dump complete
--
"""


def test_parses_all_valid_rows() -> None:
    rows = prices.parse_stocks_prices_dump(_DUMP)

    assert rows == [
        PriceSnapshotRow(
            symbol="FFC",
            price=Decimal("547.71"),
            as_of=datetime(2026, 7, 28, 10, 36, 3, 984000, tzinfo=UTC),
        ),
        PriceSnapshotRow(
            symbol="OGDC",
            price=Decimal("321"),
            as_of=datetime(2026, 7, 28, 10, 36, 3, 980000, tzinfo=UTC),
        ),
        PriceSnapshotRow(
            symbol="CNERGY",
            price=Decimal("10.95"),
            as_of=datetime(2026, 7, 28, 10, 36, 3, 977000, tzinfo=UTC),
        ),
    ]


def test_symbol_is_upper_cased() -> None:
    rows = prices.parse_stocks_prices_dump(_DUMP)
    assert rows[2].symbol == "CNERGY"


def test_ignores_content_outside_copy_block() -> None:
    noise = 'COPY public."payouts" (id, symbol) FROM stdin;\n1\tFFC\n\\.\n' + _DUMP
    rows = prices.parse_stocks_prices_dump(noise)
    assert {row.symbol for row in rows} == {"FFC", "OGDC", "CNERGY"}


def test_returns_empty_when_no_copy_block() -> None:
    assert prices.parse_stocks_prices_dump("SELECT 1;") == []


def test_skips_malformed_rows() -> None:
    dump = (
        'COPY public."StocksPrices" (symbol, price, "updatedAt") FROM stdin;\n'
        "GOOD\t10.5\t2026-07-28 10:36:03.98+00\n"
        "MISSINGCOL\t10.5\n"  # too few fields
        "BADPRICE\tnot-a-number\t2026-07-28 10:36:03.98+00\n"
        "BADDATE\t10.5\tnot-a-date\n"
        "\tNULLSYM\t2026-07-28 10:36:03.98+00\n"  # empty symbol
        "NEG\t-5\t2026-07-28 10:36:03.98+00\n"  # negative price
        "NULLPRICE\t\\N\t2026-07-28 10:36:03.98+00\n"  # NULL price token
        "\\.\n"
    )
    rows = prices.parse_stocks_prices_dump(dump)
    assert [row.symbol for row in rows] == ["GOOD"]


def test_latest_by_symbol_keeps_most_recent() -> None:
    older = PriceSnapshotRow(
        symbol="FFC", price=Decimal("500"), as_of=datetime(2026, 1, 1, tzinfo=UTC)
    )
    newer = PriceSnapshotRow(
        symbol="FFC", price=Decimal("550"), as_of=datetime(2026, 7, 1, tzinfo=UTC)
    )
    other = PriceSnapshotRow(
        symbol="OGDC", price=Decimal("300"), as_of=datetime(2026, 3, 1, tzinfo=UTC)
    )

    latest = prices.latest_by_symbol([older, newer, other])

    assert latest["FFC"] == newer
    assert latest["OGDC"] == other
