"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { getWatchlist, removeFromWatchlist, useAuth } from "@/lib/auth";
import { formatPrice } from "@/lib/format";
import type { Recommendation, WatchlistItem } from "@/lib/types";

const RECOMMENDATION_STYLES: Record<Recommendation, string> = {
  BUY: "border-positive/40 bg-positive/10 text-positive",
  HOLD: "border-warning/40 bg-warning/10 text-warning",
  SELL: "border-negative/40 bg-negative/10 text-negative",
};

function discountTone(value: number | null): string {
  if (value == null || value === 0) return "text-text";
  return value > 0 ? "text-positive" : "text-negative";
}

function signedPercent(value: number | null): string {
  if (value == null) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(1)}%`;
}

export default function WatchlistPage() {
  const { token, status } = useAuth();
  const [items, setItems] = useState<WatchlistItem[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (status !== "ready") return;
    let cancelled = false;
    const run = async () => {
      if (!token) {
        setItems(null);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const result = await getWatchlist();
        if (!cancelled) setItems(result);
      } catch {
        if (!cancelled)
          setError("Unable to load your watchlist. Is the backend running?");
      } finally {
        if (!cancelled) setLoading(false);
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token, status]);

  const remove = useCallback(async (symbol: string) => {
    try {
      await removeFromWatchlist(symbol);
      setItems((current) =>
        current ? current.filter((item) => item.symbol !== symbol) : current
      );
    } catch (err: unknown) {
      setError(
        err instanceof ApiError ? err.message : "Unable to remove this company."
      );
    }
  }, []);

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-12">
      <header>
        <h1 className="text-3xl font-semibold text-text">Watchlist</h1>
        <p className="mt-2 max-w-2xl text-sm text-text-muted">
          Companies you&apos;re tracking, with the current price, intrinsic
          value discount, and standing recommendation.
        </p>
      </header>

      {status === "ready" && !token ? (
        <p className="mt-10 rounded-md border border-border bg-surface px-4 py-3 text-sm text-text-muted">
          Please{" "}
          <Link href="/login" className="text-accent hover:opacity-90">
            log in
          </Link>{" "}
          to view your watchlist.
        </p>
      ) : null}

      {error ? (
        <p className="mt-6 rounded-md border border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative">
          {error}
        </p>
      ) : null}

      {loading && items === null ? (
        <p className="mt-8 text-sm text-text-muted">Loading watchlist…</p>
      ) : null}

      {items !== null && items.length === 0 ? (
        <p className="mt-10 text-sm text-text-muted">
          Your watchlist is empty. Open a company page and choose{" "}
          <span className="text-text">Add to watchlist</span>.
        </p>
      ) : null}

      {items !== null && items.length > 0 ? (
        <div className="mt-8 overflow-x-auto">
          <table className="w-full min-w-[640px] text-sm">
            <thead>
              <tr className="border-b border-border text-left text-xs text-text-muted">
                <th className="py-2 pr-4 font-medium">Symbol</th>
                <th className="py-2 pr-4 font-medium">Sector</th>
                <th className="py-2 pr-4 text-right font-medium">Price</th>
                <th className="py-2 pr-4 text-right font-medium">Intrinsic</th>
                <th className="py-2 pr-4 text-right font-medium">Discount</th>
                <th className="py-2 pr-4 font-medium">Call</th>
                <th className="py-2 font-medium" aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {items.map((item) => (
                <tr key={item.symbol} className="border-b border-border/60">
                  <td className="py-3 pr-4">
                    <Link
                      href={`/companies/${item.symbol}`}
                      className="font-mono font-semibold text-accent transition-colors hover:opacity-90"
                    >
                      {item.symbol}
                    </Link>
                    {item.name ? (
                      <div className="text-xs text-text-muted">{item.name}</div>
                    ) : null}
                  </td>
                  <td className="py-3 pr-4 text-text-muted">
                    {item.sector ?? "—"}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-text">
                    {formatPrice(item.current_price)}
                  </td>
                  <td className="py-3 pr-4 text-right tabular-nums text-text">
                    {formatPrice(item.intrinsic_value)}
                  </td>
                  <td
                    className={`py-3 pr-4 text-right tabular-nums ${discountTone(item.discount)}`}
                  >
                    {signedPercent(item.discount)}
                  </td>
                  <td className="py-3 pr-4">
                    {item.recommendation ? (
                      <span
                        className={`rounded-full border px-2 py-0.5 text-xs font-semibold ${RECOMMENDATION_STYLES[item.recommendation]}`}
                      >
                        {item.recommendation}
                      </span>
                    ) : (
                      <span className="text-text-muted">—</span>
                    )}
                  </td>
                  <td className="py-3 text-right">
                    <button
                      type="button"
                      onClick={() => remove(item.symbol)}
                      className="text-xs text-text-muted transition-colors hover:text-negative"
                      aria-label={`Remove ${item.symbol}`}
                    >
                      Remove
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : null}
    </main>
  );
}
