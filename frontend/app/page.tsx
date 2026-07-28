import Link from "next/link";

const HIGHLIGHTS = [
  {
    label: "Intrinsic value",
    description:
      "A weighted blend of DCF, Graham, historical & industry P/E, EV/EBITDA, residual income and DDM — never a single model.",
  },
  {
    label: "Buy & sell zones",
    description:
      "Clear Strong Buy to Strong Sell price bands so you know exactly when to act.",
  },
  {
    label: "Explainable calls",
    description:
      "Every recommendation shows its reasons, assumptions, and data sources. No black boxes.",
  },
];

export default function Home() {
  return (
    <main className="mx-auto flex w-full max-w-5xl flex-1 flex-col px-6 py-16 sm:py-24">
      <span className="text-sm font-medium tracking-wide text-accent">
        Pakistan Stock Exchange &middot; Fundamental analysis
      </span>

      <h1 className="mt-4 max-w-3xl text-4xl font-semibold leading-tight text-text sm:text-6xl">
        What is this company <span className="text-accent">actually worth</span>
        , and should you buy it today?
      </h1>

      <p className="mt-6 max-w-2xl text-lg text-text-muted">
        PSX Value Investor goes beyond stock prices. It calculates intrinsic
        value, defines buy and sell zones, and explains every recommendation —
        so long-term investors can decide with confidence.
      </p>

      <div className="mt-10 flex flex-wrap items-center gap-4">
        <Link
          href="/companies"
          className="rounded-md bg-accent px-5 py-3 text-sm font-semibold text-white transition-colors hover:opacity-90"
        >
          Explore companies
        </Link>
        <Link
          href="/screener"
          className="rounded-md border border-border px-5 py-3 text-sm font-semibold text-text transition-colors hover:bg-surface-2"
        >
          Stock screener
        </Link>
      </div>

      <section
        aria-label="Platform highlights"
        className="mt-20 grid gap-4 sm:grid-cols-3"
      >
        {HIGHLIGHTS.map((item) => (
          <article
            key={item.label}
            className="rounded-lg border border-border bg-surface p-6"
          >
            <h2 className="text-base font-semibold text-text">{item.label}</h2>
            <p className="mt-2 text-sm text-text-muted">{item.description}</p>
          </article>
        ))}
      </section>

      <footer className="mt-24 border-t border-border pt-6 text-xs text-text-muted">
        For informational and educational purposes only. Not financial advice.
      </footer>
    </main>
  );
}
