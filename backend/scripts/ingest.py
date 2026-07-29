"""CLI to ingest financial records from a JSON file through the data pipeline.

Usage (inside the backend container or a venv with DATABASE_URL set)::

    python -m scripts.ingest database/seeds/ingestion_sample.json

Offline-runnable and idempotent: re-running with unchanged data reports every
record as ``skipped``. Prints a per-run summary and exits non-zero if the run
did not fully succeed, so it can gate a CI or cron pipeline.
"""

from __future__ import annotations

import sys
from pathlib import Path

from app.core.database import SessionLocal
from app.scraper import parser
from app.services import ingestion as ingestion_service

DEFAULT_FILE = Path(__file__).resolve().parents[2] / "database" / "seeds" / "ingestion_sample.json"


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    path = Path(args[0]) if args else DEFAULT_FILE

    records = parser.parse_file(path)
    with SessionLocal() as db:
        report = ingestion_service.ingest(db, source=str(path), records=records)

    print(
        f"Ingestion {report.status}: {report.processed} processed, "
        f"{report.ingested} ingested, {report.updated} updated, "
        f"{report.skipped} skipped, {report.rejected} rejected, {report.flagged} flagged."
    )
    for outcome in report.outcomes:
        for issue in outcome.issues:
            print(
                f"  [{issue.severity}] {outcome.symbol} "
                f"{outcome.fiscal_year} {outcome.fiscal_period}: {issue.message}"
            )
    return 0 if report.rejected == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
