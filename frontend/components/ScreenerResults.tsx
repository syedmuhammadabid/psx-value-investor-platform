import Link from "next/link";

import {
  formatMarketCap,
  formatMultiple,
  formatPercent,
  formatRatio,
} from "@/lib/format";
import type { ScreenerRow } from "@/lib/types";

const COLUMNS: {
  key: keyof ScreenerRow;
  label: string;
  format: (row: ScreenerRow) => string;
}[] = [
  { key: "roe", label: "ROE", format: (r) => formatPercent(r.roe) },
  { key: "roic", label: "ROIC", format: (r) => formatPercent(r.roic) },
  { key: "pe", label: "P/E", format: (r) => formatMultiple(r.pe) },
  {
    key: "dividend_yield",
    label: "Div Yield",
    format: (r) => formatPercent(r.dividend_yield),
  },
  {
    key: "debt_to_equity",
    label: "D/E",
    format: (r) => formatRatio(r.debt_to_equity),
  },
  {
    key: "revenue_growth",
    label: "Rev Growth",
    format: (r) => formatPercent(r.revenue_growth),
  },
  {
    key: "free_cash_flow",
    label: "Free Cash Flow",
    format: (r) => formatMarketCap(r.free_cash_flow),
  },
];

export function ScreenerResults({ rows }: { rows: ScreenerRow[] }) {
  if (rows.length === 0) {
    return (
      <p className="mt-8 rounded-md border border-border bg-surface px-4 py-6 text-sm text-text-muted">
        No companies match these filters. Try loosening a rule.
      </p>
    );
  }

  return (
    <div className="mt-6 overflow-x-auto rounded-lg border border-border">
      <table className="w-full min-w-[720px] border-collapse text-sm">
        <thead>
          <tr className="border-b border-border bg-surface text-left text-xs text-text-muted">
            <th className="sticky left-0 z-10 bg-surface px-4 py-3 font-medium">
              Company
            </th>
            {COLUMNS.map((col) => (
              <th key={col.key} className="px-4 py-3 text-right font-medium">
                {col.label}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr
              key={row.symbol}
              className="border-b border-border last:border-0 hover:bg-surface-2"
            >
              <td className="sticky left-0 z-10 bg-surface px-4 py-3">
                <Link
                  href={`/companies/${row.symbol}`}
                  className="font-mono text-sm font-semibold text-accent hover:underline"
                >
                  {row.symbol}
                </Link>
                <div className="text-xs text-text-muted">
                  {row.sector ?? "—"}
                </div>
              </td>
              {COLUMNS.map((col) => (
                <td
                  key={col.key}
                  className="px-4 py-3 text-right tabular-nums text-text"
                >
                  {col.format(row)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
