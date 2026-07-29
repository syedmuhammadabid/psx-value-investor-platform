import type {
  AltmanScore,
  CompanyScores,
  CompositeScore,
  MagicFormula,
  PiotroskiScore,
  ScoreCheck,
  ScoreRating,
} from "@/lib/types";
import { formatPercent } from "@/lib/format";

/** Accent colours for each composite rating band. */
const RATING_STYLES: Record<
  ScoreRating,
  { text: string; border: string; label: string }
> = {
  excellent: {
    text: "text-positive",
    border: "border-positive/40",
    label: "Excellent",
  },
  good: { text: "text-positive", border: "border-positive/30", label: "Good" },
  fair: { text: "text-warning", border: "border-warning/40", label: "Fair" },
  weak: { text: "text-negative", border: "border-negative/40", label: "Weak" },
  na: { text: "text-text-muted", border: "border-border", label: "No data" },
};

/** Accent colours for the Altman distress band. */
const BAND_STYLES: Record<
  string,
  { text: string; border: string; label: string }
> = {
  safe: { text: "text-positive", border: "border-positive/40", label: "Safe" },
  grey: {
    text: "text-warning",
    border: "border-warning/40",
    label: "Grey zone",
  },
  distress: {
    text: "text-negative",
    border: "border-negative/40",
    label: "Distress",
  },
  na: { text: "text-text-muted", border: "border-border", label: "No data" },
};

function CheckRow({ check }: { check: ScoreCheck }) {
  const glyph = check.passed === null ? "•" : check.passed ? "✓" : "✕";
  const tone =
    check.passed === null
      ? "text-text-muted"
      : check.passed
        ? "text-positive"
        : "text-negative";

  return (
    <li className="flex items-start gap-2 text-xs">
      <span className={`mt-px ${tone}`} aria-hidden>
        {glyph}
      </span>
      <span className="text-text-muted">
        <span className="text-text">{check.label}</span> — {check.detail}
      </span>
    </li>
  );
}

function CompositeCard({ score }: { score: CompositeScore }) {
  const style = RATING_STYLES[score.rating];

  return (
    <div className={`rounded-lg border bg-surface-2 p-4 ${style.border}`}>
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-text">{score.label}</h3>
        <span className={`text-xs font-medium ${style.text}`}>
          {style.label}
        </span>
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className={`text-2xl font-semibold tabular-nums ${style.text}`}>
          {score.value === null ? "—" : Math.round(score.value)}
        </span>
        <span className="text-xs text-text-muted">/ 100</span>
      </div>
      <ul className="mt-3 space-y-1.5">
        {score.checks.map((check) => (
          <CheckRow key={check.label} check={check} />
        ))}
      </ul>
    </div>
  );
}

function PiotroskiCard({ score }: { score: PiotroskiScore }) {
  const tone =
    score.rating === "strong"
      ? "text-positive"
      : score.rating === "moderate"
        ? "text-warning"
        : "text-text-muted";

  return (
    <div className="rounded-lg border border-border bg-surface-2 p-4">
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-text">Piotroski F-Score</h3>
        <span className={`text-xs font-medium capitalize ${tone}`}>
          {score.rating === "na" ? "No data" : score.rating}
        </span>
      </div>
      <div className="mt-2 flex items-baseline gap-1">
        <span className={`text-2xl font-semibold tabular-nums ${tone}`}>
          {score.value === null ? "—" : score.value}
        </span>
        <span className="text-xs text-text-muted">/ {score.max_score}</span>
      </div>
      {score.checks.length > 0 ? (
        <ul className="mt-3 space-y-1.5">
          {score.checks.map((check) => (
            <CheckRow key={check.label} check={check} />
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-xs text-text-muted">
          Needs two years of financials to compute.
        </p>
      )}
    </div>
  );
}

function AltmanCard({ score }: { score: AltmanScore }) {
  const style = BAND_STYLES[score.band] ?? BAND_STYLES.na;

  return (
    <div className={`rounded-lg border bg-surface-2 p-4 ${style.border}`}>
      <div className="flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-text">Altman Z-Score</h3>
        <span className={`text-xs font-medium ${style.text}`}>
          {style.label}
        </span>
      </div>
      <div className="mt-2">
        <span className={`text-2xl font-semibold tabular-nums ${style.text}`}>
          {score.value === null ? "—" : score.value.toFixed(2)}
        </span>
      </div>
      <p className="mt-3 text-xs text-text-muted">{score.detail}</p>
    </div>
  );
}

function MagicCard({ score }: { score: MagicFormula }) {
  return (
    <div className="rounded-lg border border-border bg-surface-2 p-4">
      <h3 className="text-sm font-medium text-text">Magic Formula</h3>
      <dl className="mt-2 grid grid-cols-2 gap-3">
        <div>
          <dt className="text-xs text-text-muted">Return on capital</dt>
          <dd className="text-lg font-semibold tabular-nums text-text">
            {score.roic === null ? "—" : formatPercent(score.roic)}
          </dd>
        </div>
        <div>
          <dt className="text-xs text-text-muted">Earnings yield</dt>
          <dd className="text-lg font-semibold tabular-nums text-text">
            {score.earnings_yield === null
              ? "—"
              : formatPercent(score.earnings_yield)}
          </dd>
        </div>
      </dl>
      <p className="mt-3 text-xs text-text-muted">{score.detail}</p>
    </div>
  );
}

export function ScoresView({ scores }: { scores: CompanyScores }) {
  return (
    <section id="scores" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Investment Scores</h2>
        <span className="text-sm text-text-muted">
          Rules-based scorecards from the reported financials
        </span>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2">
        {scores.composites.map((score) => (
          <CompositeCard key={score.key} score={score} />
        ))}
      </div>

      <div className="mt-3 grid gap-3 sm:grid-cols-2">
        <PiotroskiCard score={scores.piotroski} />
        <div className="grid gap-3">
          <AltmanCard score={scores.altman_z} />
          <MagicCard score={scores.magic_formula} />
        </div>
      </div>

      <p className="mt-4 text-xs text-text-muted">
        Scores are computed mechanically from the latest reported financials —
        for informational purposes only, not financial advice.
      </p>
    </section>
  );
}
