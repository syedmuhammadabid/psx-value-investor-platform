"""Tests for the financial sync CLI."""

from __future__ import annotations

import json
from contextlib import nullcontext
from datetime import date
from pathlib import Path

from scripts import sync_financials
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.financial_statement import FinancialStatement


def _payload() -> dict[str, object]:
    return {
        "records": [
            {
                "symbol": "MARI",
                "period_type": "annual",
                "fiscal_year": 2099,
                "fiscal_period": "FY",
                "period_end": date(2099, 12, 31).isoformat(),
                "currency": "PKR",
                "scale": "millions",
                "source_url": "https://example.com/mari-2099.pdf",
                "source_page": 88,
                "revenue": 400000,
                "cost_of_revenue": 276000,
                "gross_profit": 124000,
                "operating_expenses": 44000,
                "operating_income": 80000,
                "interest_expense": 7000,
                "pretax_income": 73000,
                "tax_expense": 21900,
                "net_income": 51100,
                "eps_basic": 38.36,
                "shares_outstanding": 1332,
                "cash_and_equivalents": 55000,
                "inventory": 65000,
                "current_assets": 200000,
                "total_assets": 660000,
                "current_liabilities": 160000,
                "total_debt": 110000,
                "total_liabilities": 380000,
                "total_equity": 280000,
                "operating_cash_flow": 82000,
                "capital_expenditure": 34000,
                "investing_cash_flow": -36000,
                "financing_cash_flow": -22000,
                "dividends_paid": 20000,
            },
            {
                "symbol": "UBL",
                "period_type": "annual",
                "fiscal_year": 2099,
                "fiscal_period": "FY",
                "period_end": date(2099, 12, 31).isoformat(),
                "currency": "PKR",
                "scale": "millions",
                "source_url": "https://example.com/ubl-2099.pdf",
                "source_page": 92,
                "revenue": 500000,
                "cost_of_revenue": 310000,
                "gross_profit": 190000,
                "operating_expenses": 60000,
                "operating_income": 130000,
                "interest_expense": 9000,
                "pretax_income": 121000,
                "tax_expense": 36300,
                "net_income": 84700,
                "eps_basic": 70.56,
                "shares_outstanding": 1200.6225,
                "cash_and_equivalents": 76000,
                "inventory": 53000,
                "current_assets": 215000,
                "total_assets": 690000,
                "current_liabilities": 145000,
                "total_debt": 95000,
                "total_liabilities": 360000,
                "total_equity": 330000,
                "operating_cash_flow": 95000,
                "capital_expenditure": 38000,
                "investing_cash_flow": -41000,
                "financing_cash_flow": -25000,
                "dividends_paid": 30000,
            },
        ]
    }


def test_sync_financials_ingests_records(
    db_session: Session,
    seed_companies: list[object],
    tmp_path: Path,
    monkeypatch,
) -> None:
    payload_path = tmp_path / "financials.json"
    payload_path.write_text(json.dumps(_payload()), encoding="utf-8")

    monkeypatch.setattr(sync_financials, "SessionLocal", lambda: nullcontext(db_session))

    exit_code = sync_financials.main(
        ["--input-file", str(payload_path), "--source-type", "psxdata"]
    )

    assert exit_code == 0
    assert (
        db_session.execute(
            select(func.count())
            .select_from(FinancialStatement)
            .where(FinancialStatement.fiscal_year == 2099)
        ).scalar()
        == 2
    )


def test_sync_financials_filters_symbols(
    db_session: Session,
    seed_companies: list[object],
    tmp_path: Path,
    monkeypatch,
) -> None:
    payload_path = tmp_path / "financials.json"
    payload_path.write_text(json.dumps(_payload()), encoding="utf-8")

    monkeypatch.setattr(sync_financials, "SessionLocal", lambda: nullcontext(db_session))

    exit_code = sync_financials.main(
        ["--input-file", str(payload_path), "--symbol", "MARI"]
    )

    assert exit_code == 0
    assert (
        db_session.execute(
            select(func.count())
            .select_from(FinancialStatement)
            .where(FinancialStatement.fiscal_year == 2099)
        ).scalar()
        == 1
    )


