"""Live PSX fundamentals-list fetcher.

This module fetches the PSX financial-reports filing list via ``psxdata`` and
normalizes it into a manifest that can later drive document-level extraction.

The repository does not yet include a parser for the filing documents
themselves, so the live sync starts by capturing the authoritative filing
metadata in a stable schema.
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

try:
    import psxdata
except ImportError:  # pragma: no cover - exercised in runtime only
    psxdata = None


def _normalize_value(value: Any) -> Any:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _normalize_row(row: dict[str, Any]) -> dict[str, Any]:
    symbol = str(row.get("symbol", "")).upper()
    year = row.get("year")
    report_type = row.get("type")
    period_ended = row.get("period_ended")
    posting_date = row.get("posting_date")
    posting_time = row.get("posting_time")
    document = row.get("document")

    return {
        "symbol": symbol,
        "fiscal_year": int(year) if year is not None else None,
        "report_type": str(report_type).strip().lower() if report_type else None,
        "period_ended": _normalize_value(period_ended),
        "posting_date": _normalize_value(posting_date),
        "posting_time": _normalize_value(posting_time),
        "document": document,
    }


def fetch_fundamentals_manifest(symbols: Sequence[str] | None = None) -> list[dict[str, Any]]:
    """Fetch and normalize the PSX filing list for one or more symbols."""
    if psxdata is None:
        raise RuntimeError(
            "psxdata is not installed. Install it to use live PSX fundamentals capture."
        )

    selected = [symbol.upper() for symbol in symbols] if symbols else None
    rows: list[dict[str, Any]] = []

    if selected:
        for symbol in selected:
            frame = psxdata.fundamentals(symbol)
            if frame is None or frame.empty:
                continue
            rows.extend(_normalize_row(row) for row in frame.to_dict(orient="records"))
    else:
        frame = psxdata.fundamentals()
        if frame is None or frame.empty:
            return []
        rows.extend(_normalize_row(row) for row in frame.to_dict(orient="records"))

    return rows
