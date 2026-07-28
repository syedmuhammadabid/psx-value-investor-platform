import Link from "next/link";

import { formatStatementValue } from "@/lib/format";
import type {
  FinancialPeriod,
  FinancialStatements,
  PeriodType,
} from "@/lib/types";

interface Row {
  key: string;
  label: string;
  emphasis?: boolean;
}

const INCOME_ROWS: Row[] = [
  { key: "revenue", label: "Revenue", emphasis: true },
  { key: "cost_of_revenue", label: "Cost of revenue" },
  { key: "gross_profit", label: "Gross profit", emphasis: true },
  { key: "operating_expenses", label: "Operating expenses" },
  { key: "operating_income", label: "Operating income", emphasis: true },
  { key: "interest_expense", label: "Interest expense" },
  { key: "pretax_income", label: "Pre-tax income" },
  { key: "tax_expense", label: "Tax expense" },
  { key: "net_income", label: "Net income", emphasis: true },
  { key: "eps_basic", label: "EPS (basic)" },
  { key: "shares_outstanding", label: "Shares outstanding" },
];

const BALANCE_ROWS: Row[] = [
  { key: "cash_and_equivalents", label: "Cash & equivalents" },
  { key: "inventory", label: "Inventory" },
  { key: "current_assets", label: "Current assets" },
  { key: "total_assets", label: "Total assets", emphasis: true },
  { key: "current_liabilities", label: "Current liabilities" },
  { key: "total_debt", label: "Total debt" },
  { key: "total_liabilities", label: "Total liabilities", emphasis: true },
  { key: "total_equity", label: "Total equity", emphasis: true },
];

const CASH_FLOW_ROWS: Row[] = [
  { key: "operating_cash_flow", label: "Operating cash flow", emphasis: true },
  { key: "capital_expenditure", label: "Capital expenditure" },
  { key: "free_cash_flow", label: "Free cash flow", emphasis: true },
  { key: "investing_cash_flow", label: "Investing cash flow" },
  { key: "financing_cash_flow", label: "Financing cash flow" },
  { key: "dividends_paid", label: "Dividends paid" },
];

function periodLabel(period: FinancialPeriod): string {
  return period.fiscal_period === "FY"
    ? `FY ${period.fiscal_year}`
    : `${period.fiscal_period} ${period.fiscal_year}`;
}

function cellValue(
  period: FinancialPeriod,
  statement: "income_statement" | "balance_sheet" | "cash_flow",
  key: string
): string {
  const group = period[statement] as unknown as Record<string, string | null>;
  return formatStatementValue(group[key]);
}

function StatementTable({
  title,
  rows,
  statement,
  periods,
}: {
  title: string;
  rows: Row[];
  statement: "income_statement" | "balance_sheet" | "cash_flow";
  periods: FinancialPeriod[];
}) {
  return (
    <section className="mt-8">
      <h3 className="text-base font-semibold text-text">{title}</h3>
      <div className="mt-3 overflow-x-auto rounded-lg border border-border">
        <table className="w-full min-w-[32rem] border-collapse text-sm">
          <caption className="sr-only">
            {title} by period, values in PKR.
          </caption>
          <thead>
            <tr className="border-b border-border bg-surface">
              <th
                scope="col"
                className="sticky left-0 z-10 bg-surface px-4 py-2 text-left font-medium text-text-muted"
              >
                Line item
              </th>
              {periods.map((period) => (
                <th
                  key={`${period.fiscal_year}-${period.fiscal_period}`}
                  scope="col"
                  className="whitespace-nowrap px-4 py-2 text-right font-medium text-text-muted"
                >
                  {periodLabel(period)}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((row) => (
              <tr
                key={row.key}
                className="border-b border-border last:border-0"
              >
                <th
                  scope="row"
                  className={`sticky left-0 z-10 bg-surface px-4 py-2 text-left font-normal ${
                    row.emphasis ? "text-text" : "text-text-muted"
                  }`}
                >
                  {row.label}
                </th>
                {periods.map((period) => (
                  <td
                    key={`${period.fiscal_year}-${period.fiscal_period}`}
                    className={`whitespace-nowrap px-4 py-2 text-right tabular-nums ${
                      row.emphasis ? "font-medium text-text" : "text-text-muted"
                    }`}
                  >
                    {cellValue(period, statement, row.key)}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}

export function FinancialStatementsView({
  symbol,
  financials,
  activePeriod,
}: {
  symbol: string;
  financials: FinancialStatements;
  activePeriod: PeriodType;
}) {
  const tabs: { label: string; value: PeriodType }[] = [
    { label: "Annual", value: "annual" },
    { label: "Quarterly", value: "quarterly" },
  ];

  return (
    <section id="financials" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <h2 className="text-lg font-semibold text-text">
          Financial statements
        </h2>
        <div
          role="tablist"
          aria-label="Reporting period"
          className="inline-flex rounded-md border border-border p-0.5"
        >
          {tabs.map((tab) => {
            const active = tab.value === activePeriod;
            return (
              <Link
                key={tab.value}
                role="tab"
                aria-selected={active}
                href={`/companies/${symbol}?period=${tab.value}#financials`}
                scroll={false}
                className={`rounded px-3 py-1 text-sm transition-colors ${
                  active
                    ? "bg-surface-2 text-text"
                    : "text-text-muted hover:text-text"
                }`}
              >
                {tab.label}
              </Link>
            );
          })}
        </div>
      </div>

      {financials.periods.length === 0 ? (
        <p className="mt-6 text-sm text-text-muted">
          No {activePeriod} statements are available for this company yet.
        </p>
      ) : (
        <>
          <StatementTable
            title="Income statement"
            rows={INCOME_ROWS}
            statement="income_statement"
            periods={financials.periods}
          />
          <StatementTable
            title="Balance sheet"
            rows={BALANCE_ROWS}
            statement="balance_sheet"
            periods={financials.periods}
          />
          <StatementTable
            title="Cash flow"
            rows={CASH_FLOW_ROWS}
            statement="cash_flow"
            periods={financials.periods}
          />
        </>
      )}
    </section>
  );
}
