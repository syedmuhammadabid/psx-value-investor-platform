import type { AlertReport, AlertSentiment, AlertSignal } from "@/lib/types";

/** Per-sentiment accent and glyph for an alert row. */
const SENTIMENT_STYLES: Record<
  AlertSentiment,
  { border: string; text: string; glyph: string }
> = {
  positive: {
    border: "border-positive/40",
    text: "text-positive",
    glyph: "▲",
  },
  negative: {
    border: "border-negative/40",
    text: "text-negative",
    glyph: "▼",
  },
  neutral: {
    border: "border-border",
    text: "text-text-muted",
    glyph: "•",
  },
};

function AlertRow({ alert }: { alert: AlertSignal }) {
  const style = SENTIMENT_STYLES[alert.sentiment];

  return (
    <li
      className={`flex items-start gap-3 rounded-lg border bg-surface-2 px-4 py-3 ${style.border}`}
    >
      <span className={`mt-0.5 text-xs ${style.text}`} aria-hidden>
        {style.glyph}
      </span>
      <div>
        <div className={`text-sm font-medium ${style.text}`}>{alert.title}</div>
        <div className="text-xs text-text-muted">{alert.detail}</div>
      </div>
    </li>
  );
}

export function AlertsView({ report }: { report: AlertReport }) {
  const { alerts } = report;
  const hasAlerts = alerts.length > 0;

  return (
    <section id="alerts" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Alerts</h2>
        <span className="text-sm text-text-muted">
          Conditions worth watching now
        </span>
      </div>

      {hasAlerts ? (
        <ul className="mt-6 grid gap-2 sm:grid-cols-2">
          {alerts.map((alert) => (
            <AlertRow key={alert.type} alert={alert} />
          ))}
        </ul>
      ) : (
        <p className="mt-6 text-sm text-text-muted">
          No active alerts. Nothing noteworthy has changed in the latest
          reported figures.
        </p>
      )}

      <p className="mt-4 text-xs text-text-muted">
        Signals are derived from the latest reported financials and our
        valuation models — for informational purposes only, not financial
        advice.
      </p>
    </section>
  );
}
