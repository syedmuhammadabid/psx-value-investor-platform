"use client";

import Link from "next/link";
import {
  useCallback,
  useEffect,
  useMemo,
  useState,
  useSyncExternalStore,
} from "react";

import { analyzePortfolio, ApiError } from "@/lib/api";
import { compact, formatPrice } from "@/lib/format";
import type {
  HoldingAnalysis,
  PortfolioAnalysis,
  PortfolioHolding,
  Recommendation,
} from "@/lib/types";

const STORAGE_KEY = "psx-portfolio-holdings";

const RECOMMENDATION_STYLES: Record<Recommendation, string> = {
  BUY: "border-positive/40 bg-positive/10 text-positive",
  HOLD: "border-warning/40 bg-warning/10 text-warning",
  SELL: "border-negative/40 bg-negative/10 text-negative",
};

/** Colour a signed figure: gains positive, losses negative. */
function tone(value: number | null | undefined): string {
  if (value == null || value === 0) return "text-text";
  return value > 0 ? "text-positive" : "text-negative";
}

/** Signed percentage, e.g. `+24.10%` / `-8.00%`. */
function signedPercent(value: number | null): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(2)}%`;
}

/** Signed compact PKR figure, e.g. `+Rs 12.05K`. */
function signedMoney(value: number | null): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${sign}Rs ${compact(Math.abs(value))}`;
}

function healthTone(score: number | null): string {
  if (score == null) return "text-text";
  if (score >= 66) return "text-positive";
  if (score >= 40) return "text-warning";
  return "text-negative";
}

function isValidHolding(value: unknown): value is PortfolioHolding {
  if (typeof value !== "object" || value === null) return false;
  const record = value as Record<string, unknown>;
  return (
    typeof record.symbol === "string" &&
    typeof record.quantity === "number" &&
    typeof record.average_cost === "number"
  );
}

// A tiny localStorage-backed store so holdings survive reloads. Using
// useSyncExternalStore keeps hydration safe (server snapshot is empty) and
// avoids calling setState inside an effect.
const EMPTY_HOLDINGS: PortfolioHolding[] = [];
const listeners = new Set<() => void>();
let cache: PortfolioHolding[] | null = null;

function readHoldings(): PortfolioHolding[] {
  if (cache !== null) return cache;
  try {
    const raw = window.localStorage.getItem(STORAGE_KEY);
    const parsed: unknown = raw ? JSON.parse(raw) : null;
    cache = Array.isArray(parsed) ? parsed.filter(isValidHolding) : [];
  } catch {
    cache = [];
  }
  return cache;
}

function writeHoldings(next: PortfolioHolding[]): void {
  cache = next;
  try {
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Ignore quota/serialisation errors.
  }
  for (const listener of listeners) listener();
}

function subscribeHoldings(callback: () => void): () => void {
  listeners.add(callback);
  return () => {
    listeners.delete(callback);
  };
}

function SummaryCard({
  label,
  value,
  valueTone = "text-text",
  hint,
}: {
  label: string;
  value: string;
  valueTone?: string;
  hint?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      <div className="text-xs text-text-muted">{label}</div>
      <div className={`mt-1 text-xl font-semibold tabular-nums ${valueTone}`}>
        {value}
      </div>
      {hint ? <div className="mt-1 text-xs text-text-muted">{hint}</div> : null}
    </div>
  );
}

