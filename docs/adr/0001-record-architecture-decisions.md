# 0001 — Record architecture decisions

- Status: Accepted
- Date: 2026-07-28

## Context

We need a lightweight, durable way to capture the *why* behind significant
technical decisions so future contributors understand the reasoning and don't
relitigate settled choices.

## Decision

We will use Architecture Decision Records (ADRs), one Markdown file per decision,
stored in `docs/adr/` and numbered sequentially. We follow a lightweight MADR-style
template: Context, Decision, Consequences.

An ADR is added whenever a decision is costly to reverse (frameworks, data stores,
API contracts, auth model, deployment topology). ADRs are immutable once accepted;
a later ADR supersedes an earlier one rather than editing it.

## Consequences

- New contributors can read the history of decisions quickly.
- Decisions are reviewed via pull request like code.
- Minor, easily reversible choices do not require an ADR.
