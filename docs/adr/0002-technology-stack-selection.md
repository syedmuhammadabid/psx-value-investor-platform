# 0002 — Technology stack selection

- Status: Accepted
- Date: 2026-07-28

## Context

The platform must be production-grade yet run entirely on free tiers for the
foreseeable future. It performs heavy financial computation (ratios, valuation
models) and serves a content-first, data-dense, dark-themed web UI. Most PSX
retail users are on mobile.

## Decision

We adopt the following stack (all with usable free tiers):

**Frontend** — Next.js (App Router) + React + TypeScript (strict), Tailwind CSS,
TanStack Query (server state), Zustand (client state), React Hook Form + Zod,
TradingView Lightweight Charts, next-intl (English + Urdu). Hosted on Vercel Hobby.

**Backend** — FastAPI (Python 3.12) for first-class financial libraries
(Pandas, NumPy, scikit-learn later), Pydantic v2, SQLAlchemy 2.0 + Alembic,
APScheduler for scheduled jobs. Hosted on Render Free.

**Database / Auth / Storage** — PostgreSQL via Supabase (Auth with JWT + RLS,
Storage, connection pooling).

**Ops** — GitHub Actions (CI/CD), Sentry (errors), UptimeRobot (uptime),
PostHog (analytics), Resend (email).

> Note: `create-next-app` provisioned Next.js 16 (current latest) rather than 15
> named in the roadmap. Next 16 is backward compatible for our usage and adopted.

## Consequences

- Python backend keeps financial math expressive and testable as pure functions.
- Free-tier constraints defer Redis/Celery, read replicas, and PITR until scale
  and revenue justify them (APScheduler + GitHub Actions cron cover jobs initially).
- TypeScript strict + Pydantic v2 give end-to-end typed validation at both boundaries.
