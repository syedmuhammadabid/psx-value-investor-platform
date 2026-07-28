# PSX Value Investor Platform

## Product Requirements Document (PRD) & MVP Roadmap

**Version:** 2.0 (Production-Grade)
**Status:** Draft
**Author:** Syed Muhammad Abid Hussain
**Last Updated:** July 2026

---

# Document Purpose

This roadmap defines both the **product vision** (what to build) and the **engineering standards** (how to build it to production quality). Every phase must satisfy the cross-cutting production requirements defined in the *Production Engineering Standards* section before it is considered "done."

**Definition of Done (applies to every feature):**

* Code reviewed and merged via pull request
* Unit + integration tests written and passing (≥ 80% coverage on business logic)
* Input validated and sanitized at the API boundary
* Errors handled gracefully with structured logging
* Observability in place (metrics, logs, traces)
* Documented (API contract + user-facing where relevant)
* Accessible (WCAG 2.1 AA) and responsive
* Deployed via CI/CD with automated rollback

---

# Vision

Build Pakistan's first AI-powered fundamental analysis platform that helps investors determine **what a PSX-listed company is actually worth**, instead of simply displaying stock prices.

The platform should answer questions such as:

* Is this stock undervalued?
* What is its intrinsic value?
* What is the ideal buying range?
* When should I take profits?
* Why is this stock recommended?
* What risks should I consider?

The long-term goal is to become the **Simply Wall St + Morningstar + Screener.in** equivalent for Pakistan Stock Exchange.

---

# Guiding Principles

* Start completely free.
* Build one module at a time.
* Validate the product before spending money.
* Focus on long-term investors.
* Make every recommendation explainable.
* Automate calculations instead of manual analysis.

---

# Budget

## Phase 1

Budget: **$0**

Use only free-tier services.

## Free-First Principle

The entire platform is designed to run on **free tiers only** for the foreseeable future. Every tool listed in this roadmap has a usable free tier. Paid tiers and paid-only tools are explicitly labeled **(paid — later, at scale)** and are **not required** for the MVP or beta launch.

**What stays $0 today:**

| Concern | Free-tier tool |
| --- | --- |
| Frontend hosting | Vercel (Hobby) |
| Backend hosting | Render / Railway / Fly.io free tier |
| Database + Auth + Storage | Supabase Free |
| Cache / rate-limit / queue | Upstash Redis Free |
| CI/CD | GitHub Actions (free minutes) |
| Error tracking | Sentry Developer (free) |
| Uptime monitoring | Better Stack / UptimeRobot free |
| Product analytics | PostHog Cloud free tier |
| Email (alerts) | Resend / Brevo free tier |

Anything that would incur cost (read replicas, PITR, dedicated Redis, higher CI minutes, payment processing fees) is deferred until real usage and revenue justify it.

---

# Tech Stack

> **Finalized stack (all free tier).** These are the locked decisions for the MVP. Alternatives were considered and rejected in favor of the single choice listed. Anything marked **(later)** is only introduced when scale/revenue demands it.

## Stack at a Glance

| Layer | Choice | Hosting (free) |
| --- | --- | --- |
| Frontend framework | Next.js 15 (App Router) + React + TypeScript | Vercel Hobby |
| Styling | Tailwind CSS | — |
| Server state | TanStack Query | — |
| Client state | Zustand | — |
| Forms + validation | React Hook Form + Zod | — |
| Charts | TradingView Lightweight Charts | — |
| i18n | next-intl (English + Urdu) | — |
| Backend framework | FastAPI (Python 3.12) | Render Free |
| Data validation | Pydantic v2 | — |
| ORM + migrations | SQLAlchemy 2.0 + Alembic | — |
| Data/math | Pandas + NumPy (scikit-learn later for forecasting) | — |
| Background jobs | APScheduler + GitHub Actions cron | — |
| Database | PostgreSQL via Supabase | Supabase Free |
| Auth | Supabase Auth (JWT + RLS) | Supabase Free |
| File storage | Supabase Storage | Supabase Free |
| Cache / rate-limit **(later)** | Upstash Redis | Upstash Free |
| CI/CD | GitHub Actions | Free minutes |
| Error tracking | Sentry | Developer (free) |
| Uptime | UptimeRobot | Free |
| Analytics | PostHog Cloud | Free tier |
| Transactional email | Resend | Free tier |

