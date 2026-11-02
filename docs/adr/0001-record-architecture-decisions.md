# 0001. Record architecture decisions

- Status: Accepted
- Date: 2026-11-02

## Context and problem statement

Wingbeat spans signal processing, edge software, streaming, batch data engineering and platform
operations. Decisions in one layer constrain the others, and the reasoning behind a choice is
lost quickly in a long-running project.

## Decision outcome

Every decision that changes the architecture, the stack, a data contract policy or an
operational guarantee is recorded as an ADR in `docs/adr/`, using MADR 4. ADRs are reviewed in
the same pull request as the change they justify. Superseded ADRs stay in place with a link to
their successor.

### Consequences

- Good: newcomers, reviewers and future-me can follow why the system looks the way it does.
- Bad: a small writing cost on every significant change.

### Confirmation

The pull request template asks "Does this need an ADR?". The docs site renders the index.
