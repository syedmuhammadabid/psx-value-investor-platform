import type {
  Recommendation,
  RecommendationReason,
  RecommendationReport,
  Sentiment,
} from "@/lib/types";

const RECOMMENDATION_STYLES: Record<Recommendation, string> = {
  BUY: "border-positive/40 bg-positive/10 text-positive",
  HOLD: "border-warning/40 bg-warning/10 text-warning",
  SELL: "border-negative/40 bg-negative/10 text-negative",
};

/** Per-sentiment accent and glyph for a reason row. */
const SENTIMENT_STYLES: Record<Sentiment, { text: string; glyph: string }> = {
  positive: { text: "text-positive", glyph: "▲" },
  negative: { text: "text-negative", glyph: "▼" },
  neutral: { text: "text-text-muted", glyph: "•" },
};

function ReasonRow({ reason }: { reason: RecommendationReason }) {
  const style = SENTIMENT_STYLES[reason.sentiment];

  return (
    <li className="flex items-start gap-3 rounded-lg border border-border bg-surface-2 px-4 py-3">
      <span className={`mt-0.5 text-xs ${style.text}`} aria-hidden>
        {style.glyph}
      </span>
      <div>
        <div className="text-sm font-medium text-text">{reason.detail}</div>
        <div className="text-xs text-text-muted">{reason.label}</div>
      </div>
    </li>
  );
}

export function RecommendationView({
  recommendation,
}: {
  recommendation: RecommendationReport;
}) {
  const { recommendation: call, summary, reasons } = recommendation;
  const hasReasons = reasons.length > 0;

  return (
    <section id="recommendation" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Recommendation</h2>
        <span className="text-sm text-text-muted">Why we reach this call</span>
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-4">
        <span
          className={`rounded-full border px-3 py-1 text-sm font-semibold ${RECOMMENDATION_STYLES[call]}`}
        >
          {call}
        </span>
        <p className="text-sm text-text-muted">{summary}</p>
      </div>

      {hasReasons ? (
        <ul className="mt-6 grid gap-2 sm:grid-cols-2">
          {reasons.map((reason) => (
            <ReasonRow key={reason.label} reason={reason} />
          ))}
        </ul>
      ) : (
        <p className="mt-6 text-sm text-text-muted">
          Detailed reasons will appear once financials are available to assess
          this company.
        </p>
      )}

      <p className="mt-4 text-xs text-text-muted">
        For informational purposes only — not financial advice. Every factor is
        derived from reported financials and our valuation models.
      </p>
    </section>
  );
}
