import Link from "next/link";

import { formatMarketCap, formatPrice } from "@/lib/format";
import type { CompanySummary } from "@/lib/types";

export function CompanyCard({ company }: { company: CompanySummary }) {
  return (
    <Link
      href={`/companies/${company.symbol}`}
      className="group flex flex-col rounded-lg border border-border bg-surface p-5 transition-colors hover:bg-surface-2 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
    >
      <div className="flex items-baseline justify-between gap-3">
        <span className="font-mono text-sm font-semibold text-accent">
          {company.symbol}
        </span>
        <span className="text-sm text-text">
          {formatPrice(company.current_price)}
        </span>
      </div>

      <h2 className="mt-2 line-clamp-2 text-base font-medium text-text">
        {company.name}
      </h2>

      <dl className="mt-4 flex items-center justify-between text-xs text-text-muted">
        <div>
          <dt className="sr-only">Sector</dt>
          <dd>{company.sector ?? "—"}</dd>
        </div>
        <div className="text-right">
          <dt className="sr-only">Market capitalisation</dt>
          <dd>{formatMarketCap(company.market_cap)}</dd>
        </div>
      </dl>
    </Link>
  );
}
