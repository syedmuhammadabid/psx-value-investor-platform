import {
  formatMarketCap,
  formatMultiple,
  formatPercent,
  formatRatio,
} from "@/lib/format";
import type { FinancialRatios } from "@/lib/types";

type Formatter = (value: number | null) => string;

interface Metric {
  label: string;
  value: number | null;
  format: Formatter;
}

interface Group {
  title: string;
  metrics: Metric[];
}

function periodLabel(ratios: FinancialRatios): string | null {
  if (ratios.fiscal_year == null) return null;
  const period = ratios.fiscal_period ?? "FY";
  return period === "FY"
    ? `FY ${ratios.fiscal_year}`
    : `${period} ${ratios.fiscal_year}`;
}

function buildGroups(ratios: FinancialRatios): Group[] {
  const { profitability, valuation, debt, liquidity, cash_flow, growth } =
    ratios;
  const growthWindow =
    growth.years > 0 ? ` (${growth.years}y CAGR)` : " (CAGR)";

  return [
    {
      title: "Profitability",
      metrics: [
        { label: "ROE", value: profitability.roe, format: formatPercent },
        { label: "ROA", value: profitability.roa, format: formatPercent },
        { label: "ROIC", value: profitability.roic, format: formatPercent },
        {
          label: "Gross margin",
          value: profitability.gross_margin,
          format: formatPercent,
        },
        {
          label: "Operating margin",
          value: profitability.operating_margin,
          format: formatPercent,
        },
        {
          label: "Net margin",
          value: profitability.net_margin,
          format: formatPercent,
        },
      ],
    },
    {
      title: "Valuation",
      metrics: [
        { label: "P/E", value: valuation.pe, format: formatMultiple },
        { label: "P/B", value: valuation.pb, format: formatMultiple },
        { label: "PEG", value: valuation.peg, format: formatMultiple },
        {
          label: "EV/EBITDA",
          value: valuation.ev_ebitda,
          format: formatMultiple,
        },
        {
          label: "Price/Sales",
          value: valuation.price_to_sales,
          format: formatMultiple,
        },
        {
          label: "Dividend yield",
          value: valuation.dividend_yield,
          format: formatPercent,
        },
      ],
    },
    {
      title: "Debt",
      metrics: [
        {
          label: "Debt/Equity",
          value: debt.debt_to_equity,
          format: formatRatio,
        },
        {
          label: "Interest coverage",
          value: debt.interest_coverage,
          format: formatMultiple,
        },
      ],
    },
    {
      title: "Liquidity",
      metrics: [
        {
          label: "Current ratio",
          value: liquidity.current_ratio,
          format: formatRatio,
        },
        {
          label: "Quick ratio",
          value: liquidity.quick_ratio,
          format: formatRatio,
        },
      ],
    },
    {
      title: "Cash flow",
      metrics: [
        {
          label: "Operating cash flow",
          value: cash_flow.operating_cash_flow,
          format: formatMarketCap,
        },
        {
          label: "Free cash flow",
          value: cash_flow.free_cash_flow,
          format: formatMarketCap,
        },
        {
          label: "FCF yield",
          value: cash_flow.fcf_yield,
          format: formatPercent,
        },
      ],
    },
    {
      title: `Growth${growthWindow}`,
      metrics: [
        {
          label: "Revenue",
          value: growth.revenue_cagr,
          format: formatPercent,
        },
        { label: "EPS", value: growth.eps_cagr, format: formatPercent },
        {
          label: "Dividend",
          value: growth.dividend_cagr,
          format: formatPercent,
        },
      ],
    },
  ];
}

function GroupCard({ group }: { group: Group }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-5">
      <h3 className="text-sm font-semibold text-text-muted">{group.title}</h3>
      <dl className="mt-4 space-y-2.5">
        {group.metrics.map((metric) => (
          <div
            key={metric.label}
            className="flex items-baseline justify-between gap-4"
          >
            <dt className="text-sm text-text-muted">{metric.label}</dt>
            <dd className="text-sm font-medium tabular-nums text-text">
              {metric.format(metric.value)}
            </dd>
          </div>
        ))}
      </dl>
    </div>
  );
}

export function FinancialRatiosView({ ratios }: { ratios: FinancialRatios }) {
  const asOf = periodLabel(ratios);
  const groups = buildGroups(ratios);

  return (
    <section id="ratios" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Key ratios</h2>
        {asOf ? (
          <span className="text-sm text-text-muted">As of {asOf}</span>
        ) : null}
      </div>

      {asOf == null ? (
        <p className="mt-6 text-sm text-text-muted">
          Ratios will appear once annual financials are available for this
          company.
        </p>
      ) : (
        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {groups.map((group) => (
            <GroupCard key={group.title} group={group} />
          ))}
        </div>
      )}
    </section>
  );
}
