"""Idempotent seed loader that fetches KSE-100 companies live from PSX.

Usage (inside the backend container or a venv with DATABASE_URL set)::

    python -m scripts.seed

Fetches the current KSE-100 index constituents via the ``psxdata`` library,
then upserts sectors and companies by their natural keys (sector name /
company symbol).  Safe to run repeatedly.

Fields populated from psxdata:
  - symbol, name, sector         → psxdata.symbols()
  - current_price, market_cap,
    dividend_yield                → psxdata.quote(symbol)
  - fifty_two_week_{high,low},
    website, listing_date,
    fiscal_year_end, description  → left as None (not exposed by psxdata)
"""

from __future__ import annotations

import sys
from decimal import Decimal, InvalidOperation
from typing import Any

import psxdata
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import SessionLocal
from app.models.company import Company
from app.models.financial_statement import FinancialStatement, PeriodType
from app.models.sector import Sector
from scripts.generate_financials import generate_financials

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_decimal(value: Any) -> Decimal | None:
    if value is None:
        return None
    try:
        d = Decimal(str(value))
        return d if d.is_finite() else None
    except (InvalidOperation, ValueError):
        return None


def _get_field(obj: Any, *keys: str) -> Any:
    """Return the first non-None value found by trying attribute then item access.

    psxdata functions return single-row DataFrames.  Squeeze to a Series via
    .iloc[0] so that column access yields scalars rather than nested Series.
    """
    # Single-row DataFrame → extract the row as a Series first.
    # An empty DataFrame means psxdata found no match for that symbol.
    if hasattr(obj, "iloc") and hasattr(obj, "columns"):
        if len(obj) == 0:
            return None
        obj = obj.iloc[0]

    for key in keys:
        # attribute access (dataclass, pandas Series, …)
        try:
            val = getattr(obj, key, None)
            if val is not None:
                return val
        except Exception:  # noqa: BLE001
            pass
        # item access (dict, pandas Series, …)
        try:
            val = obj[key]  # type: ignore[index]
            if val is not None:
                return val
        except (KeyError, TypeError, IndexError):
            pass
    return None


def _normalise_sector(raw: str | None) -> str:
    """Convert psxdata sector codes (e.g. 'OIL & GAS EXPLORATION') to title case."""
    if not raw:
        return "Other"
    return raw.strip().title()


def _strip_xd(symbol: str) -> str:
    """Remove the ex-dividend 'XD' suffix PSX temporarily appends to a symbol."""
    return symbol[:-2] if symbol.upper().endswith("XD") else symbol


# ---------------------------------------------------------------------------
# psxdata fetch helpers
# ---------------------------------------------------------------------------


def _fetch_kse100_symbols() -> list[str]:
    """Return the 100 ticker symbols that make up the KSE-100 index."""
    result = psxdata.tickers(index="KSE100")

    # SDK may return the list directly or wrap it in an object with a .data attr.
    # Strip the temporary "XD" ex-dividend suffix PSX appends to some symbols.
    if isinstance(result, list):
        return [_strip_xd(str(s).upper()) for s in result]

    data = _get_field(result, "data")
    if isinstance(data, list):
        return [_strip_xd(str(s).upper()) for s in data]

    raise RuntimeError(f"Unexpected return type from psxdata.tickers(): {type(result)}")


def _build_symbols_map() -> dict[str, dict[str, Any]]:
    """Build {SYMBOL: {name, sector_name}} from psxdata.symbols().

    psxdata.symbols() returns a DataFrame (or list) covering all ~1 000 PSX
    symbols.  We index it by symbol for O(1) lookup in the seed loop.
    """
    result = psxdata.symbols()
    mapping: dict[str, dict[str, Any]] = {}

    # pandas DataFrame path
    if hasattr(result, "iterrows"):
        for _, row in result.iterrows():
            sym = str(_get_field(row, "symbol") or "").upper()
            if sym:
                mapping[sym] = {
                    "name": _get_field(row, "name"),
                    "sector_name": _get_field(row, "sector_name", "sector"),
                }
        return mapping

    # list-of-dicts / list-of-objects path
    if isinstance(result, list):
        for item in result:
            sym = str(_get_field(item, "symbol") or "").upper()
            if sym:
                mapping[sym] = {
                    "name": _get_field(item, "name"),
                    "sector_name": _get_field(item, "sector_name", "sector"),
                }
        return mapping

    return mapping


