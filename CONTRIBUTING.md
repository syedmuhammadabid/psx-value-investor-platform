# Contributing to PSX Value Investor Platform

Thank you for contributing! This guide keeps the codebase consistent and
production-quality.

## Ground rules

- Every change ships via a **pull request** — no direct pushes to `main`.
- CI must be green (lint, type-check, tests) before merge.
- Keep PRs small and focused on a single concern.
- Follow the **Definition of Done** in [PROJECT_ROADMAP.md](PROJECT_ROADMAP.md).

## Branching

- `main` — production-ready, protected.
- `develop` — integration branch (optional, if used).
- Feature branches: `feat/<short-description>`
- Fixes: `fix/<short-description>`
- Chores: `chore/<short-description>`

## Commit messages

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
feat(valuation): add discounted cash flow model
fix(api): correct pagination cursor encoding
chore(ci): bump GitHub Actions runner
docs(adr): record database choice
```

## Before you open a PR

### Frontend

```bash
cd frontend
npm run lint
npm run typecheck
npm run format
```

### Backend

```bash
cd backend
ruff check .
black --check .
mypy app
pytest
```

Install the repository hooks with `pre-commit install` after installing the backend dev dependencies.

## Pull request checklist

- [ ] Tests added/updated and passing
- [ ] Lint + type-check pass
- [ ] Inputs validated at the API boundary (Zod / Pydantic)
- [ ] Errors handled with structured logging
- [ ] Docs updated where relevant (API contract, ADR, methodology)
- [ ] Accessible (WCAG 2.1 AA) and responsive for UI changes

## Architecture decisions

Significant technical decisions are recorded as ADRs in [docs/adr/](docs/adr/).
Add a new ADR when you make a decision that is costly to reverse.

## Code style

- **Frontend:** ESLint + Prettier + TypeScript strict.
- **Backend:** Ruff + Black + mypy (strict).
- No ad-hoc hex colors in the frontend — use design tokens (CSS variables).
