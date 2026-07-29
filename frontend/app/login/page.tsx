"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const { login, user, status } = useAuth();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (status === "ready" && user) {
      router.replace("/");
    }
  }, [status, user, router]);

  const onSubmit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email.trim(), password);
      router.push("/");
    } catch (err: unknown) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Unable to log in. Please try again."
      );
      setSubmitting(false);
    }
  };

  return (
    <main className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-16">
      <h1 className="text-2xl font-semibold text-text">Welcome back</h1>
      <p className="mt-2 text-sm text-text-muted">
        Log in to access your watchlist, portfolio, and alerts.
      </p>

      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <div>
          <label
            htmlFor="email"
            className="block text-xs font-medium text-text-muted"
          >
            Email
          </label>
          <input
            id="email"
            type="email"
            autoComplete="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>
        <div>
          <label
            htmlFor="password"
            className="block text-xs font-medium text-text-muted"
          >
            Password
          </label>
          <input
            id="password"
            type="password"
            autoComplete="current-password"
            required
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="mt-1 w-full rounded-md border border-border bg-surface-2 px-3 py-2 text-sm text-text outline-none focus:border-accent"
          />
        </div>

        {error ? (
          <p className="rounded-md border border-negative/40 bg-negative/10 px-3 py-2 text-sm text-negative">
            {error}
          </p>
        ) : null}

        <button
          type="submit"
          disabled={submitting}
          className="rounded-md bg-accent px-4 py-2 text-sm font-semibold text-white transition-colors hover:opacity-90 disabled:opacity-60"
        >
          {submitting ? "Logging in…" : "Log in"}
        </button>
      </form>

      <p className="mt-6 text-sm text-text-muted">
        Don&apos;t have an account?{" "}
        <Link href="/register" className="text-accent hover:opacity-90">
          Sign up
        </Link>
      </p>
    </main>
  );
}
