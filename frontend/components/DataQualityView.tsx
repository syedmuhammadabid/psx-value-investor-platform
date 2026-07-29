import type { DataQualityReport, DataSourceInfo } from "@/lib/types";

/** Freshness badge tone based on how stale the newest statement is. */
function freshness(days: number | null): { label: string; tone: string } {
  if (days === null) {
    return { label: "No data", tone: "border-border text-text-muted" };
  }
  if (days <= 120) {
    return { label: "Fresh", tone: "border-positive/40 text-positive" };
  }
  if (days <= 400) {
    return { label: "Aging", tone: "border-warning/40 text-warning" };
  }
  return { label: "Stale", tone: "border-negative/40 text-negative" };
}

function formatDateTime(value: string | null): string {
  if (!value) return "—";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "—";
  return date.toLocaleDateString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
  });
}

function Stat({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-lg border border-border bg-surface-2 p-4">
      <p className="text-xs text-text-muted">{label}</p>
      <p className="mt-1 text-lg font-semibold tabular-nums text-text">
        {value}
      </p>
    </div>
  );
}

function SourceRow({ source }: { source: DataSourceInfo }) {
  const period =
    source.period_type === "annual"
      ? `FY${source.fiscal_year}`
      : `${source.fiscal_period} ${source.fiscal_year}`;

  return (
    <li className="flex flex-wrap items-center justify-between gap-2 border-b border-border py-2 text-xs last:border-b-0">
      <span className="font-medium tabular-nums text-text">{period}</span>
      <span className="text-text-muted">
        {source.source_url ? (
          <a
            href={source.source_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-accent hover:underline"
          >
            {source.source_type}
            {source.source_page ? ` · p.${source.source_page}` : ""}
          </a>
        ) : (
          <span>{source.source_type}</span>
        )}
      </span>
      <span className="tabular-nums text-text-muted">
        {formatDateTime(source.extracted_at)}
      </span>
      <span
        className="font-mono text-text-muted"
        title={`Content checksum: ${source.checksum}`}
      >
        {source.checksum.slice(0, 8)}
      </span>
    </li>
  );
}

export function DataQualityView({ report }: { report: DataQualityReport }) {
  const badge = freshness(report.staleness_days);
  const staleness =
    report.staleness_days === null
      ? "—"
      : `${report.staleness_days} day${report.staleness_days === 1 ? "" : "s"} ago`;

  return (
    <section id="data-quality" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">Data Quality</h2>
        <span
          className={`rounded-full border px-2.5 py-0.5 text-xs font-medium ${badge.tone}`}
        >
          {badge.label}
        </span>
      </div>

      <div className="mt-6 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        <Stat
          label="Last updated"
          value={formatDateTime(report.last_updated)}
        />
        <Stat label="Staleness" value={staleness} />
        <Stat label="Annual periods" value={String(report.annual_periods)} />
        <Stat
          label="Quarterly periods"
          value={String(report.quarterly_periods)}
        />
      </div>

      {report.sources.length > 0 ? (
        <div className="mt-6 rounded-lg border border-border bg-surface p-4">
          <h3 className="text-sm font-medium text-text">Provenance</h3>
          <ul className="mt-2">
            {report.sources.map((source) => (
              <SourceRow
                key={source.checksum + source.fiscal_year}
                source={source}
              />
            ))}
          </ul>
        </div>
      ) : (
        <p className="mt-6 text-sm text-text-muted">
          No ingestion provenance is recorded for this company yet.
        </p>
      )}

      <p className="mt-4 text-xs text-text-muted">
        Every figure is traced to its source filing with a content checksum, so
        you can verify the numbers behind every analysis on this page.
      </p>
    </section>
  );
}