---

## Frontend

* Next.js (App Router, React Server Components, streaming SSR)
* React
* TypeScript (strict mode enabled)
* Tailwind CSS
* TanStack Query (server-state caching, optimistic updates)
* Zustand (lightweight client state where needed)
* TradingView Lightweight Charts
* React Hook Form
* Zod (shared validation schemas)
* next-intl (i18n — English + Urdu ready)

Quality tooling

* ESLint + Prettier + TypeScript strict
* Vitest + React Testing Library (unit/component)
* Playwright (E2E)
* Storybook (component library & visual regression)

Hosting

* Vercel Hobby (free)

---

## Backend

Python FastAPI

Why?

* Better for financial calculations
* Pandas
* NumPy
* Scikit-learn (later, for forecasting)
* Easy API development, first-class OpenAPI/Swagger

Production stack

* Pydantic v2 (request/response validation & settings)
* SQLAlchemy 2.0 + Alembic (ORM & migrations)
* Uvicorn + Gunicorn (ASGI workers)
* APScheduler (in-process scheduled jobs — no Redis needed to start)
* Ruff + Black + mypy (lint, format, type-check)
* Pytest + pytest-cov + factory_boy (tests & fixtures)

Hosting

* Render Free (chosen). Railway/Fly.io/Cloud Run remain drop-in fallbacks if Render's free limits become a problem.

---

## Database

PostgreSQL

Provider

* Supabase Free → Pro

Benefits

* PostgreSQL
* Authentication
* Storage
* Row Level Security (RLS)
* Scheduled backups

Production practices

* All schema changes via versioned migrations (Alembic)
* RLS policies enforced on every user-owned table
* Connection pooling via Supabase's built-in pooler (free)
* Indexed foreign keys and hot query paths
* **(paid — later, at scale)** Read replicas and point-in-time recovery (PITR) on the Pro tier

---

## Caching & Performance

* Redis (Upstash free tier) — API response cache, rate-limit counters, job queue
* HTTP caching via Vercel Edge + `Cache-Control` / `stale-while-revalidate`
* CDN for static assets and chart data snapshots

---

## File Storage

Supabase Storage (financial PDFs, exported reports)

---

## Charts

TradingView Lightweight Charts

---

## Authentication & Authorization

Supabase Auth

* Email/password + OAuth (Google)
* JWT-based sessions, refresh token rotation
* Role-based access control (free / premium / professional / admin)
* Row Level Security tying data to `auth.uid()`

---

## Background Jobs

Initially (chosen)

* APScheduler running inside the FastAPI service for lightweight schedules
* GitHub Actions cron for heavier scheduled scrapes/recomputes (free minutes)

At scale (later)

* Upstash Redis-backed Celery for scraping, ratio recomputation, valuation refresh, and alert dispatch
* Idempotent, retryable jobs with dead-letter handling

---

## Infrastructure & DevOps

* GitHub Actions — lint, test, type-check, build, deploy pipelines (free minutes)
* Environment separation: `development`, `staging`, `production`
* Secrets managed via platform secret stores (never committed)
* Infrastructure config as code where supported
* Docker for reproducible backend builds
* Sentry (errors), UptimeRobot (uptime), PostHog (analytics), Resend (email) — all on **free tiers**

---

# Design System & Visual Theme

> **Direction: dark-first and minimalistic.** The interface is calm, content-focused, and data-dense without clutter — the numbers are the hero, not the chrome.

## Principles

* **Dark by default** — dark theme is the primary experience; a light theme is optional and secondary.
* **Minimalism** — generous whitespace, few borders, no gradients/shadows unless they aid hierarchy, no decorative imagery.
* **Content-first** — typography and numbers carry the design; UI recedes.
* **One accent color** — a single accent used sparingly for primary actions and key highlights.
* **Consistency** — all styling flows from design tokens (CSS variables), never ad-hoc hex values.
* **Restraint in motion** — subtle, fast transitions only; respect `prefers-reduced-motion`.

## Color Tokens (dark theme)

Defined as CSS variables and mapped into Tailwind's theme config.

