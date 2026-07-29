"""File-based source adapter.

The parser layer turns a raw source into validated :class:`RawFinancialRecord`
instances. This adapter reads a JSON document (a list of records, or an object
with a ``records`` array) — the shape a real HTTP/PDF scraper would emit once
built. Keeping the adapter behind this function means the rest of the pipeline
never changes when the real source is added.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.schemas.ingestion import RawFinancialRecord


def parse_records(payload: list[dict[str, Any]] | dict[str, Any]) -> list[RawFinancialRecord]:
    """Validate a decoded JSON payload into raw records."""
    rows = payload["records"] if isinstance(payload, dict) else payload
    return [RawFinancialRecord.model_validate(row) for row in rows]


def parse_file(path: str | Path) -> list[RawFinancialRecord]:
    """Read and validate records from a JSON file on disk."""
    with Path(path).open(encoding="utf-8") as handle:
        return parse_records(json.load(handle))
