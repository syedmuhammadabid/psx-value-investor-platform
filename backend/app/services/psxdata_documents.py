"""Filing-document queue and downloader helpers.

The live PSX filing manifest gives us report metadata and document links. This
module turns that manifest into a document queue and can persist the referenced
filing documents locally for later parsing.

Actual statement extraction is still a later step; this layer only handles the
document bridge between manifest capture and parser development.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx

_SAFE_NAME = re.compile(r"[^A-Za-z0-9._-]+")


@dataclass(frozen=True, slots=True)
class FilingDocument:
    """A single filing document queued from the PSX manifest."""

    symbol: str
    fiscal_year: int | None
    report_type: str | None
    document_url: str
    period_ended: str | None
    posting_date: str | None
    posting_time: str | None

    @property
    def stem(self) -> str:
        year = self.fiscal_year if self.fiscal_year is not None else "unknown-year"
        report_type = self.report_type or "report"
        return f"{self.symbol}_{year}_{report_type}"


def _text_or_none(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _sanitize_filename(name: str) -> str:
    cleaned = _SAFE_NAME.sub("_", name).strip("._-")
    return cleaned or "filing"


def build_filing_documents(manifest_rows: Sequence[dict[str, Any]]) -> list[FilingDocument]:
    """Convert normalized manifest rows into a filing-document queue."""
    documents: list[FilingDocument] = []
    for row in manifest_rows:
        document_url = _text_or_none(row.get("document"))
        symbol = _text_or_none(row.get("symbol"))
        if not document_url or not symbol:
            continue
        documents.append(
            FilingDocument(
                symbol=symbol.upper(),
                fiscal_year=row.get("fiscal_year"),
                report_type=_text_or_none(row.get("report_type")),
                document_url=document_url,
                period_ended=_text_or_none(row.get("period_ended")),
                posting_date=_text_or_none(row.get("posting_date")),
                posting_time=_text_or_none(row.get("posting_time")),
            )
        )
    return documents


def download_filing_documents(
    manifest_rows: Sequence[dict[str, Any]],
    output_dir: str | Path,
) -> list[Path]:
    """Download filing documents referenced by the manifest into ``output_dir``."""
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    documents = build_filing_documents(manifest_rows)
    saved: list[Path] = []

    with httpx.Client(follow_redirects=True, timeout=120.0) as client:
        for document in documents:
            response = client.get(document.document_url)
            response.raise_for_status()

            suffix = Path(document.document_url.split("?", 1)[0]).suffix.lower()
            if suffix not in {".pdf", ".html", ".htm", ".xls", ".xlsx", ".doc", ".docx"}:
                suffix = ".bin"

            file_name = _sanitize_filename(f"{document.stem}{suffix}")
            destination = output_path / file_name
            destination.write_bytes(response.content)
            saved.append(destination)

    return saved
