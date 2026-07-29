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

/** Headline recommendation derived from the discount to intrinsic value. */
export type Recommendation = "BUY" | "HOLD" | "SELL";

/** A single valuation model's per-share estimate and its blend weight. */
export interface ValuationModelResult {
  name: string;
  value: number | null;
  weight: number;
  applied: boolean;
}

/** Key assumptions behind the valuation, surfaced for transparency. */
export interface ValuationAssumptions {
  discount_rate: number;
  terminal_growth: number;
  projection_years: number;
}

/**
 * Blended intrinsic value and recommendation. Intrinsic value and current
 * price are plain numbers (PKR); discount is a percentage (positive ==
 * undervalued).
 */
export interface Valuation {
  symbol: string;
  currency: string;
  intrinsic_value: number | null;
  current_price: number | null;
  discount: number | null;
  recommendation: Recommendation;
  models: ValuationModelResult[];
  assumptions: ValuationAssumptions;
}

/** The five buy/sell price bands, cheapest to most expensive. */
export type ZoneName = "STRONG_BUY" | "BUY" | "HOLD" | "SELL" | "STRONG_SELL";

/** A single price band with optional bounds (PKR). Nulls are unbounded. */
export interface PriceZone {
  name: ZoneName;
  label: string;
  lower: number | null;
  upper: number | null;
  is_current: boolean;
}

/** Price bands derived from a company's intrinsic value. */
export interface BuySellZones {
  symbol: string;
  currency: string;
  intrinsic_value: number | null;
  current_price: number | null;
  current_zone: ZoneName | null;
  zones: PriceZone[];
}

/** Whether a reason supports, opposes, or is neutral toward the call. */
export type Sentiment = "positive" | "negative" | "neutral";

/** A single explainable factor behind the recommendation. */
export interface RecommendationReason {
  label: string;
  detail: string;
  sentiment: Sentiment;
}

/**
 * The headline BUY/HOLD/SELL call plus the transparent reasons that justify
 * it. Intrinsic value and current price are plain numbers (PKR); discount is a
 * percentage (positive == undervalued).
 */
export interface RecommendationReport {
  symbol: string;
  recommendation: Recommendation;
  summary: string;
  intrinsic_value: number | null;
  current_price: number | null;
  discount: number | null;
  reasons: RecommendationReason[];
}

/** A single position submitted for portfolio analysis. */
export interface PortfolioHolding {
  symbol: string;
  quantity: number;
  average_cost: number;
}

/** Computed analytics for one holding. Money figures are PKR; MoS/CAGR are %. */
export interface HoldingAnalysis {
  symbol: string;
  name: string | null;
  quantity: number;
  average_cost: number;
  current_price: number | null;
  cost_basis: number;
  market_value: number | null;
  gain_loss: number | null;
  gain_loss_pct: number | null;
  intrinsic_value: number | null;
  intrinsic_total: number | null;
  margin_of_safety: number | null;
  expected_cagr: number | null;
  recommendation: Recommendation | null;
  weight: number | null;
}

/** Portfolio-level roll-up across all holdings. */
export interface PortfolioSummary {
  holdings_count: number;
  total_cost: number;
  total_market_value: number | null;
  total_gain_loss: number | null;
  total_gain_loss_pct: number | null;
  total_intrinsic_value: number | null;
  margin_of_safety: number | null;
  expected_cagr: number | null;
  health_score: number | null;
}

/** The full stateless portfolio analysis response. */
export interface PortfolioAnalysis {
  currency: string;
  summary: PortfolioSummary;
  holdings: HoldingAnalysis[];
}

export type AlertSentiment = "positive" | "negative" | "neutral";

/** A single alert condition currently active for a company. */
export interface AlertSignal {
  type: string;
  title: string;
  detail: string;
  sentiment: AlertSentiment;
}

/** The set of alert conditions active for a company right now. */
export interface AlertReport {
  symbol: string;
  currency: string;
  alerts: AlertSignal[];
}

/** A deterministic answer composed from a company's computed data. */
export interface AssistantAnswer {
  symbol: string;
  question: string;
  intent: string;
  answer: string;
  highlights: string[];
  recommendation: Recommendation;
  disclaimer: string;
}

export type ScoreRating = "excellent" | "good" | "fair" | "weak" | "na";

/** A single pass/fail criterion behind a score (`passed` null == no data). */
export interface ScoreCheck {
  label: string;
  detail: string;
  passed: boolean | null;
}

/** A 0-100 composite score with its underlying checks. */
export interface CompositeScore {
  key: string;
  label: string;
  value: number | null;
  rating: ScoreRating;
  checks: ScoreCheck[];
}

/** The Piotroski F-Score (0-9) with its nine checks. */
export interface PiotroskiScore {
  value: number | null;
  max_score: number;
  rating: string;
  checks: ScoreCheck[];
}

/** The Altman Z-Score with its distress band. */
export interface AltmanScore {
  value: number | null;
  band: string;
  detail: string;
}

/** The two Magic Formula components, each as a percentage. */
export interface MagicFormula {
  roic: number | null;
  earnings_yield: number | null;
  detail: string;
}

/** The full investment scorecard for a company. */
export interface CompanyScores {
  symbol: string;
  currency: string;
  composites: CompositeScore[];
  piotroski: PiotroskiScore;
  altman_z: AltmanScore;
  magic_formula: MagicFormula;
}
