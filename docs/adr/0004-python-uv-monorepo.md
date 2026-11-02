# 0004. Python 3.13 monorepo with uv workspaces

- Status: Accepted
- Date: 2026-11-02

## Context and problem statement

The project has a DSP library, several services, an orchestration code location, a dbt project,
schemas, contracts and deployment code. They change together, and versions must stay
consistent.

## Decision outcome

A single repository with a **uv workspace**: `packages/` holds the libraries (`wingbeat-dsp`,
`wingbeat-contracts`, `wingbeat-common`) and `services/` holds the deployables (`edge-agent`,
`simulator`, `bridge`, `stream-processor`, `api`), with one `uv.lock`. Python is pinned to
**3.13** because `dagster-dbt` 0.29 doesn't support 3.14 yet. CI tests 3.13 and runs a
non-blocking 3.14 job for the libraries.

Tooling: Ruff (lint and format), mypy `--strict`, pytest + Hypothesis, `just` for tasks,
pre-commit hooks, and a dev container for a one-step setup.

### Consequences

- Good: atomic cross-cutting changes, one dependency graph, shared CI.
- Bad: CI must use path filters and caching to stay fast.

### Confirmation

`just check` runs every gate locally in under 2 minutes on a laptop, and CI on a pull request
takes under 10 minutes.
