"""CLI to sync financial statements from an exported PSX data payload.

The current repository does not yet include a live PSX filing extractor, so this
command focuses on the stable part of the pipeline: validating and ingesting
financial-statement records that match the existing JSON ingestion schema.

That keeps the sync path ready for a future psxdata-powered extractor while
still providing a real end-to-end write command for imported PSX financials.

Usage::

    python -m scripts.sync_financials --input-file tmp/psx_financials.json
    python -m scripts.sync_financials --input-file tmp/psx_financials.json \
        --symbol ENGROH --symbol MARI

The input file must contain either a JSON array of records or an object with a
``records`` array, matching ``database/seeds/ingestion_sample.json``.

The command also supports ``--live-manifest-file`` to capture the current PSX
financial-reports filing list via ``psxdata``. That is the first step toward a
live extractor, and it produces normalized filing metadata for later document
parsing.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.schemas.ingestion import RawFinancialRecord
from app.scraper import parser
from app.services import ingestion as ingestion_service
from app.services.psxdata_documents import build_filing_documents, download_filing_documents
from app.services.psxdata_filing_parser import parse_filing_documents, parsed_document_to_dict
from app.services.psxdata_fundamentals import fetch_fundamentals_manifest


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser_ = argparse.ArgumentParser(description="Sync PSX financial statements from JSON.")
    parser_.add_argument(
        "--input-file",
        help="Path to a JSON payload with a records array or a top-level array.",
    )
    parser_.add_argument(
        "--source",
        help="Provenance label stored with the ingestion job (defaults to the input file path).",
    )
    parser_.add_argument(
        "--source-type",
        default="psxdata",
        help="Source type stored with provenance rows (defaults to psxdata).",
    )
    parser_.add_argument(
        "--symbol",
        dest="symbols",
        action="append",
        help="Restrict the sync to one symbol; may be repeated.",
    )
    parser_.add_argument(
        "--live-manifest-file",
        help="Fetch the live PSX filing list and write the normalized manifest to this file.",
    )
    parser_.add_argument(
        "--download-documents-dir",
        help="When capturing a live manifest, download the referenced filing documents here.",
    )
    parser_.add_argument(
        "--document-index-file",
        help="Parse downloaded filing documents and write the structured index JSON here.",
    )
    parser_.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and filter records without writing to the database.",
    )
    return parser_.parse_args(argv)


def _filter_records(
    records: list[RawFinancialRecord],
    symbols: list[str] | None,
) -> list[RawFinancialRecord]:
    if not symbols:
        return records
    allowed = {symbol.upper() for symbol in symbols}
    return [record for record in records if record.symbol.upper() in allowed]


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    if args.live_manifest_file:
        output_file = Path(args.live_manifest_file)
        try:
            manifest = fetch_fundamentals_manifest(args.symbols)
        except Exception as exc:  # pragma: no cover - exercised in runtime only
            manifest = []
            print(f"Live PSX manifest capture failed: {exc}. Writing an empty manifest.")

        output_file.write_text(json.dumps({"records": manifest}, indent=2), encoding="utf-8")

        if not manifest:
            print("No live PSX filing rows were captured; wrote an empty manifest.")
            return 0

        document_count = len(build_filing_documents(manifest))
        downloaded_count = 0
        parsed_count = 0
        if args.download_documents_dir:
            saved_documents = download_filing_documents(manifest, args.download_documents_dir)
            downloaded_count = len(saved_documents)
            if args.document_index_file:
                documents = build_filing_documents(manifest)
                parsed_documents = parse_filing_documents(documents, saved_documents)
                index_file = Path(args.document_index_file)
                index_file.write_text(
                    json.dumps(
                        {
                            "documents": [
                                parsed_document_to_dict(document)
                                for document in parsed_documents
                            ]
                        },
                        indent=2,
                    ),
                    encoding="utf-8",
                )
                parsed_count = len(parsed_documents)
        print(
            f"Captured {len(manifest)} live PSX filing rows to {output_file}."
        )
        if args.download_documents_dir:
            print(
                f"Downloaded {downloaded_count}/{document_count} filing documents "
                f"to {args.download_documents_dir}."
            )
        if args.document_index_file:
            print(f"Parsed {parsed_count} filing documents into {args.document_index_file}.")
        return 0

    if not args.input_file:
        print("Either --input-file or --live-manifest-file must be provided.")
        return 1

    input_file = Path(args.input_file)
    source = args.source or str(input_file)

    records = parser.parse_file(input_file)
    records = _filter_records(records, args.symbols)

    if not records:
        print(f"No financial records matched {source}.")
        return 1

    if args.dry_run:
        symbols = ", ".join(sorted({record.symbol for record in records}))
        print(
            f"Parsed {len(records)} financial records from {source} (dry run — no changes written)."
        )
        print(f"Symbols: {symbols}")
        return 0

    with SessionLocal() as db:
        report = ingestion_service.ingest(
            db,
            source=source,
            records=records,
            source_type=args.source_type,
        )

    print(
        f"Financial sync {report.status}: {report.processed} processed, "
        f"{report.ingested} ingested, {report.updated} updated, "
        f"{report.skipped} skipped, {report.rejected} rejected, {report.flagged} flagged."
    )
    return 0 if report.rejected == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())