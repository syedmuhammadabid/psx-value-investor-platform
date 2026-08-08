"""CLI to sync the top-20 KSE-100 companies by index weight into the database.

Scrapes the PSX data portal (https://dps.psx.com.pk/indices) with Selenium,
extracts the KSE-100 constituent table, and upserts the top 20 most-weighted
companies into the database.  Current price is taken directly from the scraped
page, so no additional API calls are needed.

Usage::

    python -m scripts.sync_top_companies            # scrape + upsert DB
    python -m scripts.sync_top_companies --dry-run  # print results only

Requires a Chrome installation (uses headless mode).  ChromeDriver is
managed automatically by Selenium Manager (bundled with Selenium 4.6+).
"""

from __future__ import annotations

import argparse
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec  # noqa: N812 – Selenium convention
from selenium.webdriver.support.ui import Select, WebDriverWait
from sqlalchemy import select

from app.core.database import SessionLocal
from app.models.company import Company
from app.models.sector import Sector

PSX_INDICES_URL = "https://dps.psx.com.pk/indices"
_TABLE_ID = "DataTables_Table_0"
_TOP_N = 20
_MIN_COLUMNS = 7  # expected columns: symbol, name, ldcp, current, change, change%, idx_weight


# ---------------------------------------------------------------------------
# Data container
# ---------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class CompanyRow:
    symbol: str
    name: str
    current_price: Decimal | None
    ldcp: Decimal | None
    idx_weight: float


# ---------------------------------------------------------------------------
# Scraper
# ---------------------------------------------------------------------------


def _build_driver() -> webdriver.Chrome:
    """Return a configured headless Chrome WebDriver."""
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")
    return webdriver.Chrome(options=options)


def _to_decimal(raw: str) -> Decimal | None:
    cleaned = raw.strip().replace(",", "").replace("%", "")
    if not cleaned:
        return None
    try:
        d = Decimal(cleaned)
        return d if d.is_finite() and d >= 0 else None
    except (InvalidOperation, ValueError):
        return None


def _strip_xd(symbol: str) -> str:
    """Remove the ex-dividend 'XD' suffix PSX temporarily appends to a symbol."""
    return symbol[:-2] if symbol.upper().endswith("XD") else symbol


def scrape_top_companies(n: int = _TOP_N) -> list[CompanyRow]:
    """Scrape the PSX indices page and return the top *n* companies by weight."""
    driver = _build_driver()
    rows: list[CompanyRow] = []

    try:
        print(f"Opening {PSX_INDICES_URL} …")
        driver.get(PSX_INDICES_URL)

        # Wait for the DataTable to render.
        WebDriverWait(driver, 20).until(ec.presence_of_element_located((By.ID, _TABLE_ID)))

        # Expand to 100 rows so we capture all constituents before sorting.
        try:
            dropdown = Select(driver.find_element(By.NAME, f"{_TABLE_ID}_length"))
            dropdown.select_by_value("100")
            WebDriverWait(driver, 10).until(
                ec.text_to_be_present_in_element((By.ID, f"{_TABLE_ID}_info"), "100 entries")
            )
        except Exception:  # noqa: BLE001
            print("  [WARN] Could not expand table to 100 entries; using default.", file=sys.stderr)

        soup = BeautifulSoup(driver.page_source, "html.parser")
    finally:
        driver.quit()

    table = soup.find("table", {"id": _TABLE_ID})
    if not table:
        raise RuntimeError(f"Table '{_TABLE_ID}' not found in page source.")

    for tr in table.find_all("tr")[1:]:
        cells = tr.find_all("td")
        if len(cells) < _MIN_COLUMNS:
            continue
        symbol = _strip_xd(cells[0].get_text(strip=True).upper())
        name = cells[1].get_text(strip=True)
        ldcp_raw = cells[2].get_text(strip=True)
        current_raw = cells[3].get_text(strip=True)
        weight_raw = cells[6].get_text(strip=True)

        if not symbol or symbol == "SYMBOL":
            continue

        weight_str = weight_raw.replace("%", "").strip()
        try:
            weight = float(weight_str)
        except ValueError:
            continue

        rows.append(
            CompanyRow(
                symbol=symbol,
                name=name,
                current_price=_to_decimal(current_raw),
                ldcp=_to_decimal(ldcp_raw),
                idx_weight=weight,
            )
        )

    # Sort descending by weight and return top-n.
    rows.sort(key=lambda r: r.idx_weight, reverse=True)
    return rows[:n]


# ---------------------------------------------------------------------------
# Database upsert
# ---------------------------------------------------------------------------


def upsert_companies(rows: list[CompanyRow]) -> tuple[int, int]:
    """Upsert *rows* into the database.  Returns (created, updated) counts."""
    created = updated = 0

    with SessionLocal() as db:
        # Ensure a catch-all sector exists for companies without known sector.
        sector = db.execute(select(Sector).where(Sector.name == "KSE-100")).scalar_one_or_none()
        if sector is None:
            sector = Sector(name="KSE-100")
            db.add(sector)
            db.flush()

        for row in rows:
            company = db.execute(
                select(Company).where(Company.symbol == row.symbol)
            ).scalar_one_or_none()

            if company is None:
                company = Company(symbol=row.symbol)
                db.add(company)
                created += 1
            else:
                updated += 1

            company.name = row.name
            company.current_price = row.current_price
            if company.sector is None:
                company.sector = sector
            company.is_active = True

        db.commit()

    return created, updated


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Sync top-20 KSE-100 companies by index weight from PSX."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Scrape and print results without writing to the database.",
    )
    parser.add_argument(
        "--top",
        type=int,
        default=_TOP_N,
        metavar="N",
        help=f"Number of top companies to sync (default: {_TOP_N}).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(sys.argv[1:] if argv is None else argv)

    rows = scrape_top_companies(n=args.top)
    if not rows:
        print("No companies scraped from PSX — nothing to sync.")
        return 1

    as_of = datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    header = f"{'#':<4} {'SYMBOL':<12} {'IDX WTG%':>9}  {'CURRENT':>10}  NAME"
    print(f"\nTop {args.top} KSE-100 companies by index weight (as of {as_of}):")
    print(header)
    print("-" * len(header))
    for i, row in enumerate(rows, 1):
        price_str = f"{row.current_price:.2f}" if row.current_price else "N/A"
        print(f"{i:<4} {row.symbol:<12} {row.idx_weight:>8.4f}%  {price_str:>10}  {row.name}")

    if args.dry_run:
        print("\n(dry run — no changes written)")
        return 0

    created, updated = upsert_companies(rows)
    print(f"\nDB sync complete: {created} created, {updated} updated.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
