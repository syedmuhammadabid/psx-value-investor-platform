"""Downloaded filing document parser.

The live PSX manifest and document downloader give us local filing artifacts.
This module turns each downloaded filing into a small, structured index record:
text, headings, and basic metadata. That is enough to drive the next step — a
real financial-statement mapper — without pretending the mapping is complete.
"""

from __future__ import annotations

import html
import re
from collections.abc import Sequence
from dataclasses import asdict, dataclass
from importlib import import_module
from pathlib import Path
from types import ModuleType
from typing import Any, cast

from app.services.psxdata_documents import FilingDocument

try:
    pypdf: ModuleType | None = import_module("pypdf")
except ModuleNotFoundError:  # pragma: no cover - exercised in runtime only
    pypdf = None

if pypdf is not None:
    PdfReader: type[Any] | None = cast(type[Any], pypdf.PdfReader)
else:
    PdfReader = None

_WHITESPACE = re.compile(r"\s+")
_HEADING_HINT = re.compile(r"\b(?:annual report|financial statements?|statement of)\b", re.I)


@dataclass(frozen=True, slots=True)
class ParsedFilingDocument:
    """Structured document index produced from a downloaded filing."""

    symbol: str
    fiscal_year: int | None
    report_type: str | None
    source_path: str
    source_url: str
    content_type: str
    heading: str | None
    text_excerpt: str
    page_count: int | None


def _normalize_text(text: str) -> str:
    return _WHITESPACE.sub(" ", html.unescape(text)).strip()


def _extract_html_text(content: str) -> tuple[str | None, str]:
    heading_match = _HEADING_HINT.search(content)
    heading = None
    if heading_match:
        heading = heading_match.group(0).lower()
    cleaned = re.sub(r"<script.*?</script>|<style.*?</style>", " ", content, flags=re.I | re.S)
    cleaned = re.sub(r"<[^>]+>", " ", cleaned)
    return heading, _normalize_text(cleaned)


def _extract_pdf_text(path: Path) -> tuple[str | None, str, int | None]:
    if PdfReader is None:
        content = _normalize_text(path.read_bytes().decode("utf-8", errors="ignore"))
        match = _HEADING_HINT.search(content)
        heading = match.group(0).lower() if match else None
        return heading, content, None

    reader = PdfReader(str(path))
    parts: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        if text.strip():
            parts.append(text)
    content = _normalize_text(" ".join(parts))
    heading = None
    match = _HEADING_HINT.search(content)
    if match:
        heading = match.group(0).lower()
    return heading, content, len(reader.pages)


def parse_filing_document(
    document: FilingDocument,
    source_path: str | Path,
) -> ParsedFilingDocument:
    """Parse a downloaded filing into a searchable document index row."""
    path = Path(source_path)
    suffix = path.suffix.lower()

    if suffix in {".html", ".htm"}:
        content = path.read_text(encoding="utf-8", errors="ignore")
        heading, text = _extract_html_text(content)
        page_count: int | None = None
        content_type = "html"
    elif suffix == ".pdf":
        heading, text, page_count = _extract_pdf_text(path)
        content_type = "pdf"
    else:
        content = path.read_text(encoding="utf-8", errors="ignore")
        heading = None
        text = _normalize_text(content)
        page_count = None
        content_type = "text"

    return ParsedFilingDocument(
        symbol=document.symbol,
        fiscal_year=document.fiscal_year,
        report_type=document.report_type,
        source_path=str(path),
        source_url=document.document_url,
        content_type=content_type,
        heading=heading,
        text_excerpt=text[:2_000],
        page_count=page_count,
    )


def parse_filing_documents(
    documents: Sequence[FilingDocument],
    source_paths: Sequence[str | Path],
) -> list[ParsedFilingDocument]:
    """Parse each downloaded filing into a structured document index."""
    parsed: list[ParsedFilingDocument] = []
    for document, source_path in zip(documents, source_paths, strict=True):
        parsed.append(parse_filing_document(document, source_path))
    return parsed


def parsed_document_to_dict(document: ParsedFilingDocument) -> dict[str, object]:
    """Serialize a parsed filing document for JSON output."""
    return asdict(document)
