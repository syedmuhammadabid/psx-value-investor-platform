/** Formatting helpers for financial figures (PKR).
 *
 * Decimal values from the API arrive as strings to preserve precision, so all
 * helpers accept `number | string` and coerce defensively.
 */

type Numeric = number | string | null | undefined;

function toNumber(value: Numeric): number | null {
  if (value == null || value === "") return null;
  const parsed = typeof value === "number" ? value : Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

/** Format a PKR price with up to two decimals, e.g. `Rs 620.50`. */
export function formatPrice(value: Numeric): string {
  const num = toNumber(value);
  if (num == null) return "—";
  return `Rs ${num.toLocaleString("en-PK", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

/**
 * Abbreviate a large PKR figure into a compact, readable string
 * (trillions / billions / millions).
 */
export function formatMarketCap(value: Numeric): string {
  const num = toNumber(value);
  if (num == null) return "—";
  return `Rs ${compact(num)}`;
}

/** Compact signed number, e.g. `143.16B`, `-9.60B`, `1.20M`. */
export function compact(value: number): string {
  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";
  const trillion = 1_000_000_000_000;
  const billion = 1_000_000_000;
  const million = 1_000_000;
  const thousand = 1_000;

  if (abs >= trillion) return `${sign}${(abs / trillion).toFixed(2)}T`;
  if (abs >= billion) return `${sign}${(abs / billion).toFixed(2)}B`;
  if (abs >= million) return `${sign}${(abs / million).toFixed(2)}M`;
  if (abs >= thousand) return `${sign}${(abs / thousand).toFixed(2)}K`;
  return value.toLocaleString("en-PK", { maximumFractionDigits: 2 });
}

/**
 * Format a financial-statement line item for a table cell. Large monetary
 * values are abbreviated; small values (e.g. EPS) show two decimals.
 */
export function formatStatementValue(value: Numeric): string {
  const num = toNumber(value);
  if (num == null) return "—";
  if (Math.abs(num) < 1000) {
    return num.toLocaleString("en-PK", {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    });
  }
  return compact(num);
}

/** Format a ratio as a percentage, e.g. `9.80%`. */
export function formatPercent(value: Numeric): string {
  const num = toNumber(value);
  if (num == null) return "—";
  return `${num.toFixed(2)}%`;
}

/** Format a valuation multiple, e.g. `7.66×`. */
export function formatMultiple(value: Numeric): string {
  const num = toNumber(value);
  if (num == null) return "—";
  return `${num.toFixed(2)}×`;
}

/** Format a plain ratio to two decimals, e.g. `1.59`. */
export function formatRatio(value: Numeric): string {
  const num = toNumber(value);
  if (num == null) return "—";
  return num.toFixed(2);
}
