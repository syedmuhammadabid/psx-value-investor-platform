"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useAuth } from "@/lib/auth";

const NAV_LINKS = [
  { href: "/companies", label: "Companies" },
  { href: "/screener", label: "Screener" },
  { href: "/watchlist", label: "Watchlist" },
  { href: "/portfolio", label: "Portfolio" },
];

export default function SiteHeader() {
  const { user, status, logout } = useAuth();
  const pathname = usePathname();

  return (
    <header className="border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-6 py-3">
        <Link href="/" className="font-mono text-sm font-semibold text-text">
          PSX<span className="text-accent">Value</span>
        </Link>

        <nav className="flex items-center gap-1 text-sm">
          {NAV_LINKS.map((link) => {
            const active =
              pathname === link.href || pathname.startsWith(`${link.href}/`);
            return (
              <Link
                key={link.href}
                href={link.href}
                className={`rounded-md px-3 py-1.5 transition-colors ${
                  active
                    ? "bg-surface-2 text-text"
                    : "text-text-muted hover:text-text"
                }`}
              >
                {link.label}
              </Link>
            );
          })}
        </nav>

        <div className="flex items-center gap-2 text-sm">
          {status === "loading" ? (
            <span className="text-text-muted">…</span>
          ) : user ? (
            <>
              <span
                className="hidden max-w-[180px] truncate text-text-muted sm:inline"
                title={user.email}
              >
                {user.full_name ?? user.email}
              </span>
              <button
                type="button"
                onClick={logout}
                className="rounded-md border border-border px-3 py-1.5 text-text-muted transition-colors hover:text-text"
              >
                Log out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/login"
                className="rounded-md px-3 py-1.5 text-text-muted transition-colors hover:text-text"
              >
                Log in
              </Link>
              <Link
                href="/register"
                className="rounded-md bg-accent px-3 py-1.5 font-semibold text-white transition-colors hover:opacity-90"
              >
                Sign up
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}
