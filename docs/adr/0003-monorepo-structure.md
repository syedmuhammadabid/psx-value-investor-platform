# 0003 — Monorepo structure

- Status: Accepted
- Date: 2026-07-28

## Context

Frontend, backend, database artifacts, infrastructure, and docs evolve together
and share contracts (OpenAPI → typed client, Zod ↔ Pydantic schemas). We want
atomic cross-cutting changes and a single source of truth.

## Decision

Use a single Git repository (monorepo) with top-level folders:

```text
frontend/  backend/  database/  infra/  scripts/  docs/
```

CI is path-scoped: `frontend/**` triggers the frontend workflow, `backend/**`
triggers the backend workflow. Each app owns its own dependency manifest and
tooling (npm for frontend, pyproject for backend).

## Consequences

- Cross-cutting changes (API + client) land in one pull request.
- Path filters keep CI fast and relevant.
- No package-linking complexity; each app builds and deploys independently.