| Token | Purpose | Value (guide) |
| --- | --- | --- |
| `--bg` | App background | near-black `#0A0A0B` |
| `--surface` | Cards / panels | `#141416` |
| `--surface-2` | Raised / hover | `#1C1C1F` |
| `--border` | Hairline dividers | `#26262A` |
| `--text` | Primary text | `#EDEDED` |
| `--text-muted` | Secondary text | `#A1A1AA` |
| `--accent` | Primary action / links | `#3B82F6` (or a single chosen hue) |
| `--positive` | Gains / undervalued / BUY | `#22C55E` |
| `--negative` | Losses / overvalued / SELL | `#EF4444` |
| `--warning` | Hold / caution | `#F59E0B` |

**Semantic financial colors** are reused everywhere (charts, badges, buy/sell zones) so green/red always mean the same thing.

## Typography

* **UI font** — Inter (or Geist), variable weight, system-font fallback.
* **Numeric font** — tabular/monospaced figures for all financial numbers so columns align (e.g. `font-variant-numeric: tabular-nums`).
* Clear type scale; limited weights (regular, medium, semibold).

## Layout & Components

* Spacing on a consistent scale (Tailwind 4px base); breathable, uncrowded tables.
* Flat cards with hairline borders instead of heavy shadows.
* Charts inherit theme tokens (dark background, muted grid lines, semantic series colors).
* Every data view designs its loading (skeletons), empty, and error states.
* Fully responsive, mobile-first (most PSX retail users are on mobile).

## Implementation

* Tailwind CSS with a dark-first token config (`darkMode: 'class'`, defaulting to dark).
* Design tokens as CSS variables in a single theme file — the single source of truth.
* Optional: a lightweight headless component layer (Radix UI primitives) for accessible, unstyled building blocks kept minimal.

---

# Initial Folder Structure

```text
psx-value-investor/

frontend/
    app/                  # Next.js App Router routes
    components/           # Reusable UI (co-located with Storybook stories)
    hooks/
    services/             # API client (typed, generated from OpenAPI)
    lib/                  # utils, formatters, config
    schemas/              # Zod schemas shared with forms
    tests/                # unit + Playwright E2E

backend/
    app/
        api/              # routers, dependencies, versioned (v1)
        core/             # config, security, logging, exceptions
        models/           # SQLAlchemy models
        schemas/          # Pydantic request/response models
        services/         # business logic layer
        calculations/     # financial math (pure, unit-tested)
        valuation/        # valuation models
        scraper/          # PSX ingestion + parsers
        repositories/     # data-access layer
        jobs/             # scheduled/background tasks
    tests/                # pytest unit + integration
    alembic/              # DB migrations

database/
    migrations/
    seeds/
    policies/             # RLS policy definitions

scripts/                  # data ops, backfills, maintenance

infra/                    # Docker, CI config, env templates

docs/                     # ADRs, API docs, runbooks
```

---

# MVP Philosophy

The first version should solve one problem extremely well.

> "At what price should I buy this stock?"

Nothing else matters initially.

---

# Product Roadmap

---

# Phase 1 — Project Setup

Duration

1 Week

Deliverables

* Next.js application (TypeScript strict, ESLint/Prettier configured)
* FastAPI backend (Ruff/Black/mypy, Pydantic settings)
* PostgreSQL database with Alembic migrations
* Supabase project (Auth + RLS baseline)
* CI/CD pipelines (GitHub Actions: lint, test, type-check, build, deploy)
* Staging + production environments with secret management
* Sentry + logging + uptime monitoring wired in
* Dockerized backend + local Docker Compose dev setup
* GitHub Repository with branch protection & PR templates
* Domain configuration (HTTPS, security headers)
* Landing page
* README + contribution guide + ADR folder

---

# Phase 2 — Company Explorer

Goal

Search any PSX company.

Homepage

```
Search

ENGRO

MARI

SYS

UBL

HBL
```

Features

* Search
* Sector
* Industry
* Market Cap
* Current Price
* Company Profile

No login required.

---

# Phase 3 — Company Profile

Every company gets its own page.

Example

```
ENGRO

Current Price

Market Cap

Industry

Sector

52 Week High

52 Week Low

Dividend Yield

Website

Financial Year

Listing Date
```

---

# Phase 4 — Financial Statements

Display

Income Statement

Balance Sheet

Cash Flow

Support

* Annual
* Quarterly
* Last 10 years

---

# Phase 5 — Financial Ratio Engine

Automatically calculate

## Profitability

* ROE
* ROA
* ROIC
* Gross Margin
* Operating Margin
* Net Margin

---

## Valuation

