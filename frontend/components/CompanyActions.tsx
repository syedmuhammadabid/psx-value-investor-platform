"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";

import {
  addToWatchlist,
  getAlertSubscriptions,
  getWatchlist,
  removeFromWatchlist,
  subscribeToAlerts,
  unsubscribeFromAlerts,
  useAuth,
} from "@/lib/auth";

export function CompanyActions({ symbol }: { symbol: string }) {
  const { token, status } = useAuth();
  const [watching, setWatching] = useState(false);
  const [subscribed, setSubscribed] = useState(false);
  const [busy, setBusy] = useState<"watch" | "alert" | null>(null);

  useEffect(() => {
    if (status !== "ready") return;
    let cancelled = false;
    const run = async () => {
      if (!token) {
        setWatching(false);
        setSubscribed(false);
        return;
      }
      try {
        const [watchlist, subscriptions] = await Promise.all([
          getWatchlist(),
          getAlertSubscriptions(),
        ]);
        if (cancelled) return;
        setWatching(watchlist.some((item) => item.symbol === symbol));
        setSubscribed(subscriptions.some((sub) => sub.symbol === symbol));
      } catch {
        // Leave defaults; the buttons still work optimistically.
      }
    };
    void run();
    return () => {
      cancelled = true;
    };
  }, [token, status, symbol]);

  const toggleWatch = useCallback(async () => {
    setBusy("watch");
    try {
      if (watching) {
        await removeFromWatchlist(symbol);
        setWatching(false);
      } else {
        await addToWatchlist(symbol);
        setWatching(true);
      }
    } catch {
      // Ignore; state is unchanged on failure.
    } finally {
      setBusy(null);
    }
  }, [watching, symbol]);

  const toggleAlerts = useCallback(async () => {
    setBusy("alert");
    try {
      if (subscribed) {
        await unsubscribeFromAlerts(symbol);
        setSubscribed(false);
      } else {
        await subscribeToAlerts(symbol);
        setSubscribed(true);
      }
    } catch {
      // Ignore; state is unchanged on failure.
    } finally {
      setBusy(null);
    }
  }, [subscribed, symbol]);

  if (status === "loading") {
    return null;
  }

  if (!token) {
    return (
      <p className="mt-4 text-xs text-text-muted">
        <Link href="/login" className="text-accent hover:opacity-90">
          Log in
        </Link>{" "}
        to add this company to your watchlist or subscribe to alerts.
      </p>
    );
  }

  return (
    <div className="mt-4 flex flex-wrap gap-2">
      <button
        type="button"
        onClick={toggleWatch}
        disabled={busy === "watch"}
        className={`rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors disabled:opacity-60 ${
          watching
            ? "border-accent/40 bg-accent/10 text-accent"
            : "border-border text-text-muted hover:text-text"
        }`}
      >
        {watching ? "✓ On watchlist" : "+ Add to watchlist"}
      </button>
      <button
        type="button"
        onClick={toggleAlerts}
        disabled={busy === "alert"}
        className={`rounded-md border px-3 py-1.5 text-xs font-semibold transition-colors disabled:opacity-60 ${
          subscribed
            ? "border-accent/40 bg-accent/10 text-accent"
            : "border-border text-text-muted hover:text-text"
        }`}
      >
        {subscribed ? "✓ Alerts on" : "🔔 Subscribe to alerts"}
      </button>
    </div>
  );
}
