import Link from "next/link";
import { notFound } from "next/navigation";

import { AlertsView } from "@/components/AlertsView";
import { AssistantView } from "@/components/AssistantView";
import { BuySellZonesView } from "@/components/BuySellZonesView";
import { CompanyActions } from "@/components/CompanyActions";
import { DataQualityView } from "@/components/DataQualityView";
import { FinancialCharts } from "@/components/FinancialCharts";
import { FinancialRatiosView } from "@/components/FinancialRatios";
import { FinancialStatementsView } from "@/components/FinancialStatements";
import { RecommendationView } from "@/components/RecommendationView";
import { ScoresView } from "@/components/ScoresView";
import { ValuationView } from "@/components/ValuationView";
import {
  ApiError,
  getAlerts,
  getCompany,
  getDataQuality,
  getFinancials,
  getHistory,
  getRatios,
  getRecommendation,
  getScores,
  getValuation,
  getZones,
} from "@/lib/api";
import { formatMarketCap, formatPercent, formatPrice } from "@/lib/format";
import type {
  AlertReport,
  BuySellZones,
  CompanyDetail,
  CompanyHistory,
  CompanyScores,
  DataQualityReport,
  FinancialRatios,
  FinancialStatements,
  PeriodType,
  RecommendationReport,
  Valuation,
} from "@/lib/types";

interface CompanyPageProps {
  params: Promise<{ symbol: string }>;
  searchParams: Promise<{ period?: string }>;
}

export async function generateMetadata({ params }: CompanyPageProps) {
  const { symbol } = await params;
  return {
    title: `${symbol.toUpperCase()} · PSX Value Investor`,
  };
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <dt className="text-xs text-text-muted">{label}</dt>
      <dd className="mt-1 text-sm font-medium text-text">{value}</dd>
    </div>
  );
}

export default async function CompanyPage({
  params,
  searchParams,
}: CompanyPageProps) {
  const { symbol } = await params;
  const { period } = await searchParams;
  const activePeriod: PeriodType =
    period === "quarterly" ? "quarterly" : "annual";

  let company: CompanyDetail;
  try {
    company = await getCompany(symbol);
  } catch (error) {
    if (error instanceof ApiError && error.status === 404) {
      notFound();
    }
    throw error;
  }

  let financials: FinancialStatements | null = null;
  try {
    financials = await getFinancials(company.symbol, activePeriod, 10);
  } catch {
    financials = null;
  }

  let ratios: FinancialRatios | null = null;
  try {
    ratios = await getRatios(company.symbol);
  } catch {
    ratios = null;
  }

  let history: CompanyHistory | null = null;
  try {
    history = await getHistory(company.symbol, 10);
  } catch {
    history = null;
  }

  let valuation: Valuation | null = null;
  try {
    valuation = await getValuation(company.symbol);
  } catch {
    valuation = null;
  }

  let zones: BuySellZones | null = null;
  try {
    zones = await getZones(company.symbol);
  } catch {
    zones = null;
  }

  let recommendation: RecommendationReport | null = null;
  try {
    recommendation = await getRecommendation(company.symbol);
  } catch {
    recommendation = null;
  }

  let alerts: AlertReport | null = null;
  try {
    alerts = await getAlerts(company.symbol);
  } catch {
    alerts = null;
  }

  let scores: CompanyScores | null = null;
  try {
    scores = await getScores(company.symbol);
  } catch {
    scores = null;
  }

  let dataQuality: DataQualityReport | null = null;
  try {
    dataQuality = await getDataQuality(company.symbol);
  } catch {
    dataQuality = null;
  }

  return (
    <main className="mx-auto flex w-full max-w-4xl flex-1 flex-col px-6 py-12">
      <Link
        href="/companies"
        className="text-sm text-text-muted transition-colors hover:text-text"
      >
        ← All companies
      </Link>

      <header className="mt-6 flex flex-wrap items-start justify-between gap-4">
        <div>
          <span className="font-mono text-sm font-semibold text-accent">
            {company.symbol}
          </span>
          <h1 className="mt-1 text-3xl font-semibold text-text">
            {company.name}
          </h1>
          <p className="mt-1 text-sm text-text-muted">
            {[company.sector, company.industry].filter(Boolean).join(" · ") ||
              "—"}
          </p>
          <CompanyActions symbol={company.symbol} />
        </div>
        <div className="text-right">
          <div className="text-2xl font-semibold text-text">
            {formatPrice(company.current_price)}
          </div>
          <div className="text-xs text-text-muted">Current price</div>
        </div>
      </header>

      <dl className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Stat label="Market cap" value={formatMarketCap(company.market_cap)} />
        <Stat
          label="52-week high"
          value={formatPrice(company.fifty_two_week_high)}
        />
        <Stat
          label="52-week low"
          value={formatPrice(company.fifty_two_week_low)}
        />
        <Stat
          label="Dividend yield"
          value={formatPercent(company.dividend_yield)}
        />
        <Stat label="Fiscal year end" value={company.fiscal_year_end ?? "—"} />
        <Stat label="Listed" value={company.listing_date ?? "—"} />
      </dl>

      {company.description ? (
        <section className="mt-10">
          <h2 className="text-lg font-semibold text-text">About</h2>
          <p className="mt-2 text-sm leading-relaxed text-text-muted">
            {company.description}
          </p>
        </section>
      ) : null}

      {company.website ? (
        <a
          href={company.website}
          target="_blank"
          rel="noopener noreferrer"
          className="mt-6 inline-flex w-fit items-center text-sm text-accent transition-colors hover:opacity-90"
        >
          Visit company website ↗
        </a>
      ) : null}

      {valuation ? <ValuationView valuation={valuation} /> : null}

      {zones ? <BuySellZonesView zones={zones} /> : null}

      {recommendation ? (
        <RecommendationView recommendation={recommendation} />
      ) : null}

      {scores ? <ScoresView scores={scores} /> : null}

      {alerts ? <AlertsView report={alerts} /> : null}

      <AssistantView symbol={company.symbol} />

      {ratios ? <FinancialRatiosView ratios={ratios} /> : null}

      {history && history.points.length > 0 ? (
        <FinancialCharts history={history} />
      ) : null}

      {financials ? (
        <FinancialStatementsView
          symbol={company.symbol}
          financials={financials}
          activePeriod={activePeriod}
        />
      ) : (
        <p className="mt-14 text-sm text-text-muted">
          Financial statements are currently unavailable.
        </p>
      )}

      {dataQuality ? <DataQualityView report={dataQuality} /> : null}

      <p className="mt-16 border-t border-border pt-6 text-xs text-text-muted">
        Figures shown are illustrative development data and must not be used for
        investment decisions. Not financial advice.
      </p>
    </main>
  );
}