* P/E
* P/B
* PEG
* EV/EBITDA
* Price/Sales
* Dividend Yield

---

## Debt

* Debt/Equity
* Interest Coverage

---

## Liquidity

* Current Ratio
* Quick Ratio

---

## Cash Flow

* Operating Cash Flow
* Free Cash Flow
* FCF Yield

---

## Growth

* Revenue CAGR
* EPS CAGR
* Dividend CAGR

---

# Phase 6 — Financial Charts

Visualize

* Revenue
* EPS
* Net Profit
* ROE
* ROIC
* Dividend
* Book Value
* Free Cash Flow

This allows users to see long-term trends.

---

# Phase 7 — Stock Screener

Users should filter stocks using custom rules.

Examples

```
ROE > 20%

ROIC > 15%

PE < 10

Dividend Yield > 8%

Debt/Equity < 0.5

Revenue Growth > 10%

Positive Free Cash Flow
```

---

# Phase 8 — Intrinsic Value Engine

This is the core feature.

Instead of showing only the stock price:

```
Current Price

Rs.310
```

Show

```
Intrinsic Value

Rs.395

Current Price

Rs.310

Discount

21%

Recommendation

BUY
```

---

# Valuation Models

Never rely on a single valuation model.

Use multiple models.

---

## Discounted Cash Flow

Weight

30%

---

## Graham Intrinsic Value

Weight

20%

---

## Historical PE

Weight

15%

---

## Industry PE

Weight

10%

---

## EV/EBITDA

Weight

10%

---

## Residual Income

Weight

10%

---

## Dividend Discount Model

Weight

5%

Applicable only to dividend-paying companies.

---

Final intrinsic value should be the weighted average.

---

# Phase 9 — Buy & Sell Zones

Instead of only displaying BUY.

Display

```
Strong Buy

Below Rs.285

Buy

Rs.285–315

Hold

Rs.315–360

Sell

Rs.360–410

Strong Sell

Above Rs.410
```

---

# Phase 10 — Explainable Recommendation Engine

Every recommendation must explain itself.

Example

```
BUY

Reason

ROE 23%

ROIC 18%

Debt Low

Growing EPS

Growing Dividend

Trading 21% below intrinsic value
```

No black-box recommendations.

---

# Phase 11 — Portfolio Tracker

Features

* Purchase Price
* Average Price
* Current Gain/Loss
* Intrinsic Value
* Margin of Safety
* Expected CAGR
* Portfolio Health Score

---

# Phase 12 — Alerts

Users receive notifications when

* Price drops below intrinsic value
* Dividend announced
* Quarterly report released
* ROIC improves
* Debt increases
* Recommendation changes

Delivery

* Browser notifications
* Email
* Telegram (future)

---

# Phase 13 — AI Assistant

Future module.

Example

```
Should I buy HUBC?
```

The assistant should answer using

* Financial statements
* Valuation
* Risks
* Growth
* Cash Flow
* Intrinsic value

---

# Data Pipeline

```
PSX Filings

↓

Financial PDFs

↓

Python Parser

↓

Data Validation

↓

Normalized Database

↓

Ratio Engine

↓

Valuation Engine

↓

Recommendation Engine

↓

REST API

↓

Frontend
```

## Data Quality & Integrity (Production-Critical)

Financial data errors destroy user trust. The pipeline must guarantee correctness.

* **Source provenance** — every data point stores its source (filing URL, page, extraction date).
* **Schema validation** — Pydantic validates every parsed record before it touches the DB.
* **Sanity checks** — automated rules: assets = liabilities + equity, non-negative revenue, YoY change thresholds flag anomalies for manual review.
* **Idempotent ingestion** — re-running the scraper never duplicates or corrupts data (upsert by natural key).
* **Versioning & restatements** — support restated financials without overwriting history; keep an audit trail.
* **Manual review queue** — anomalies routed to an admin dashboard before publishing.
* **Data freshness SLAs** — track last-updated timestamps; surface staleness to users.
* **Backfill & reprocessing** — scripts to recompute ratios/valuations when models change.
* **Unit normalization** — consistent currency (PKR), units (thousands/millions), and fiscal-year alignment.

---

# Database Schema

Core tables

```
companies

prices

income_statements

balance_sheets

cash_flows

dividends

financial_ratios

valuations

recommendations

users

watchlists

portfolios

alerts
```

