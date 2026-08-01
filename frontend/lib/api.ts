/** Minimal, typed API client for the backend.
 *
 * Server Components call these helpers directly during SSR. All requests are
 * made against `NEXT_PUBLIC_API_BASE_URL` and surface a typed `ApiError` on
 * failure so callers can render sensible error states.
 */
import type {
  AlertReport,
  AssistantAnswer,
  BuySellZones,
  CompanyDetail,
  CompanyHistory,
  CompanyScores,
  CompanySort,
  CompanySummary,
  DataQualityReport,
  FinancialRatios,
  FinancialStatements,
  Page,
  PeriodType,
  PortfolioAnalysis,
  PortfolioHolding,
  RecommendationReport,
  ScreenerResult,
  Valuation,
} from "./types";

/** Browser-side URL (embedded in the JS bundle, resolved by the user's browser). */
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";

/**
 * Server-side URL used during SSR. Inside Docker, `localhost` refers to the
 * container itself, so we need the Docker service name to reach the backend.
 * Falls back to the public URL when not set (e.g. local dev without Docker).
 */
const SERVER_API_BASE_URL =
  process.env.INTERNAL_API_BASE_URL ?? API_BASE_URL;

/** Pick the right base URL depending on whether we're on server or client. */
const getBaseUrl = () =>
  typeof window === "undefined" ? SERVER_API_BASE_URL : API_BASE_URL;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${getBaseUrl()}${path}`, {
      // Revalidate listings periodically; overrideable per call.
      next: { revalidate: 60 },
      headers: { Accept: "application/json" },
      ...init,
    });
  } catch {
    throw new ApiError("Unable to reach the API. Is the backend running?", 503);
  }

  if (response.status === 404) {
    throw new ApiError("Not found.", 404);
  }
  if (!response.ok) {
    throw new ApiError(`Request failed (${response.status}).`, response.status);
  }

  return (await response.json()) as T;
}

export interface ListCompaniesParams {
  q?: string;
  sector?: string;
  sort?: CompanySort;
  limit?: number;
  offset?: number;
}

export function listCompanies(
  params: ListCompaniesParams = {}
): Promise<Page<CompanySummary>> {
  const search = new URLSearchParams();
  if (params.q) search.set("q", params.q);
  if (params.sector) search.set("sector", params.sector);
  if (params.sort) search.set("sort", params.sort);
  if (params.limit != null) search.set("limit", String(params.limit));
  if (params.offset != null) search.set("offset", String(params.offset));

  const query = search.toString();
  return apiFetch<Page<CompanySummary>>(
    `/companies${query ? `?${query}` : ""}`
  );
}

export function getCompany(symbol: string): Promise<CompanyDetail> {
  return apiFetch<CompanyDetail>(`/companies/${encodeURIComponent(symbol)}`);
}

export function searchCompanies(
  q: string,
  limit = 10
): Promise<CompanySummary[]> {
  const search = new URLSearchParams({ q, limit: String(limit) });
  return apiFetch<CompanySummary[]>(`/search?${search.toString()}`);
}

export function getFinancials(
  symbol: string,
  period: PeriodType = "annual",
  limit = 10
): Promise<FinancialStatements> {
  const search = new URLSearchParams({ period, limit: String(limit) });
  return apiFetch<FinancialStatements>(
    `/companies/${encodeURIComponent(symbol)}/financials?${search.toString()}`
  );
}

export function getRatios(symbol: string): Promise<FinancialRatios> {
  return apiFetch<FinancialRatios>(
    `/companies/${encodeURIComponent(symbol)}/ratios`
  );
}

export function getHistory(
  symbol: string,
  limit = 10
): Promise<CompanyHistory> {
  const search = new URLSearchParams({ limit: String(limit) });
  return apiFetch<CompanyHistory>(
    `/companies/${encodeURIComponent(symbol)}/history?${search.toString()}`
  );
}

export function getValuation(symbol: string): Promise<Valuation> {
  return apiFetch<Valuation>(
    `/companies/${encodeURIComponent(symbol)}/valuation`
  );
}

export function getZones(symbol: string): Promise<BuySellZones> {
  return apiFetch<BuySellZones>(
    `/companies/${encodeURIComponent(symbol)}/zones`
  );
}

export function getRecommendation(
  symbol: string
): Promise<RecommendationReport> {
  return apiFetch<RecommendationReport>(
    `/companies/${encodeURIComponent(symbol)}/recommendation`
  );
}

export function analyzePortfolio(
  holdings: PortfolioHolding[]
): Promise<PortfolioAnalysis> {
  return apiFetch<PortfolioAnalysis>(`/portfolio/analyze`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    cache: "no-store",
    body: JSON.stringify({ holdings }),
  });
}

export function getAlerts(symbol: string): Promise<AlertReport> {
  return apiFetch<AlertReport>(
    `/companies/${encodeURIComponent(symbol)}/alerts`
  );
}

export function getScores(symbol: string): Promise<CompanyScores> {
  return apiFetch<CompanyScores>(
    `/companies/${encodeURIComponent(symbol)}/scores`
  );
}

export function getDataQuality(symbol: string): Promise<DataQualityReport> {
  return apiFetch<DataQualityReport>(
    `/companies/${encodeURIComponent(symbol)}/data-quality`
  );
}

export function askAssistant(
  symbol: string,
  question: string
): Promise<AssistantAnswer> {
  return apiFetch<AssistantAnswer>(
    `/companies/${encodeURIComponent(symbol)}/assistant`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      cache: "no-store",
      body: JSON.stringify({ question }),
    }
  );
}

export interface ScreenerParams {
  min_roe?: number;
  min_roic?: number;
  max_pe?: number;
  min_dividend_yield?: number;
  max_debt_to_equity?: number;
  min_revenue_growth?: number;
  positive_fcf?: boolean;
  sector?: string;
  limit?: number;
}

export function runScreener(
  params: ScreenerParams = {}
): Promise<ScreenerResult> {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === "") continue;
    if (value === false) continue;
    search.set(key, String(value));
  }
  const query = search.toString();
  return apiFetch<ScreenerResult>(`/screener${query ? `?${query}` : ""}`);
}
