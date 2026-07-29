"""Tests for the file-based source adapter."""

from __future__ import annotations

import json
from pathlib import Path

from app.scraper import parser


def test_parse_records_accepts_wrapped_object() -> None:
    records = parser.parse_records(
        {
            "records": [
                {
                    "symbol": "MARI",
                    "period_type": "annual",
                    "fiscal_year": 2023,
                    "period_end": "2023-12-31",
                    "revenue": 100,
                }
            ]
        }
    )
    assert len(records) == 1
    assert records[0].symbol == "MARI"


def test_parse_records_accepts_bare_list() -> None:
    records = parser.parse_records(
        [
            {
                "symbol": "UBL",
                "period_type": "quarterly",
                "fiscal_year": 2024,
                "fiscal_period": "Q1",
                "period_end": "2024-03-31",
            }
        ]
    )
    assert records[0].fiscal_period == "Q1"


def test_parse_file_reads_json(tmp_path: Path) -> None:
    path = tmp_path / "records.json"
    path.write_text(
        json.dumps(
            {
                "records": [
                    {
                        "symbol": "ENGRO",
                        "period_type": "annual",
                        "fiscal_year": 2023,
                        "period_end": "2023-12-31",
                    }
                ]
            }
        ),
        encoding="utf-8",
    )
    records = parser.parse_file(path)
    assert records[0].symbol == "ENGRO"