Supporting / operational tables

```
sectors                # normalized sector & industry taxonomy

data_sources           # provenance: filing URL, page, extracted_at

ingestion_jobs         # job status, run history, error logs

review_queue           # flagged anomalies awaiting manual approval

audit_log              # who/what/when for sensitive changes

subscriptions          # plan, status, billing metadata

notifications          # delivered alerts, read state

api_keys               # professional-tier API access + rate limits
```

Schema conventions

* UUID primary keys, `created_at` / `updated_at` on every table
* Foreign keys with appropriate indexes
* Enums for constrained values (recommendation, plan, job_status)
* Soft deletes where history matters; hard deletes elsewhere
* Row Level Security on all user-owned tables (`users`, `watchlists`, `portfolios`, `alerts`, `subscriptions`)
* All changes shipped as Alembic migrations — no manual production edits

---

# REST API Design

All endpoints are versioned under `/api/v1` and documented via OpenAPI/Swagger.

```
GET  /api/v1/companies                        # paginated, filterable

GET  /api/v1/companies/{symbol}

GET  /api/v1/companies/{symbol}/financials

GET  /api/v1/companies/{symbol}/ratios

GET  /api/v1/companies/{symbol}/valuation

GET  /api/v1/companies/{symbol}/recommendation

GET  /api/v1/companies/{symbol}/prices

GET  /api/v1/search

GET  /api/v1/screener                          # query stocks by rules

GET  /api/v1/watchlist        POST/DELETE      # auth required

GET  /api/v1/portfolio        POST/PUT/DELETE  # auth required

GET  /api/v1/alerts           POST/DELETE      # auth required

GET  /api/v1/health                            # liveness/readiness probe
```

## API Standards (Production)

* **Versioning** — `/api/v1`; breaking changes ship a new version.
* **Pagination** — cursor or limit/offset with total counts; enforced max page size.
* **Consistent errors** — RFC 7807 problem+json shape: `{ type, title, status, detail, instance }`.
* **Validation** — all inputs validated by Pydantic; reject unknown fields.
* **Rate limiting** — per-IP and per-API-key limits (Redis token bucket).
* **Auth** — JWT bearer tokens; scopes per plan tier.
* **Idempotency** — idempotency keys on mutating requests where relevant.
* **CORS** — strict allow-list of trusted origins.
* **Response caching** — `Cache-Control` + ETags on public, cacheable resources.
* **Contract testing** — OpenAPI schema drives typed frontend client and tests.

---

# Future AI Scores

## Financial Health Score

0–100

Based on

* Debt
* Cash Flow
* Profitability
* Growth
* Stability

---

## Buffett Score

Based on

* ROE
* ROIC
* Debt
* Earnings consistency
* Dividend
* Free Cash Flow

---

## Graham Score

Based on

* P/E
* P/B
* Debt
* Current Ratio
* Earnings stability

---

## Piotroski F Score

Automatically calculated.

---

## Altman Z Score

Bankruptcy risk.

---

## Magic Formula Ranking

Based on

* ROIC
* Earnings Yield

---

## Quality Score

Combination of

* Profitability
* Growth
* Cash Flow
* Debt
* Valuation

---

# Production Engineering Standards

These cross-cutting requirements apply to the entire platform. A feature is not production-ready until it meets them.

---

## 1. Security (OWASP Top 10)

* **Authentication** — Supabase Auth, JWT with short-lived access tokens and refresh rotation.
* **Authorization** — RBAC by plan tier + PostgreSQL Row Level Security tied to `auth.uid()`.
* **Input validation** — Zod on the client, Pydantic on the server; reject malformed/unknown input.
* **Injection prevention** — parameterized queries only (SQLAlchemy); never string-build SQL.
* **XSS/CSRF** — output encoding, `SameSite` cookies, CSRF tokens on state-changing forms.
* **Secrets management** — environment secret stores; never commit keys; rotate regularly.
* **Transport security** — HTTPS everywhere, HSTS, secure headers (CSP, X-Frame-Options, etc.).
* **Rate limiting & abuse protection** — Redis-backed limits, bot detection on public endpoints.
* **Dependency scanning** — Dependabot + `pip-audit` / `npm audit` in CI.
* **Least privilege** — scoped DB roles, minimal service permissions.
* **Audit logging** — record sensitive actions (auth, billing, admin edits).

---