def test_sync_financials_dry_run_skips_database(
    monkeypatch, tmp_path: Path, capsys
) -> None:
    payload_path = tmp_path / "financials.json"
    payload_path.write_text(json.dumps(_payload()), encoding="utf-8")

    def _fail() -> None:
        raise AssertionError("SessionLocal should not be used during dry-run")

    monkeypatch.setattr(sync_financials, "SessionLocal", _fail)

    exit_code = sync_financials.main(["--input-file", str(payload_path), "--dry-run"])

    assert exit_code == 0
    assert "dry run" in capsys.readouterr().out


def test_sync_financials_live_manifest_writes_json(tmp_path: Path, monkeypatch, capsys) -> None:
    output = tmp_path / "manifest.json"

    monkeypatch.setattr(
        sync_financials,
        "fetch_fundamentals_manifest",
        lambda symbols=None: [
            {
                "symbol": "MARI",
                "fiscal_year": 2024,
                "report_type": "annual",
                "period_ended": "2024-12-31",
                "posting_date": "2025-01-15",
                "posting_time": "10:00",
                "document": "https://example.com/mari-2024.html",
            }
        ],
    )

    exit_code = sync_financials.main(["--live-manifest-file", str(output), "--symbol", "MARI"])

    assert exit_code == 0
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["records"][0]["symbol"] == "MARI"
    assert "Captured 1 live PSX filing rows" in capsys.readouterr().out


def test_sync_financials_live_manifest_handles_upstream_errors(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    output = tmp_path / "manifest.json"

    def _raise(symbols=None):
        raise RuntimeError("psxdata unavailable")

    monkeypatch.setattr(sync_financials, "fetch_fundamentals_manifest", _raise)

    exit_code = sync_financials.main(["--live-manifest-file", str(output)])

    assert exit_code == 0
    assert output.exists()
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["records"] == []
    assert "No live PSX filing rows were captured" in capsys.readouterr().out


def test_sync_financials_downloads_manifest_documents(tmp_path: Path, monkeypatch, capsys) -> None:
    output = tmp_path / "manifest.json"
    docs_dir = tmp_path / "docs"
    index_file = tmp_path / "document-index.json"

    monkeypatch.setattr(
        sync_financials,
        "fetch_fundamentals_manifest",
        lambda symbols=None: [
            {
                "symbol": "MARI",
                "fiscal_year": 2024,
                "report_type": "annual",
                "period_ended": "2024-12-31",
                "posting_date": "2025-01-15",
                "posting_time": "10:00",
                "document": "https://example.com/mari-2024.html",
            }
        ],
    )

    class _Response:
        def __init__(self) -> None:
            self.content = (
                b"<html><body><h1>Annual Report</h1><p>Financial Statements</p></body></html>"
            )

        def raise_for_status(self) -> None:
            return None

    class _Client:
        def __init__(self, *args, **kwargs) -> None:
            pass

        def __enter__(self) -> _Client:
            return self

        def __exit__(self, exc_type, exc, tb) -> None:
            return None

        def get(self, url: str) -> _Response:
            return _Response()

    monkeypatch.setattr("app.services.psxdata_documents.httpx.Client", _Client)

    exit_code = sync_financials.main(
        [
            "--live-manifest-file",
            str(output),
            "--download-documents-dir",
            str(docs_dir),
            "--document-index-file",
            str(index_file),
        ]
    )

    assert exit_code == 0
    assert output.exists()
    assert docs_dir.exists()
    assert index_file.exists()
    assert list(docs_dir.iterdir())
    assert "Downloaded 1/1 filing documents" in capsys.readouterr().out
    index_payload = json.loads(index_file.read_text(encoding="utf-8"))
    assert index_payload["documents"][0]["content_type"] == "html"
    assert index_payload["documents"][0]["heading"] == "annual report"