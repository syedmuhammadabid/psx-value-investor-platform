import Link from "next/link";

import { ScreenerFilters } from "@/components/ScreenerFilters";
import type { ScreenerFilterValues } from "@/components/ScreenerFilters";
import { ScreenerResults } from "@/components/ScreenerResults";
import { ApiError, runScreener } from "@/lib/api";
import type { ScreenerParams } from "@/lib/api";
import type { ScreenerResult } from "@/lib/types";

export const metadata = {
  title: "Screener · PSX Value Investor",
  description:
    "Filter Pakistan Stock Exchange companies by ROE, ROIC, P/E, dividend yield, debt, growth, and free cash flow.",
};

type RawParams = {
  min_roe?: string;
  min_roic?: string;
  max_pe?: string;
  min_dividend_yield?: string;
  max_debt_to_equity?: string;
  min_revenue_growth?: string;
  positive_fcf?: string;
  sector?: string;
};

interface ScreenerPageProps {
  searchParams: Promise<RawParams>;
}

function toNumber(value?: string): number | undefined {
  if (value == null || value.trim() === "") return undefined;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : undefined;
}

export default async function ScreenerPage({
  searchParams,
}: ScreenerPageProps) {
  const raw = await searchParams;

  const params: ScreenerParams = {
    min_roe: toNumber(raw.min_roe),
    min_roic: toNumber(raw.min_roic),
    max_pe: toNumber(raw.max_pe),
    min_dividend_yield: toNumber(raw.min_dividend_yield),
    max_debt_to_equity: toNumber(raw.max_debt_to_equity),
    min_revenue_growth: toNumber(raw.min_revenue_growth),
    positive_fcf: raw.positive_fcf === "true" ? true : undefined,
    sector: raw.sector?.trim() || undefined,
  };

  const initial: ScreenerFilterValues = {
    min_roe: raw.min_roe,
    min_roic: raw.min_roic,
    max_pe: raw.max_pe,
    min_dividend_yield: raw.min_dividend_yield,
    max_debt_to_equity: raw.max_debt_to_equity,
    min_revenue_growth: raw.min_revenue_growth,
    positive_fcf: raw.positive_fcf,
    sector: raw.sector,
  };

  let result: ScreenerResult | null = null;
  let errorMessage: string | null = null;
  try {
    result = await runScreener(params);
  } catch (error) {
    errorMessage =
      error instanceof ApiError
        ? error.message
        : "Something went wrong running the screener.";
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-text">Stock screener</h1>
          <p className="mt-1 text-sm text-text-muted">
            Filter PSX companies by value-investing rules.
          </p>
        </div>
        <Link
          href="/companies"
          className="text-sm text-text-muted transition-colors hover:text-text"
        >
          ← Companies
        </Link>
      </div>

      <div className="mt-6">
        <ScreenerFilters initial={initial} />
      </div>

      {errorMessage ? (
        <p
          role="alert"
          className="mt-10 rounded-md border border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative"
        >
          {errorMessage}
        </p>
      ) : result ? (
        <>
          <p className="mt-6 text-xs text-text-muted">
            {result.count} {result.count === 1 ? "company" : "companies"} match
          </p>
          <ScreenerResults rows={result.items} />
        </>
      ) : null}

      <p className="mt-16 border-t border-border pt-6 text-xs text-text-muted">
        Screener results are illustrative development data and must not be used
        for investment decisions. Not financial advice.
      </p>
    </main>
  );
}