def _fetch_quote(symbol: str) -> dict[str, Decimal | None]:
    """Return headline numbers from psxdata.quote(); empty dict on failure."""
    try:
        q = psxdata.quote(symbol)
        return {
            "current_price": _to_decimal(_get_field(q, "price")),
            "market_cap": _to_decimal(_get_field(q, "market_cap")),
            "dividend_yield": _to_decimal(_get_field(q, "dividend_yield")),
        }
    except Exception as exc:  # noqa: BLE001
        print(f"  [WARN] {symbol}: quote failed — {exc}", file=sys.stderr)
        return {}


# ---------------------------------------------------------------------------
# Financial-statement seeding (synthetic data)
# ---------------------------------------------------------------------------


def _seed_financials(
    session: Session,
    company: Company,
    *,
    market_cap: float | None,
    current_price: float | None,
) -> None:
    """Generate and upsert synthetic annual + quarterly statements."""
    existing = {(fs.period_type, fs.fiscal_year, fs.fiscal_period): fs for fs in company.financials}
    for record in generate_financials(
        symbol=company.symbol,
        market_cap=market_cap,
        current_price=current_price,
        fiscal_year_end=company.fiscal_year_end,  # None is fine
    ):
        key = (
            PeriodType(record["period_type"]),
            record["fiscal_year"],
            record["fiscal_period"],
        )
        statement = existing.get(key)
        if statement is None:
            statement = FinancialStatement(
                company=company,
                period_type=PeriodType(record["period_type"]),
                fiscal_year=record["fiscal_year"],
                fiscal_period=record["fiscal_period"],
            )
            session.add(statement)
        statement.period_end = record["period_end"]
        statement.currency = record["currency"]
        for field, value in record.items():
            if field in {"period_type", "fiscal_year", "fiscal_period", "period_end", "currency"}:
                continue
            setattr(statement, field, value)


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def seed() -> None:
    print("Fetching KSE-100 index constituents from psxdata…")
    symbols = _fetch_kse100_symbols()
    if not symbols:
        print("ERROR: psxdata.tickers() returned no symbols.", file=sys.stderr)
        sys.exit(1)
    print(f"  {len(symbols)} symbols in KSE-100.")

    print("Fetching symbol metadata (names, sectors)…")
    symbols_map = _build_symbols_map()

    session = SessionLocal()
    try:
        sectors: dict[str, Sector] = {}
        created = 0
        updated = 0

        for i, symbol in enumerate(symbols, 1):
            meta = symbols_map.get(symbol, {})
            sector_name = _normalise_sector(meta.get("sector_name"))
            company_name = str(meta.get("name") or symbol)

            # Upsert sector
            if sector_name not in sectors:
                sector = session.execute(
                    select(Sector).where(Sector.name == sector_name)
                ).scalar_one_or_none()
                if sector is None:
                    sector = Sector(name=sector_name)
                    session.add(sector)
                sectors[sector_name] = sector
            session.flush()

            # Live quote
            print(f"  [{i:3d}/{len(symbols)}] {symbol}: fetching quote…")
            quote = _fetch_quote(symbol)

            # Upsert company
            company = session.execute(
                select(Company).where(Company.symbol == symbol)
            ).scalar_one_or_none()
            if company is None:
                company = Company(symbol=symbol)
                session.add(company)
                created += 1
            else:
                updated += 1

            company.name = company_name
            company.sector = sectors[sector_name]
            company.industry = sector_name
            company.current_price = quote.get("current_price")
            company.market_cap = quote.get("market_cap")
            company.dividend_yield = quote.get("dividend_yield")
            company.is_active = True
            # fifty_two_week_high/low, website, listing_date,
            # fiscal_year_end, description are not available via psxdata.

            session.flush()
            _seed_financials(
                session,
                company,
                market_cap=float(company.market_cap) if company.market_cap else None,
                current_price=float(company.current_price) if company.current_price else None,
            )

        session.commit()
        print(f"\nSeed complete: {created} created, {updated} updated.")
    finally:
        session.close()


if __name__ == "__main__":
    seed()
