"use client";

import {
  AreaSeries,
  createChart,
  type AreaData,
  type IChartApi,
  type Time,
} from "lightweight-charts";
import { useEffect, useMemo, useRef, useState } from "react";

import { compact } from "@/lib/format";
import type { CompanyHistory, MetricPoint } from "@/lib/types";

type MetricKey = Exclude<keyof MetricPoint, "fiscal_year" | "period_end">;

type MetricKind = "money" | "percent" | "perShare";

interface MetricConfig {
  key: MetricKey;
  label: string;
  kind: MetricKind;
}

/** Metrics charted over time, per PROJECT_ROADMAP.md Phase 6. */
const METRICS: MetricConfig[] = [
  { key: "revenue", label: "Revenue", kind: "money" },
  { key: "net_income", label: "Net Profit", kind: "money" },
  { key: "free_cash_flow", label: "Free Cash Flow", kind: "money" },
  { key: "eps", label: "EPS", kind: "perShare" },
  {
    key: "book_value_per_share",
    label: "Book Value / Share",
    kind: "perShare",
  },
  { key: "dividend_per_share", label: "Dividend / Share", kind: "perShare" },
  { key: "roe", label: "ROE", kind: "percent" },
  { key: "roic", label: "ROIC", kind: "percent" },
];

// Theme tokens (kept in sync with globals.css design variables).
const COLORS = {
  accent: "#3b82f6",
  border: "#26262a",
  textMuted: "#a1a1aa",
};

function formatValue(value: number, kind: MetricKind): string {
  if (kind === "percent") return `${value.toFixed(1)}%`;
  if (kind === "perShare") return `Rs ${value.toFixed(2)}`;
  return `Rs ${compact(value)}`;
}

export function FinancialCharts({ history }: { history: CompanyHistory }) {
  const [metricKey, setMetricKey] = useState<MetricKey>("revenue");
  const containerRef = useRef<HTMLDivElement>(null);
  const chartRef = useRef<IChartApi | null>(null);

  const metric = useMemo(
    () => METRICS.find((m) => m.key === metricKey) ?? METRICS[0],
    [metricKey]
  );

  const data = useMemo<AreaData<Time>[]>(
    () =>
      history.points
        .map((p) => ({ time: p.period_end as Time, value: p[metric.key] }))
        .filter((d): d is AreaData<Time> => d.value != null),
    [history.points, metric.key]
  );

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const chart = createChart(container, {
      autoSize: true,
      layout: {
        background: { color: "transparent" },
        textColor: COLORS.textMuted,
        attributionLogo: false,
      },
      grid: {
        vertLines: { color: COLORS.border },
        horzLines: { color: COLORS.border },
      },
      rightPriceScale: { borderColor: COLORS.border },
      timeScale: {
        borderColor: COLORS.border,
        fixLeftEdge: true,
        fixRightEdge: true,
      },
      crosshair: { horzLine: { labelVisible: false } },
      localization: {
        priceFormatter: (value: number) => formatValue(value, metric.kind),
      },
      handleScroll: false,
      handleScale: false,
    });
    chartRef.current = chart;

    const series = chart.addSeries(AreaSeries, {
      lineColor: COLORS.accent,
      topColor: "rgba(59, 130, 246, 0.35)",
      bottomColor: "rgba(59, 130, 246, 0.02)",
      lineWidth: 2,
      priceLineVisible: false,
    });
    series.setData(data);
    chart.timeScale().fitContent();

    return () => {
      chart.remove();
      chartRef.current = null;
    };
  }, [data, metric.kind]);

  return (
    <section id="charts" className="mt-14 scroll-mt-6">
      <h2 className="text-lg font-semibold text-text">Trends</h2>
      <p className="mt-1 text-sm text-text-muted">
        Annual history of key value-investing metrics.
      </p>

      <div className="mt-4 flex flex-wrap gap-2">
        {METRICS.map((m) => {
          const active = m.key === metricKey;
          return (
            <button
              key={m.key}
              type="button"
              onClick={() => setMetricKey(m.key)}
              aria-pressed={active}
              className={
                active
                  ? "rounded-md border border-accent bg-accent/10 px-3 py-1.5 text-sm font-medium text-accent"
                  : "rounded-md border border-border bg-surface px-3 py-1.5 text-sm text-text-muted transition-colors hover:text-text"
              }
            >
              {m.label}
            </button>
          );
        })}
      </div>

      <div className="mt-4 rounded-lg border border-border bg-surface p-4">
        {data.length > 0 ? (
          <div ref={containerRef} className="h-80 w-full" />
        ) : (
          <p className="flex h-80 items-center justify-center text-sm text-text-muted">
            No data available for {metric.label}.
          </p>
        )}
      </div>
    </section>
  );
}
