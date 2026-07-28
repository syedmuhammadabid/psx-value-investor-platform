"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";

/**
 * URL-driven search box. Updates the `q` query parameter (debounced) so the
 * server component can re-fetch and render results — no client data store
 * required for the explorer.
 */
export function SearchBar({ initialQuery = "" }: { initialQuery?: string }) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [value, setValue] = useState(initialQuery);

  useEffect(() => {
    const handle = setTimeout(() => {
      const params = new URLSearchParams(searchParams.toString());
      const trimmed = value.trim();
      if (trimmed) {
        params.set("q", trimmed);
      } else {
        params.delete("q");
      }
      const query = params.toString();
      router.replace(query ? `/companies?${query}` : "/companies", {
        scroll: false,
      });
    }, 300);

    return () => clearTimeout(handle);
    // Intentionally excludes router/searchParams to only react to input.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [value]);

  return (
    <div className="relative">
      <label htmlFor="company-search" className="sr-only">
        Search companies by symbol or name
      </label>
      <input
        id="company-search"
        type="search"
        value={value}
        onChange={(event) => setValue(event.target.value)}
        placeholder="Search by symbol or name (e.g. MARI, Systems)…"
        autoComplete="off"
        className="w-full rounded-md border border-border bg-surface px-4 py-3 text-sm text-text placeholder:text-text-muted focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      />
    </div>
  );
}
