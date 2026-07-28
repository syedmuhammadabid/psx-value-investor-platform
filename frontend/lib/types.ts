/** Shared API types. Mirror the backend Pydantic schemas.
 *
 * These are hand-written for now. Once the API stabilises we can generate
 * them from the backend's OpenAPI schema (see PROJECT_ROADMAP.md).
 */

export interface CompanySummary {
  symbol: string;
  name: string;
  sector: string | null;
  industry: string | null;
  market_cap: number | null;
  current_price: number | null;
}

export interface CompanyDetail extends CompanySummary {
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
  dividend_yield: number | null;
  website: string | null;
  fiscal_year_end: string | null;
  listing_date: string | null;
  description: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export type CompanySort = "market_cap" | "name" | "symbol";

export type PeriodType = "annual" | "quarterly";

/**
 * Monetary values arrive as decimal strings (e.g. "1200.00") to preserve
 * precision. Nullable where a line item is unavailable.
 */
export type Money = string | null;

export interface IncomeStatement {
  revenue: Money;
  cost_of_revenue: Money;
  gross_profit: Money;
  operating_expenses: Money;
  operating_income: Money;
  interest_expense: Money;
  pretax_income: Money;
  tax_expense: Money;
  net_income: Money;
  eps_basic: Money;
  shares_outstanding: Money;
}

export interface BalanceSheet {
  cash_and_equivalents: Money;
  inventory: Money;
  current_assets: Money;
  total_assets: Money;
  current_liabilities: Money;
  total_debt: Money;
  total_liabilities: Money;
  total_equity: Money;
}

export interface CashFlow {
  operating_cash_flow: Money;
  capital_expenditure: Money;
  investing_cash_flow: Money;
  financing_cash_flow: Money;
  dividends_paid: Money;
  free_cash_flow: Money;
}

export interface FinancialPeriod {
  fiscal_year: number;
  fiscal_period: string;
  period_end: string;
  currency: string;
  income_statement: IncomeStatement;
  balance_sheet: BalanceSheet;
  cash_flow: CashFlow;
}

export interface FinancialStatements {
  symbol: string;
  period_type: PeriodType;
  periods: FinancialPeriod[];
}

/**
 * Financial ratios. Percentage-style figures (margins, returns, growth, FCF
 * yield, dividend yield) are already expressed as percentages (e.g. 23.45 ==
 * 23.45%). Multiples (P/E, P/B, ratios) are plain numbers.
 */
export interface ProfitabilityRatios {
  gross_margin: number | null;
  operating_margin: number | null;
  net_margin: number | null;
  roe: number | null;
  roa: number | null;
  roic: number | null;
}

export interface ValuationRatios {
  pe: number | null;
  pb: number | null;
  peg: number | null;
  ev_ebitda: number | null;
  price_to_sales: number | null;
  dividend_yield: number | null;
}

export interface DebtRatios {
  debt_to_equity: number | null;
  interest_coverage: number | null;
}

export interface LiquidityRatios {
  current_ratio: number | null;
  quick_ratio: number | null;
}

export interface CashFlowRatios {
  operating_cash_flow: number | null;
  free_cash_flow: number | null;
  fcf_yield: number | null;
}

export interface GrowthRatios {
  revenue_cagr: number | null;
  eps_cagr: number | null;
  dividend_cagr: number | null;
  years: number;
}

export interface FinancialRatios {
  symbol: string;
  fiscal_year: number | null;
  fiscal_period: string | null;
  period_end: string | null;
  profitability: ProfitabilityRatios;
  valuation: ValuationRatios;
  debt: DebtRatios;
  liquidity: LiquidityRatios;
  cash_flow: CashFlowRatios;
  growth: GrowthRatios;
}

/**
 * A single annual data point for trend charts. Money figures are plain numbers
 * (PKR); ROE and ROIC are percentages (e.g. 24.0 == 24%).
 */
export interface MetricPoint {
  fiscal_year: number;
  period_end: string;
  revenue: number | null;
  net_income: number | null;
  eps: number | null;
  roe: number | null;
  roic: number | null;
  dividend_per_share: number | null;
  book_value_per_share: number | null;
  free_cash_flow: number | null;
}

/** A company's annual metric series, oldest period first. */
export interface CompanyHistory {
  symbol: string;
  points: MetricPoint[];
}

/**
 * A screener match. Money figures arrive as decimal strings; percentage-style
 * metrics (ROE, ROIC, dividend yield, revenue growth) are percentages, while
 * P/E and debt/equity are plain numbers.
 */
export interface ScreenerRow {
  symbol: string;
  name: string;
  sector: string | null;
  market_cap: Money;
  current_price: Money;
  roe: number | null;
  roic: number | null;
  pe: number | null;
  dividend_yield: number | null;
  debt_to_equity: number | null;
  revenue_growth: number | null;
  free_cash_flow: number | null;
}

export interface ScreenerResult {
  count: number;
  items: ScreenerRow[];
}
