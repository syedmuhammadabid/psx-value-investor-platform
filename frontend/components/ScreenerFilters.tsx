"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

/** Filter fields mirrored to URL query params (kept in sync with the API). */
const NUMERIC_FIELDS = [
  { name: "min_roe", label: "Min ROE %", placeholder: "20" },
  { name: "min_roic", label: "Min ROIC %", placeholder: "15" },
  { name: "max_pe", label: "Max P/E", placeholder: "10" },
  {
    name: "min_dividend_yield",
    label: "Min Dividend Yield %",
    placeholder: "8",
  },
  {
    name: "max_debt_to_equity",
    label: "Max Debt / Equity",
    placeholder: "0.5",
  },
  {
    name: "min_revenue_growth",
    label: "Min Revenue Growth %",
    placeholder: "10",
  },
] as const;

type NumericField = (typeof NUMERIC_FIELDS)[number]["name"];

export interface ScreenerFilterValues {
  min_roe?: string;
  min_roic?: string;
  max_pe?: string;
  min_dividend_yield?: string;
  max_debt_to_equity?: string;
  min_revenue_growth?: string;
  positive_fcf?: string;
  sector?: string;
}

/** A one-click "quality value" preset matching the roadmap example. */
const QUALITY_PRESET: Record<string, string> = {
  min_roe: "20",
  min_roic: "15",
  max_pe: "10",
  max_debt_to_equity: "0.5",
  min_revenue_growth: "10",
  positive_fcf: "true",
};

export function ScreenerFilters({
  initial,
}: {
  initial: ScreenerFilterValues;
}) {
  const router = useRouter();
  const [numbers, setNumbers] = useState<Record<NumericField, string>>(() => ({
    min_roe: initial.min_roe ?? "",
    min_roic: initial.min_roic ?? "",
    max_pe: initial.max_pe ?? "",
    min_dividend_yield: initial.min_dividend_yield ?? "",
    max_debt_to_equity: initial.max_debt_to_equity ?? "",
    min_revenue_growth: initial.min_revenue_growth ?? "",
  }));
  const [positiveFcf, setPositiveFcf] = useState(
    initial.positive_fcf === "true"
  );
  const [sector, setSector] = useState(initial.sector ?? "");

  function apply(overrides?: Record<string, string>) {
    const params = new URLSearchParams();
    const source = overrides ?? {
      ...numbers,
      positive_fcf: positiveFcf ? "true" : "",
      sector,
    };
    for (const [key, value] of Object.entries(source)) {
      const trimmed = value.trim();
      if (trimmed && trimmed !== "false") params.set(key, trimmed);
    }
    const query = params.toString();
    router.push(query ? `/screener?${query}` : "/screener", { scroll: false });
  }

  function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    apply();
  }

  function clearAll() {
    setNumbers({
      min_roe: "",
      min_roic: "",
      max_pe: "",
      min_dividend_yield: "",
      max_debt_to_equity: "",
      min_revenue_growth: "",
    });
    setPositiveFcf(false);
    setSector("");
    router.push("/screener", { scroll: false });
  }

  return (
    <form
      onSubmit={onSubmit}
      className="rounded-lg border border-border bg-surface p-5"
    >
      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {NUMERIC_FIELDS.map((field) => (
          <div key={field.name}>
            <label
              htmlFor={field.name}
              className="block text-xs font-medium text-text-muted"
            >
              {field.label}
            </label>
            <input
              id={field.name}
              name={field.name}
              type="number"
              inputMode="decimal"
              step="any"
              value={numbers[field.name]}
              placeholder={field.placeholder}
              onChange={(event) =>
                setNumbers((prev) => ({
                  ...prev,
                  [field.name]: event.target.value,
                }))
              }
              className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm tabular-nums text-text placeholder:text-text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
            />
          </div>
        ))}

        <div>
          <label
            htmlFor="sector"
            className="block text-xs font-medium text-text-muted"
          >
            Sector
          </label>
          <input
            id="sector"
            name="sector"
            type="text"
            value={sector}
            placeholder="e.g. Energy"
            onChange={(event) => setSector(event.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text placeholder:text-text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          />
        </div>
      </div>

      <div className="mt-4 flex flex-wrap items-center gap-4">
        <label className="flex items-center gap-2 text-sm text-text">
          <input
            type="checkbox"
            checked={positiveFcf}
            onChange={(event) => setPositiveFcf(event.target.checked)}
            className="h-4 w-4 rounded border-border bg-surface-2 accent-accent"
          />
          Positive free cash flow
        </label>

        <div className="ml-auto flex flex-wrap gap-2">
          <button
            type="button"
            onClick={() => apply(QUALITY_PRESET)}
            className="rounded-md border border-border px-3 py-2 text-sm text-text-muted transition-colors hover:text-text"
          >
            Quality value preset
          </button>
          <button
            type="button"
            onClick={clearAll}
            className="rounded-md border border-border px-3 py-2 text-sm text-text-muted transition-colors hover:text-text"
          >
            Clear
          </button>
          <button
            type="submit"
            className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:opacity-90"
          >
            Apply filters
          </button>
        </div>
      </div>
    </form>
  );
}
