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
3. Set up once with `just setup`, and run `just check` before pushing; CI runs the same recipes.
4. Commit in small working steps with [Conventional Commits](https://www.conventionalcommits.org)
   (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `perf:`, `build:`, `ci:`, `chore:`).
5. Open a pull request and fill in the checklist. CI must be green.
6. Pull requests are merged with a **merge commit**, so every commit is kept as written. History
   on `main` is never rewritten.

## Releases

Releases are automated with [release-please](https://github.com/googleapis/release-please). It
keeps a release pull request open that turns Conventional Commits into `CHANGELOG.md` entries and
the next version in `version.txt` (semantic versioning, `0.x` until 1.0). Merging that pull
request tags `vX.Y.Z` and creates the GitHub release. The product version lives in `version.txt`
and the tags. Workspace packages stay at `0.0.0` because they aren't published separately, and
bumping them would invalidate `uv.lock` on every release.

## Architecture decisions

Changes to the architecture, stack, data contracts or operational guarantees need an ADR in
`docs/adr/` (copy `template.md`). Accepted ADRs are superseded, not edited.

## Data sources

Before code that reads a new external source is merged, add the source to
`docs/research/data-sources.md` with its licence, attribution text, access method and size cap.
