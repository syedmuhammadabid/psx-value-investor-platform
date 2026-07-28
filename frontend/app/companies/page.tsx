import Link from "next/link";
import { Suspense } from "react";

import { CompanyCard } from "@/components/CompanyCard";
import { SearchBar } from "@/components/SearchBar";
import { ApiError, listCompanies } from "@/lib/api";
import type { CompanySummary } from "@/lib/types";

export const metadata = {
  title: "Companies · PSX Value Investor",
  description:
    "Browse and search Pakistan Stock Exchange companies by symbol, name, and sector.",
};

interface CompaniesPageProps {
  searchParams: Promise<{ q?: string; sector?: string }>;
}

export default async function CompaniesPage({
  searchParams,
}: CompaniesPageProps) {
  const { q, sector } = await searchParams;

  let companies: CompanySummary[] = [];
  let total = 0;
  let errorMessage: string | null = null;

  try {
    const page = await listCompanies({ q, sector, limit: 48 });
    companies = page.items;
    total = page.total;
  } catch (error) {
    errorMessage =
      error instanceof ApiError
        ? error.message
        : "Something went wrong loading companies.";
  }

  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-12">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-semibold text-text">Companies</h1>
          <p className="mt-1 text-sm text-text-muted">
            Explore Pakistan Stock Exchange listings.
          </p>
        </div>
        <Link
          href="/"
          className="text-sm text-text-muted transition-colors hover:text-text"
        >
          ← Home
        </Link>
      </div>

      <div className="mt-4">
        <Link
          href="/screener"
          className="text-sm text-accent transition-colors hover:underline"
        >
          Open the stock screener →
        </Link>
      </div>

      <div className="mt-6">
        <Suspense fallback={null}>
          <SearchBar initialQuery={q ?? ""} />
        </Suspense>
      </div>

      {errorMessage ? (
        <p
          role="alert"
          className="mt-10 rounded-md border border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative"
        >
          {errorMessage}
        </p>
      ) : companies.length === 0 ? (
        <p className="mt-10 text-sm text-text-muted">
          {q
            ? `No companies match “${q}”.`
            : "No companies available yet. Run the seed script to load data."}
        </p>
      ) : (
        <>
          <p className="mt-6 text-xs text-text-muted">
            {total} {total === 1 ? "company" : "companies"}
            {q ? ` matching “${q}”` : ""}
          </p>
          <section
            aria-label="Company results"
            className="mt-4 grid gap-4 sm:grid-cols-2 lg:grid-cols-3"
          >
            {companies.map((company) => (
              <CompanyCard key={company.symbol} company={company} />
            ))}
          </section>
        </>
      )}
    </main>
  );
}
