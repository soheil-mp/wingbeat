# Contributing to Wingbeat

Thanks for your interest! Wingbeat is a single-maintainer project with a public roadmap. Issues
and pull requests are welcome.

## Ground rules

- **No machine learning** in the product. Detection and attribution are classical DSP and cited
  rule tables ([ADR-0002](docs/adr/0002-deterministic-signal-processing.md)).
- **No personal data.** Use synthetic data in fixtures, examples, screenshots and bug reports.
  Never add recordings that may contain people's voices.
- **No secrets.** Configuration comes from environment variables. Add new variables to
  `.env.example` with placeholder values.
- **Cite your numbers.** Any biological parameter (frequency, slope, activity window) needs a
  DOI in the reference table.

## Workflow

1. Pick an open issue (or open one) and comment that you're working on it.
2. Create a short-lived branch: `feat/m2-harmonic-estimator`, `fix/bridge-headers`, …
3. Install the hooks once: `uvx pre-commit install`.
4. Commit in small working steps with [Conventional Commits](https://www.conventionalcommits.org)
   (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `build:`, `ci:`, `chore:`).
5. Open a pull request and fill in the checklist. CI must be green.
6. Pull requests are merged with a **merge commit**, so every commit is kept as written. History
   on `main` is never rewritten.

## Architecture decisions

Changes to the architecture, stack, data contracts or operational guarantees need an ADR in
`docs/adr/` (copy `template.md`). Accepted ADRs are superseded, not edited.

## Data sources

Before code that reads a new external source is merged, add the source to
`docs/research/data-sources.md` with its licence, attribution text, access method and size cap.
