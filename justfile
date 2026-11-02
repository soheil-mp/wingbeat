# Wingbeat task runner. Run `just` to list the recipes.
# CI calls these same recipes, so a green `just check` locally means a green pipeline.
# Install just with `uv tool install rust-just` if it isn't on your PATH.

set shell := ["bash", "-euo", "pipefail", "-c"]

pre_commit := "uvx --from pre-commit==4.6.2 pre-commit"
compose_file := "deploy/compose/compose.yaml"

# List the available recipes
default:
    @just --list --unsorted

# Sync the workspace from the lockfile and install the git hooks
setup:
    uv sync --locked
    {{ pre_commit }} install

# Format code and apply safe lint fixes
fmt:
    uv run --frozen ruff format .
    uv run --frozen ruff check --fix .

# Lint and check formatting without changing files
lint:
    uv run --frozen ruff check .
    uv run --frozen ruff format --check .

# Type-check the whole workspace with mypy --strict
typecheck:
    uv run --frozen mypy

# Run the test suite with coverage (extra arguments go to pytest)
test *args:
    uv run --frozen pytest {{ args }}

# Enforce the dependency licence and scope policy on uv.lock (ADR-0002)
deps:
    uv run --frozen python tools/dependency_policy.py

# Run every pre-commit hook on every file
hooks:
    {{ pre_commit }} run --all-files --show-diff-on-failure

# Every local gate: lint, types, tests, dependency policy and hooks
check: lint typecheck test deps hooks

# Refresh the lockfile to the newest allowed versions
upgrade:
    uv lock --upgrade

# Start the local platform (arrives in roadmap milestone M4)
up profile="core": _require-compose
    docker compose -f {{ compose_file }} --profile {{ profile }} up -d --wait

# Stop the local platform and keep its volumes
down: _require-compose
    docker compose -f {{ compose_file }} --profile "*" down

# One command from a clean clone to live detections (arrives in roadmap milestone M4)
demo: _require-compose
    @echo "demo recipe is implemented in roadmap item M4.8" && exit 1

# Remove caches and build output
clean:
    rm -rf .mypy_cache .pytest_cache .ruff_cache .hypothesis htmlcov .coverage coverage.xml dist site

[private]
_require-compose:
    @test -f {{ compose_file }} || { echo "{{ compose_file }} does not exist yet: the Compose stack arrives in roadmap milestone M4." >&2; exit 1; }