## 2. Testing Strategy

* **Unit tests** — all financial calculations and valuation models (pure functions, deterministic, edge-case covered). Target ≥ 90% coverage on `calculations/` and `valuation/`.
* **Integration tests** — API endpoints against a test database.
* **Contract tests** — OpenAPI schema validates frontend/backend agreement.
* **E2E tests** — Playwright for critical user journeys (search → company → valuation → watchlist).
* **Component tests** — React Testing Library + Storybook.
* **Data-validation tests** — golden-file tests for parsers against known filings.
* **CI gate** — no merge without green tests, type checks, and lint.

---

## 3. CI/CD Pipeline

```
Push / PR
  ↓
Lint (ESLint, Ruff) + Format check
  ↓
Type check (tsc, mypy)
  ↓
Unit + Integration tests
  ↓
Build (frontend + backend Docker image)
  ↓
Deploy to Staging (auto)
  ↓
E2E smoke tests on Staging
  ↓
Manual approval
  ↓
Deploy to Production (with automated rollback on failure)
```

* Preview deployments per pull request (Vercel).
* Database migrations run automatically and safely (backward-compatible, reversible).
* Blue-green / rolling deploys to avoid downtime.

---

## 4. Observability & Monitoring

All tools below run on **free tiers**.

* **Error tracking** — Sentry (frontend + backend) with source maps and release tagging.
* **Structured logging** — JSON logs with correlation/request IDs across services (platform-native log viewers).
* **Metrics** — request latency, error rate, throughput, job success rate, cache hit ratio.
* **Uptime & alerting** — health-check probes via UptimeRobot.
* **Tracing** — basic request tracing now; distributed tracing later, at scale.
* **Product analytics** — PostHog for funnels, retention, feature adoption (privacy-respecting).
* **Dashboards** — golden signals (latency, traffic, errors, saturation) + business KPIs.

---

## 5. Performance & Scalability

* **Frontend** — code splitting, RSC streaming, image optimization, lazy-loaded charts; Core Web Vitals budget (LCP < 2.5s, CLS < 0.1, INP < 200ms).
* **Backend** — async I/O, connection pooling, N+1 query elimination, response caching.
* **Database** — proper indexing, query analysis, materialized views for heavy aggregates (screener).
* **Caching layers** — CDN → edge → Redis → DB.
* **Load testing** — k6/Locust before major launches.
* **Graceful degradation** — stale-while-revalidate, fallbacks when a data source is down.

---

## 6. Reliability & Resilience

* **Backups** — automated daily DB backups + point-in-time recovery; periodically test restores.
* **Disaster recovery** — documented RTO/RPO targets and runbooks.
* **Idempotent, retryable jobs** — exponential backoff, dead-letter queues.
* **Circuit breakers & timeouts** — on all external calls (scraper, email, payments).
* **Feature flags** — ship dark, roll out gradually, kill switch for risky features.
* **Zero-downtime migrations** — expand/contract pattern.

---

## 7. Compliance, Legal & Trust

Financial products carry regulatory and reputational risk in Pakistan.

* **Investment disclaimer** — clear "not financial advice / for informational purposes" notices on all recommendations and valuations.
* **SECP awareness** — avoid activities that constitute regulated advisory services without licensing; consult legal counsel before monetizing advice.
* **Data licensing** — confirm rights to scrape/redistribute PSX filings and price data; respect terms of use.
* **Privacy** — privacy policy, terms of service, user data export/deletion (GDPR-style rights).
* **Transparency** — every recommendation is explainable and shows its assumptions and data sources.
* **Cookie/consent** — analytics consent where required.

---

## 8. Accessibility & UX Quality

* WCAG 2.1 AA compliance (keyboard nav, ARIA, color contrast, screen-reader support).
* Responsive design (mobile-first — most PSX retail users are on mobile).
* **Dark theme by default** (see *Design System & Visual Theme*); optional light theme.
* Loading, empty, and error states designed for every data view.
* Internationalization-ready (English + Urdu).
* SEO: SSR/SSG for public company pages, structured data, sitemaps, meta tags.

---

## 9. Environments & Configuration

* Three environments: `development`, `staging`, `production`.
* Config via environment variables (12-factor); typed and validated at boot.
* Seeded staging data mirroring production shape (never real user data).
* Reproducible local setup (Docker Compose) documented in the README.

---