function HoldingsTable({
  holdings,
  onRemove,
}: {
  holdings: HoldingAnalysis[];
  onRemove: (symbol: string) => void;
}) {
  return (
    <div className="mt-6 overflow-x-auto">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b border-border text-left text-xs text-text-muted">
            <th className="py-2 pr-4 font-medium">Symbol</th>
            <th className="py-2 pr-4 text-right font-medium">Qty</th>
            <th className="py-2 pr-4 text-right font-medium">Avg cost</th>
            <th className="py-2 pr-4 text-right font-medium">Price</th>
            <th className="py-2 pr-4 text-right font-medium">Value</th>
            <th className="py-2 pr-4 text-right font-medium">Gain/Loss</th>
            <th className="py-2 pr-4 text-right font-medium">MoS</th>
            <th className="py-2 pr-4 text-right font-medium">Exp. CAGR</th>
            <th className="py-2 pr-4 font-medium">Call</th>
            <th className="py-2 pr-2 text-right font-medium">Weight</th>
            <th className="py-2 font-medium" aria-label="Actions" />
          </tr>
        </thead>
        <tbody>
          {holdings.map((h) => (
            <tr key={h.symbol} className="border-b border-border/60">
              <td className="py-3 pr-4">
                <Link
                  href={`/companies/${h.symbol}`}
                  className="font-mono font-semibold text-accent transition-colors hover:opacity-90"
                >
                  {h.symbol}
                </Link>
                {h.name ? (
                  <div className="text-xs text-text-muted">{h.name}</div>
                ) : null}
              </td>
              <td className="py-3 pr-4 text-right tabular-nums text-text">
                {h.quantity.toLocaleString("en-PK")}
              </td>
              <td className="py-3 pr-4 text-right tabular-nums text-text">
                {formatPrice(h.average_cost)}
              </td>
              <td className="py-3 pr-4 text-right tabular-nums text-text">
                {formatPrice(h.current_price)}
              </td>
              <td className="py-3 pr-4 text-right tabular-nums text-text">
                {h.market_value == null ? "—" : `Rs ${compact(h.market_value)}`}
              </td>
              <td
                className={`py-3 pr-4 text-right tabular-nums ${tone(h.gain_loss)}`}
              >
                <div>{signedMoney(h.gain_loss)}</div>
                <div className="text-xs">{signedPercent(h.gain_loss_pct)}</div>
              </td>
              <td
                className={`py-3 pr-4 text-right tabular-nums ${tone(h.margin_of_safety)}`}
              >
                {signedPercent(h.margin_of_safety)}
              </td>
              <td className="py-3 pr-4 text-right tabular-nums text-text">
                {signedPercent(h.expected_cagr)}
              </td>
              <td className="py-3 pr-4">
                {h.recommendation ? (
                  <span
                    className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${RECOMMENDATION_STYLES[h.recommendation]}`}
                  >
                    {h.recommendation}
                  </span>
                ) : (
                  <span className="text-text-muted">—</span>
                )}
              </td>
              <td className="py-3 pr-2 text-right tabular-nums text-text-muted">
                {h.weight == null ? "—" : `${h.weight.toFixed(1)}%`}
              </td>
              <td className="py-3 text-right">
                <button
                  type="button"
                  onClick={() => onRemove(h.symbol)}
                  className="text-xs text-text-muted transition-colors hover:text-negative"
                  aria-label={`Remove ${h.symbol}`}
                >
                  Remove
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

export default function PortfolioPage() {
  const holdings = useSyncExternalStore(
    subscribeHoldings,
    readHoldings,
    () => EMPTY_HOLDINGS
  );
  const [analysis, setAnalysis] = useState<PortfolioAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [symbol, setSymbol] = useState("");
  const [quantity, setQuantity] = useState("");
  const [averageCost, setAverageCost] = useState("");

  // Re-analyse whenever holdings change.
  useEffect(() => {
    if (holdings.length === 0) return;
    let cancelled = false;
    const run = async () => {
      setLoading(true);
      setError(null);
      try {
        const result = await analyzePortfolio(holdings);
        if (!cancelled) setAnalysis(result);
      } catch (err: unknown) {
        if (cancelled) return;
        const message =
          err instanceof ApiError && err.status === 404
            ? "One of your symbols was not found. Check and try again."
            : "Unable to analyse the portfolio. Is the backend running?";
        setError(message);
        setAnalysis(null);
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [holdings]);

  const addHolding = useCallback(
    (event: React.FormEvent) => {
      event.preventDefault();
      const cleanSymbol = symbol.trim().toUpperCase();
      const qty = Number(quantity);
      const cost = Number(averageCost);
      if (!cleanSymbol || !Number.isFinite(qty) || qty <= 0) return;
      if (!Number.isFinite(cost) || cost < 0) return;

      const existing = holdings.find((h) => h.symbol === cleanSymbol);
      if (existing) {
        // Merge into a weighted-average position.
        const totalQty = existing.quantity + qty;
        const totalCost =
          existing.quantity * existing.average_cost + qty * cost;
        writeHoldings(
          holdings.map((h) =>
            h.symbol === cleanSymbol
              ? {
                  symbol: cleanSymbol,
                  quantity: totalQty,
                  average_cost: totalCost / totalQty,
                }
              : h
          )
        );
      } else {
        writeHoldings([
          ...holdings,
          { symbol: cleanSymbol, quantity: qty, average_cost: cost },
        ]);
      }
      setSymbol("");
      setQuantity("");
      setAverageCost("");
    },
    [symbol, quantity, averageCost, holdings]
  );

  const removeHolding = useCallback(
    (target: string) => {
      writeHoldings(holdings.filter((h) => h.symbol !== target));
    },
    [holdings]
  );

  const summary = holdings.length > 0 ? analysis?.summary : undefined;
  const holdingRows = useMemo(
    () => (holdings.length > 0 ? (analysis?.holdings ?? []) : []),
    [analysis, holdings]
  );

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-12">
      <Link
        href="/"
        className="text-sm text-text-muted transition-colors hover:text-text"
      >
        ← Home
      </Link>

      <header className="mt-6">
        <h1 className="text-3xl font-semibold text-text">Portfolio tracker</h1>
        <p className="mt-2 max-w-2xl text-sm text-text-muted">
          Add your holdings to see gain/loss, margin of safety against intrinsic
          value, expected CAGR, and an overall portfolio health score. Your
          holdings stay in this browser only.
        </p>
      </header>

      <form
        onSubmit={addHolding}
        className="mt-8 grid gap-4 rounded-lg border border-border bg-surface p-5 sm:grid-cols-[1.5fr_1fr_1fr_auto] sm:items-end"
      >
        <div>
          <label
            htmlFor="symbol"
            className="block text-xs font-medium text-text-muted"
          >
            Symbol
          </label>
          <input
            id="symbol"
            value={symbol}
            onChange={(e) => setSymbol(e.target.value)}
            placeholder="ENGRO"
            className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 font-mono text-sm text-text uppercase outline-none focus:border-accent"
          />
        </div>
        <div>
          <label
            htmlFor="quantity"
            className="block text-xs font-medium text-text-muted"
          >
            Quantity
          </label>
          <input
            id="quantity"
            type="number"
            min="0"
            step="any"
            value={quantity}
            onChange={(e) => setQuantity(e.target.value)}
            placeholder="100"
            className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text tabular-nums outline-none focus:border-accent"
          />
        </div>
        <div>
          <label
            htmlFor="average_cost"
            className="block text-xs font-medium text-text-muted"
          >
            Avg cost (Rs)
          </label>
          <input
            id="average_cost"
            type="number"
            min="0"
            step="any"
            value={averageCost}
            onChange={(e) => setAverageCost(e.target.value)}
            placeholder="305"
            className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text tabular-nums outline-none focus:border-accent"
          />
        </div>
        <button
          type="submit"
          className="rounded-md bg-accent px-5 py-2 text-sm font-semibold text-white transition-colors hover:opacity-90"
        >
          Add holding
        </button>
      </form>

      {error ? (
        <p className="mt-6 rounded-md border border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative">
          {error}
        </p>
      ) : null}

      {holdings.length === 0 ? (
        <p className="mt-10 text-sm text-text-muted">
          No holdings yet. Add a position above to build your portfolio.
        </p>
      ) : null}

      {summary ? (
        <section className="mt-8">
          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <SummaryCard
              label="Total value"
              value={
                summary.total_market_value == null
                  ? "—"
                  : `Rs ${compact(summary.total_market_value)}`
              }
              hint={`Cost Rs ${compact(summary.total_cost)}`}
            />
            <SummaryCard
              label="Total gain / loss"
              value={signedMoney(summary.total_gain_loss)}
              valueTone={tone(summary.total_gain_loss)}
              hint={signedPercent(summary.total_gain_loss_pct)}
            />
            <SummaryCard
              label="Margin of safety"
              value={signedPercent(summary.margin_of_safety)}
              valueTone={tone(summary.margin_of_safety)}
              hint={
                summary.total_intrinsic_value == null
                  ? "No intrinsic value"
                  : `Intrinsic Rs ${compact(summary.total_intrinsic_value)}`
              }
            />
            <SummaryCard
              label="Health score"
              value={
                summary.health_score == null
                  ? "—"
                  : `${summary.health_score}/100`
              }
              valueTone={healthTone(summary.health_score)}
              hint={
                summary.expected_cagr == null
                  ? undefined
                  : `Exp. CAGR ${signedPercent(summary.expected_cagr)}`
              }
            />
          </div>
        </section>
      ) : null}

      {loading && !summary ? (
        <p className="mt-8 text-sm text-text-muted">Analysing portfolio…</p>
      ) : null}

      {holdingRows.length > 0 ? (
        <HoldingsTable holdings={holdingRows} onRemove={removeHolding} />
      ) : null}

      <p className="mt-16 border-t border-border pt-6 text-xs text-text-muted">
        For informational and educational purposes only. Margin of safety and
        expected CAGR assume price converges to our estimated intrinsic value —
        not a forecast, and not financial advice.
      </p>
    </main>
  );
}
