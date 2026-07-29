"use client";

import { useState } from "react";

import { ApiError, askAssistant } from "@/lib/api";
import type { AssistantAnswer, Recommendation } from "@/lib/types";

const SUGGESTIONS = [
  "Should I buy this stock?",
  "Is it undervalued?",
  "How fast is it growing?",
  "How much debt does it carry?",
  "What is the dividend?",
] as const;

const RECOMMENDATION_STYLES: Record<Recommendation, string> = {
  BUY: "border-positive/40 bg-positive/10 text-positive",
  HOLD: "border-warning/40 bg-warning/10 text-warning",
  SELL: "border-negative/40 bg-negative/10 text-negative",
};

export function AssistantView({ symbol }: { symbol: string }) {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<AssistantAnswer | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function ask(raw: string) {
    const trimmed = raw.trim();
    if (!trimmed || loading) return;

    setLoading(true);
    setError(null);
    try {
      const result = await askAssistant(symbol, trimmed);
      setAnswer(result);
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.message
          : "Something went wrong. Please try again.";
      setError(message);
      setAnswer(null);
    } finally {
      setLoading(false);
    }
  }

  return (
    <section id="assistant" className="mt-14 scroll-mt-6">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <h2 className="text-lg font-semibold text-text">AI assistant</h2>
        <span className="text-sm text-text-muted">
          Ask about {symbol} in plain language
        </span>
      </div>

      <form
        className="mt-6 flex flex-col gap-3 sm:flex-row"
        onSubmit={(event) => {
          event.preventDefault();
          void ask(question);
        }}
      >
        <input
          type="text"
          value={question}
          onChange={(event) => setQuestion(event.target.value)}
          placeholder={`Should I buy ${symbol}?`}
          aria-label={`Ask a question about ${symbol}`}
          maxLength={500}
          className="flex-1 rounded-lg border border-border bg-surface px-4 py-2.5 text-sm text-text placeholder:text-text-muted focus:border-accent focus:outline-none"
        />
        <button
          type="submit"
          disabled={loading || question.trim().length === 0}
          className="rounded-lg border border-accent bg-accent/10 px-5 py-2.5 text-sm font-medium text-accent transition-colors hover:bg-accent/20 disabled:cursor-not-allowed disabled:opacity-50"
        >
          {loading ? "Thinking…" : "Ask"}
        </button>
      </form>

      <div className="mt-3 flex flex-wrap gap-2">
        {SUGGESTIONS.map((suggestion) => (
          <button
            key={suggestion}
            type="button"
            disabled={loading}
            onClick={() => {
              setQuestion(suggestion);
              void ask(suggestion);
            }}
            className="rounded-full border border-border bg-surface-2 px-3 py-1 text-xs text-text-muted transition-colors hover:border-accent hover:text-text disabled:cursor-not-allowed disabled:opacity-50"
          >
            {suggestion}
          </button>
        ))}
      </div>

      {error ? (
        <p className="mt-6 rounded-lg border border-negative/40 bg-negative/10 px-4 py-3 text-sm text-negative">
          {error}
        </p>
      ) : null}

      {answer ? (
        <article className="mt-6 rounded-lg border border-border bg-surface p-5">
          <div className="flex items-start justify-between gap-4">
            <p className="text-xs uppercase tracking-wide text-text-muted">
              {answer.question}
            </p>
            <span
              className={`shrink-0 rounded-full border px-2.5 py-0.5 text-xs font-medium ${RECOMMENDATION_STYLES[answer.recommendation]}`}
            >
              {answer.recommendation}
            </span>
          </div>

          <p className="mt-3 text-sm leading-relaxed text-text">
            {answer.answer}
          </p>

          {answer.highlights.length > 0 ? (
            <ul className="mt-4 grid gap-2 sm:grid-cols-2">
              {answer.highlights.map((highlight) => (
                <li
                  key={highlight}
                  className="rounded-md border border-border bg-surface-2 px-3 py-2 text-xs tabular-nums text-text-muted"
                >
                  {highlight}
                </li>
              ))}
            </ul>
          ) : null}

          <p className="mt-4 text-xs text-text-muted">{answer.disclaimer}</p>
        </article>
      ) : null}
    </section>
  );
}
