import { formatPercent, formatPrice, formatRatio } from "@/lib/format";
import type { Recommendation, Valuation } from "@/lib/types";

const RECOMMENDATION_STYLES: Record<Recommendation, string> = {
  BUY: "border-positive/40 bg-positive/10 text-positive",
  HOLD: "border-warning/40 bg-warning/10 text-warning",
  SELL: "border-negative/40 bg-negative/10 text-negative",
};

const RECOMMENDATION_LABELS: Record<Recommendation, string> = {
  BUY: "Undervalued",
  HOLD: "Fairly valued",
  SELL: "Overvalued",
};

/** Format the discount to intrinsic value with an explicit sign. */
function formatDiscount(discount: number | null): string {
  if (discount == null) return "—";
  const sign = discount > 0 ? "+" : "";
  return `${sign}${discount.toFixed(1)}%`;
}

function discountTone(discount: number | null): string {
  if (discount == null) return "text-text";
  if (discount > 0) return "text-positive";
  if (discount < 0) return "text-negative";
  return "text-text";
}

function Metric({
  label,
  value,
  tone = "text-text",
}: {
  label: string;
  value: string;
  tone?: string;
}) {
  return (
    <div className="rounded-lg border border-border bg-surface-2 p-4">
      <div className="text-xs text-text-muted">{label}</div>
      <div className={`mt-1 text-xl font-semibold tabular-nums ${tone}`}>
        {value}
      </div>
    </div>
  );
}

export function ValuationView({ valuation }: { valuation: Valuation }) {
  const { intrinsic_value, current_price, discount, recommendation, models } =
    valuation;

  const hasEstimate = intrinsic_value != null;
  const appliedModels = models.filter((model) => model.applied);

  return (
    <section id="valuation" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Intrinsic value</h2>
        <span className="text-sm text-text-muted">
          Blended fair value estimate
        </span>
      </div>

      {!hasEstimate ? (
        <p className="mt-6 text-sm text-text-muted">
          An intrinsic value estimate will appear once annual financials are
          available for this company.
        </p>
      ) : (
        <div className="mt-6 rounded-lg border border-border bg-surface p-6">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-semibold tabular-nums text-text">
                {formatPrice(intrinsic_value)}
              </span>
              <span className="text-sm text-text-muted">per share</span>
            </div>
            <span
              className={`rounded-full border px-3 py-1 text-sm font-semibold ${RECOMMENDATION_STYLES[recommendation]}`}
            >
              {recommendation} · {RECOMMENDATION_LABELS[recommendation]}
            </span>
          </div>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <Metric
              label="Intrinsic value"
              value={formatPrice(intrinsic_value)}
            />
            <Metric label="Current price" value={formatPrice(current_price)} />
            <Metric
              label="Discount to fair value"
              value={formatDiscount(discount)}
              tone={discountTone(discount)}
            />
          </div>

          <div className="mt-8">
            <h3 className="text-sm font-semibold text-text-muted">
              Model breakdown
            </h3>
            <ul className="mt-3 divide-y divide-border">
              {models.map((model) => (
                <li
                  key={model.name}
                  className="flex items-baseline justify-between gap-4 py-2"
                >
                  <span className="text-sm text-text">
                    {model.name}
                    <span className="ml-2 text-xs text-text-muted">
                      {formatPercent(model.weight * 100)} weight
                    </span>
                  </span>
                  <span
                    className={`text-sm font-medium tabular-nums ${
                      model.applied ? "text-text" : "text-text-muted"
                    }`}
                  >
                    {model.applied ? formatPrice(model.value) : "n/a"}
                  </span>
                </li>
              ))}
            </ul>
            <p className="mt-3 text-xs text-text-muted">
              The intrinsic value is the weight-adjusted average of{" "}
              {appliedModels.length} applicable{" "}
              {appliedModels.length === 1 ? "model" : "models"}. Assumes a{" "}
              {formatRatio(valuation.assumptions.discount_rate * 100)}% discount
              rate and{" "}
              {formatRatio(valuation.assumptions.terminal_growth * 100)}%
              terminal growth.
            </p>
          </div>
        </div>
      )}
    </section>
  );
}