## 10. Documentation & Runbooks

* **ADRs** — architecture decision records for significant choices.
* **API docs** — auto-generated Swagger + usage guides.
* **Runbooks** — incident response, data reprocessing, deploy/rollback, on-call.
* **Onboarding** — README that gets a new dev running locally quickly.
* **Financial methodology docs** — how each ratio, valuation model, and score is computed (builds user trust and is auditable).

---

# Revenue Model

## Free Plan

* Search companies
* Financial statements
* Basic ratios
* Stock screener
* Limited watchlist

---

## Premium

* Intrinsic value
* Buy/Sell zones
* Portfolio tracking
* AI assistant
* Alerts
* Advanced screeners

---

## Professional

* API access
* Portfolio analytics
* Institutional tools

---

## Billing Infrastructure (paid — later, when monetizing)

Not needed while the platform is free. Build this only when introducing paid plans; until then all features ship on free tiers with no payment integration.

* **Payments** — Stripe (no monthly fee; per-transaction only) and a local PSP for Pakistan (PKR) — evaluate availability and fees when the time comes.
* **Subscription lifecycle** — trials, upgrades/downgrades, proration, dunning, cancellations.
* **Webhooks** — idempotent handling of payment events; reconcile against `subscriptions` table.
* **Entitlements** — plan gates enforced server-side (never trust the client).
* **Invoicing & tax** — receipts, applicable sales tax handling.
* **Fraud & chargeback** protections.

---

# Weekly Roadmap

## Week 1

* Project setup
* Next.js
* FastAPI
* PostgreSQL
* CI/CD

---

## Week 2

* Search
* Company profile
* Landing page

---

## Week 3

* Historical prices
* Charts

---

## Week 4

* Financial statements

---

## Week 5

* Ratio engine

---

## Week 6

* Stock screener

---

## Week 7

* Intrinsic value engine

---

## Week 8

* Recommendation engine

---

## Week 9

* Watchlist
* Portfolio

---

## Week 10

* Beta launch

---

# Initial Scope

Do **not** support all 500+ PSX companies at launch.

Instead

Support approximately the top 100 companies by

* Market Capitalization
* Trading Volume
* Investor Interest

This dramatically reduces development effort while covering most user demand.

---

# Long-Term Vision

Transform the platform into Pakistan's most trusted investment research platform.

Future additions may include

* Mobile applications
* Broker integration
* AI-powered portfolio analysis
* Financial news summarization
* Forecasting models
* Institutional dashboards
* Public API
* Community discussions
* Dividend calendar
* IPO tracker
* Insider trading analysis

---

# Launch Readiness Checklist

Before public beta, confirm all of the following are green:

**Security**
* [ ] RLS policies verified on every user-owned table
* [ ] Secrets rotated and out of source control
* [ ] Rate limiting active on public + auth endpoints
* [ ] Dependency & secret scanning passing in CI
* [ ] Security headers (CSP, HSTS) configured

**Reliability**
* [ ] Automated backups + a tested restore
* [ ] Health checks and uptime alerts live
* [ ] Error tracking (Sentry) receiving events
* [ ] Rollback procedure verified

**Quality**
* [ ] ≥ 80% test coverage on business logic; ≥ 90% on calculations
* [ ] E2E smoke tests passing on staging
* [ ] Core Web Vitals within budget
* [ ] Accessibility audit (WCAG 2.1 AA) passed

**Data**
* [ ] Data validation & sanity checks running
* [ ] Provenance recorded for all financial data
* [ ] Freshness/staleness surfaced to users

**Legal & Trust**
* [ ] Investment disclaimers on all recommendations
* [ ] Privacy policy + terms of service published
* [ ] Data licensing/scraping rights confirmed
* [ ] Methodology documentation published

**Ops**
* [ ] Runbooks written (incident, deploy, data reprocessing)
* [ ] Monitoring dashboards for golden signals + KPIs
* [ ] On-call / alerting configured

---

# Success Metrics

## MVP

* 100 registered users
* 1,000 monthly visitors
* 20 returning users
* 50 watchlists created

---

## Year 1

* 10,000 users
* 500 premium subscribers
* 100,000 monthly visitors

---

# Core Product Principle

> **Do not become another stock price website.**

The mission is to help investors answer one fundamental question:

**"What is this company actually worth, and should I buy it today?"**

Every feature should support that mission.
