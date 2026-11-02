# Wingbeat — working rules for coding agents

Read `README.md`, `ROADMAP.md` and `docs/adr/` before starting work. These rules apply to
every change in this repository.

## Product boundaries

- **Deterministic signal processing only.** Detection and species attribution use classical
  DSP and literature-sourced rule tables (see ADR-0002). No machine-learning or AI anywhere in
  the product: no model APIs (OpenAI, Anthropic, Gemini, Ollama, Hugging Face or others), no
  local models, embeddings or ML libraries (scikit-learn, PyTorch, TensorFlow, ONNX Runtime,
  etc.), and no datasets meant for training or evaluating models. Use the
  words *estimator*, *rule engine* and *attribution*, never *classifier*, *model* or
  *prediction*, for project code.
- **No personal data.** Fixtures, seeds, examples and screenshots use made-up data. Never
  ingest data about people: drop fields such as `recordedBy`, `identifiedBy`, user names and
  e-mail addresses at the ingestion boundary. Never store or transmit human speech: raw audio
  stays on the edge device and the speech guard must run before any uplink (ADR-0008).
- **No health or financial records.** Ingest environmental and biodiversity data only. No
  human case counts or clinical data, even public aggregates.
- **No user accounts** and no storing other people's data. The API is read-only and public;
  admin endpoints use a single token from the environment.
- **No security tooling** that finds or exploits vulnerabilities as a product feature.

## Secrets and data

- No secrets in code or history. Read keys from environment variables, keep `.env` ignored,
  and add every new variable to `.env.example` with a placeholder value.
- Respect the storage budget in `ROADMAP.md`: downloaded data stays under `data/` (ignored),
  every external source has a size cap, and nothing larger than 500 KB is committed.
- Every external source is recorded in `docs/research/data-sources.md` with licence,
  attribution text and size budget before code that reads it is merged.

## Engineering conventions

- Python 3.13, managed with `uv` workspaces. `ruff` (lint + format) and `mypy --strict` must
  pass; tests use `pytest` and `hypothesis`.
- Contracts first: change `schemas/` (protobuf) or `contracts/` (data contracts) before the
  code that produces or consumes them; `buf breaking` must pass.
- Every architecture-level choice gets an ADR in `docs/adr/` (MADR format).
- Only add dependencies whose licences are compatible with MIT (permissive or weak copyleft
  such as MPL-2.0). Copyleft services (e.g. AGPL Grafana) may run as separate containers but are
  never vendored or linked. Never copy code we don't have the right to share.

## Git

- Commit after each working step with a Conventional Commit message (`feat:`, `fix:`,
  `docs:`, `chore:`, `ci:`, `test:`, `refactor:`, `perf:`, `build:`).
- Never squash, amend or rebase pushed commits, never force-push, and never change commit
  dates. Pull requests are merged with merge commits.
- Keep `README.md` (what it does, who it's for, built with, how to run it) and `ROADMAP.md`
  up to date when a change affects them; tick roadmap items when they are done.
- The licence is MIT (`LICENSE` in the top folder).
