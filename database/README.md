# Database

PostgreSQL schema artifacts for the platform.

```text
migrations/   # SQL migrations (Alembic is the source of truth in backend/alembic)
seeds/        # Seed data for local/staging (never real user data)
policies/     # Row Level Security (RLS) policy definitions
```

## Conventions

- UUID primary keys; `created_at` / `updated_at` on every table.
- Foreign keys indexed; enums for constrained values.
- Row Level Security on all user-owned tables (`users`, `watchlists`,
  `portfolios`, `alerts`, `subscriptions`) tied to `auth.uid()`.
- All schema changes ship as Alembic migrations — no manual production edits.
